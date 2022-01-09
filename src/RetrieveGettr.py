from gogettr import PublicClient
import time
import random

import Utilities
import Classes

###############################################################################
###############################################################################

class RetrieveGettr:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################

    def incrementByOne(self, mostRecentId: str):
        asInteger = Utilities.base36ToInteger(mostRecentId)
        asInteger += 1
        incremented = Utilities.integerToBase36(asInteger)
        return incremented

    ###########################################################################
    ###########################################################################

    def getAttachedQuotedGweet(self, post):
        quotedGweet = Classes.Tweet()
        quotedGweet.id = Utilities.base36ToInteger(post["_id"])
        quotedGweet.id_str = post["_id"]
        quotedGweet.author_id_str = post["uid"]
        quotedGweet.created_at = Utilities.convertUdateToReadable(int(post["udate"]))
        quotedGweet.conversation_id = quotedGweet.id
        quotedGweet.is_ref_tweet = True
        quotedGweet.text = post.get("txt", "")

        return quotedGweet

    ###########################################################################
    ###########################################################################

    def retrieveSingleGweet(self, client: PublicClient, id_str, typ):
        response = client.all(first=id_str, last=id_str, type=typ)
        posts = [post for post in response]
        rawPost = posts[0]

        gweet = Classes.Tweet()
        gweet.id = Utilities.base36ToInteger(rawPost["_id"])
        gweet.id_str = rawPost["_id"]
        #gweet.author_id_str = # this may not be the uid in the raw data
        gweet.created_at = Utilities.convertUdateToReadable(int(rawPost["udate"]))
        gweet.conversation_id = gweet.id
        gweet.is_ref_tweet = True
        gweet.text = rawPost.get("txt", "")

        return gweet

    ###########################################################################
    ###########################################################################

    def buildURL(self, id_str):
        if (id_str[0] == "c"):
            url = "https://www.gettr.com/comment/{}".format(id_str)
        else:
            url = "https://www.gettr.com/post/{}".format(id_str)
        return url

    ###########################################################################
    ###########################################################################

    def retrieveGweetsForUser(self, user: Classes.GettrUser, numberOfPostsForFirstScan):
        client = PublicClient()

        if (user.mostRecentPostIdStr.strip() == ""):
            self.logger.log("  Retrieving Gweets for {}, max of {}".format(user.gettrHandle, numberOfPostsForFirstScan))
            posts = client.user_activity(username=user.gettrHandle, max=numberOfPostsForFirstScan, type="posts")
        else:
            # start from most recent post retrieved, but need to add 1 so we don't get the same post as last time
            self.logger.log("  Retrieving Gweets for {}, after id {}".format(user.gettrHandle, user.mostRecentPostIdStr))
            until = self.incrementByOne(user.mostRecentPostIdStr)
            posts = client.user_activity(username=user.gettrHandle, until=until, type="posts")

        listOfRawPosts = [post for post in posts]
        listOfRawPosts.reverse()

        # TODO: could retrieve comments as well here

        # The format is:
        # post["action"] = shares_pst
        # post["uid"] = mtg4america

        # post["action"] = pub_pst
        # post["uid"] = repdonaldspress

        # post["rpstIds"] = ['pmw66we12b']
        # post["rusrIds"] = ['mariabartiromo']

         # key _t gives:
            #  post for normal post and for repost, use "action" if it exists to distinguish
            #  cmt
            # if key shrdpst exists then it has a quoted gweet

        listOfGweets = []
        dictOfURLs = {}
        for post in listOfRawPosts:
            gweet = Classes.Tweet()
            gweet.id = Utilities.base36ToInteger(post["_id"])
            gweet.id_str = post["_id"]
            gweet.author_id_str = user.gettrHandle
            udate = int(post["udate"])
            gweet.created_at = Utilities.convertUdateToReadable(udate)
            if (Utilities.daysSinceUdate(udate) > 14):
                self.logger.log("  Skipping Gweet with date {}".format(gweet.created_at))
                continue
            gweet.conversation_id = gweet.id

            action = post.get("action", "")
            if ("share" in action):
                action = "Gweet Repost of @" + post.get("uid", "?")
            else:
                action = "Gweet Post"
            gweet.text = action + "," + post.get("txt", "")

            # look for a url in the text
            # prevsrc is the url
            # ttl is the title
            if ("prevsrc" in post.keys()) and ("ttl" in post.keys()):
                url = post["prevsrc"]
                if (url.strip() != "") and (url in post.get("txt", "")):
                    url_obj = Classes.URL()
                    url_obj.shortened_url = url
                    url_obj.expanded_url = url
                    title = post["ttl"]
                    if ("|" not in title) and (" - " not in title):
                        title += " | " + Utilities.getDomainOfURL(url)
                    url_obj.title = title
                    dictOfURLs[url] = url_obj
                    gweet.list_of_urls.append(url)

            # look for regweet with comment
            try:
                quotedGweet = None
                
                if ("shrdpst" in post.keys()):
                    quotedGweet = self.getAttachedQuotedGweet(post["shrdpst"])
                elif ("rpstIds" in post.keys()):
                    id_str = post["rpstIds"][0]
                    if (id_str[0] == "c"):
                        quotedGweet = self.retrieveSingleGweet(client, id_str, "comments")
                    elif (id_str[0] == "p"):
                        quotedGweet = self.retrieveSingleGweet(client, id_str, "posts")

                if (quotedGweet is not None):
                    listOfGweets.append(quotedGweet)
                    gweet.list_of_referenced_tweets.append("quoted")
                    gweet.list_of_referenced_tweets.append(quotedGweet.id)

                    url = self.buildURL(quotedGweet.id_str)
                    gweet.text += " " + url
                    gweet.list_of_urls.append(url)

                    url_obj = Classes.URL()
                    url_obj.shortened_url = url
                    url_obj.expanded_url = url
                    url_obj.title = "Link to Gettr.com"
                    dictOfURLs[url] = url_obj
            except BaseException as e:
                self.logger.log("Warning: unable to handle quoted gweet for gweet id {}".format(gweet.id_str))
                self.logger.log("Exception: {}".format(e.args))

            listOfGweets.append(gweet)

        # save the most recent post id so we don't retrieve these posts again
        if (len(listOfRawPosts) > 0):
            user.mostRecentPostIdStr = listOfRawPosts[-1]["_id"]

        self.logger.log("  Retrieved {} gweets for user {}".format(len(listOfGweets), user.gettrHandle))

        return listOfGweets, dictOfURLs

    ###########################################################################
    ###########################################################################

    def run(self, avgSecsBetweenHandles = 10, numberOfPostsForFirstScan=20):
        currentDate = Utilities.getCurrentDate()
        listOfMembers = Utilities.loadCongressMembers()
        gettrLookupDict = Utilities.loadGettrLookup(listOfMembers)

        numHandlesRetrieved = 0
        gweetsToSave = []
        urlsToSave = {}

        for member in listOfMembers:
            for handle in member.gettr:
                if (handle == ""):
                    continue

                user = gettrLookupDict[handle]

                for retries in range(0, 3):
                    try:
                        newGweets, urls = self.retrieveGweetsForUser(user, numberOfPostsForFirstScan)
                        newGweets.insert(0, "#" + handle) # this will be used to separate gweets between different handles
                        gweetsToSave = gweetsToSave + newGweets
                        urlsToSave.update(urls)
                        break
                    except BaseException as e:
                        self.logger.log("Warning: failed to retrieve Gweets for handle " + handle)
                        self.logger.log(str(e.args))
                        time.sleep(5)
    
                numHandlesRetrieved += 1
                # slow down the requests to be nice to their servers, and to look like a "normal" user
                lower = avgSecsBetweenHandles // 2
                upper = avgSecsBetweenHandles + lower
                time.sleep(random.randint(lower, upper))

        # save the Gweets to a file
        self.logger.log("  saving " + str(len(gweetsToSave)) + " gweets")
        logMessage = Utilities.saveGweets(gweetsToSave, currentDate)
        self.logger.log("  " + logMessage)

        # save the urls
        self.logger.log("  Saving {} urls".format(len(urlsToSave)))
        logMessage = Utilities.saveURLs(urlsToSave, currentDate, "Gettr", True)
        self.logger.log("  " + logMessage)

        # save the most recent gweet ids so we don't grab the same ones again
        logMessage = Utilities.saveGettrLookup(gettrLookupDict)
        self.logger.log("  " + logMessage)
        
        self.logger.log("  Retrieved a total of " + str(len(gweetsToSave)) + " gweets")
        self.logger.log("  Finished retrieving gweets for " + str(numHandlesRetrieved) + " handles")
        
        return len(gweetsToSave)

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = RetrieveGettr(logger)
    instance.run(60)

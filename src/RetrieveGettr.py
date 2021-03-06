import time
import random

import Utilities
import Classes
from GettrAPI import PublicClient

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

    def cleanText(self, text):
        cleanedText = text.replace("& ", "&amp; ")
        return cleanedText

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
        
        text = post.get("txt", "")

        url_obj = self.getURLinPost(post)
        if (url_obj is not None):
            text = text.replace(url_obj.shortened_url, "(" + url_obj.title + ")")

        quotedGweet.text = self.cleanText(text)

        return quotedGweet

    ###########################################################################
    ###########################################################################

    def retrieveSingleGweet(self, client: PublicClient, id_str, typ):
        time.sleep(1) # slow it down...
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

        text = rawPost.get("txt", "")

        url_obj = self.getURLinPost(rawPost)
        if (url_obj is not None):
            text = text.replace(url_obj.shortened_url, "(" + url_obj.title + ")")

        gweet.text = self.cleanText(text)

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

    def getURLinPost(self, post) -> Classes.URL:
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
                return url_obj
        
        return None

    ###########################################################################
    ###########################################################################

    def retrieveGweetsForUser(self, user: Classes.GettrUser, numberOfPostsForFirstScan, allowedAgeOfPost):
        client = PublicClient()

        # get posts
        if (user.mostRecentPostTime == 0):
            self.logger.log("  Retrieving Posts for {}, max of {}".format(user.gettrHandle, numberOfPostsForFirstScan))
            posts = client.user_activity(username=user.gettrHandle, max=numberOfPostsForFirstScan, type="posts")
        else:
            # start from most recent post retrieved, but need to add 1 so we don't get the same post as last time
            self.logger.log("  Retrieving Posts for {}, after time {}".format(user.gettrHandle, user.mostRecentPostTime))
            until_time = user.mostRecentPostTime + 1
            posts = client.user_activity(username=user.gettrHandle, until_time=until_time, type="posts")

        listOfRawPosts = [post for post in posts]
        listOfRawPosts.reverse()

        time.sleep(3) # slow it down...

        # get comments
        if (user.mostRecentCommentTime == 0):
            self.logger.log("  Retrieving Comments for {}, max of {}".format(user.gettrHandle, numberOfPostsForFirstScan))
            comments = client.user_activity(username=user.gettrHandle, max=numberOfPostsForFirstScan, type="comments")
        else:
            # start from most recent comment retrieved, but need to add 1 so we don't get the same comment as last time
            self.logger.log("  Retrieving Comments for {}, after time {}".format(user.gettrHandle, user.mostRecentCommentTime))
            until_time = user.mostRecentCommentTime + 1
            comments = client.user_activity(username=user.gettrHandle, until_time=until_time, type="comments")

        listOfRawComments = [comment for comment in comments]
        listOfRawComments.reverse()

        rawPostsAndComments = listOfRawPosts + listOfRawComments

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
        for post in rawPostsAndComments:
            udate = int(post["udate"])
            if (Utilities.daysSinceUdate(udate) > allowedAgeOfPost):
                continue # ignore Gweets that are too old

            gweet = Classes.Tweet()
            gweet.id = Utilities.base36ToInteger(post["_id"])
            gweet.id_str = post["_id"]
            gweet.author_id_str = user.gettrHandle
            gweet.created_at = Utilities.convertUdateToReadable(udate)
            gweet.conversation_id = gweet.id

            action = post.get("action", "")
            if ("share" in action):
                action = "Gweet Repost of @" + post.get("uid", "?")
            elif ("pub_cm" in action):
                action = "Gweet Comment"
            else:
                action = "Gweet Post"
            text = post.get("txt", "")
            gweet.text = action + "," + self.cleanText(text)

            # look for a url in the text
            url_obj = self.getURLinPost(post)
            if (url_obj is not None):
                dictOfURLs[url_obj.shortened_url] = url_obj
                gweet.list_of_urls.append(url_obj.shortened_url)

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

        # save the most recent timestamp so we don't retrieve these posts again
        if (len(listOfRawPosts) > 0):
            user.mostRecentPostTime = listOfRawPosts[-1]["udate"]
        if (len(listOfRawComments) > 0):
            user.mostRecentCommentTime = listOfRawComments[-1]["udate"]

        self.logger.log("  Retrieved {} gweets for user {}".format(len(listOfGweets), user.gettrHandle))

        return listOfGweets, dictOfURLs

    ###########################################################################
    ###########################################################################

    # allowedAgeOfPost is in days
    def run(self, avgSecsBetweenHandles = 10, numberOfPostsForFirstScan=20, allowedAgeOfPost=14):
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
                        newGweets, urls = self.retrieveGweetsForUser(user, numberOfPostsForFirstScan, allowedAgeOfPost)
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
    instance.run(10, 60, 200)

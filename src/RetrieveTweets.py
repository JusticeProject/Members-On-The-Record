import tweepy
import Utilities
import Classes

import time

TWEETS_PER_FILE = 1000

###############################################################################
###############################################################################

class RetrieveTweets:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################
    
    def doMultipleUserLookup(self, handlesToLookup):
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)
        
        params = ",".join(handlesToLookup)
        response = client.get_users(usernames=params)
        self.logger.log("received response in doMultipleUserLookup")
        
        idStrDict = {}
        for item in response.data:
            self.logger.log("received username=" + item.username + ", id=" + str(item.id))
            idStrDict[item.username.lower()] = str(item.id)
        
        return idStrDict

    ###########################################################################
    ###########################################################################

    # check if a twitter handle has no id string, do user lookup if needed
    def findMissingUserIds(self, userLookupDict):
        handlesToLookup = []
        for handle in userLookupDict.keys():
            if (userLookupDict[handle].idStr == ""):
                self.logger.log("need idStr for handle " + handle)
                handlesToLookup.append(handle)

        if (len(handlesToLookup) > 0):
            for i in range(0, len(handlesToLookup), 100):
                # grab 0-99, 100-199, etc. because the api can only handle 100 at a time
                batch = handlesToLookup[i:i + 100]
                idStrDict = self.doMultipleUserLookup(batch)
                for handle in idStrDict.keys():
                    userLookupDict[handle].idStr = idStrDict[handle]
            
    ###########################################################################
    ###########################################################################

    def copyTweetData(self, rawTweet, isRefTweet):
        tweet = Classes.Tweet()
        tweet.id = rawTweet.id
        tweet.author_id = rawTweet.author_id
    
        # convert the datetime object from UTC to local time, then to a string
        timestamp = rawTweet.created_at.astimezone()
        tweet.created_at = timestamp.strftime("%m/%d/%Y")
    
        tweet.conversation_id = rawTweet.conversation_id
        tweet.in_reply_to_user_id = rawTweet.in_reply_to_user_id
        tweet.is_ref_tweet = isRefTweet
    
        # convert list of dicts to just a list for referenced tweets
        if (rawTweet.referenced_tweets is not None):
            tweet.list_of_referenced_tweets = []
            for refTweet in rawTweet.referenced_tweets:
                tweet.list_of_referenced_tweets.append(refTweet["type"])
                tweet.list_of_referenced_tweets.append(int(refTweet["id"]))
        else:
            tweet.list_of_referenced_tweets = None
    
        # grab the list of media keys, we will get the media later
        if (rawTweet.attachments is not None) and ("media_keys" in rawTweet.attachments.keys()):
            tweet.list_of_attachments = rawTweet.attachments["media_keys"]
        else:
            tweet.list_of_attachments = None

        # grab the urls if there are any
        urls = {}
        if (rawTweet.entities is not None) and ("urls" in rawTweet.entities.keys()):
            for item in rawTweet.entities["urls"]:
                shortened_url = item["url"]

                # store the shortened url in the Tweet object
                if (shortened_url not in tweet.list_of_urls):
                    tweet.list_of_urls.append(shortened_url)

                # store the shortened url plus the expanded info in URL object, these will be kept in a separate file
                if (shortened_url not in urls):
                    url_obj = Classes.URL()
                    url_obj.shortened_url = shortened_url
                    url_obj.expanded_url = item["expanded_url"]
                    if ("title" in item.keys()):
                        url_obj.title = item["title"]
                    urls[shortened_url] = url_obj

        tweet.text = rawTweet.text
        
        return tweet, urls

    ###########################################################################
    ###########################################################################

    def replaceMediaKeysWithData(self, listOfTweets, listOfMedia):
        for tweet in listOfTweets:
            if (tweet.list_of_attachments is None):
                continue
            
            newAttachmentsList = []
            
            for media_key in tweet.list_of_attachments:
                for mediaObject in listOfMedia:
                    if (media_key == mediaObject.media_key):
                        newAttachmentsList.append(mediaObject.data["type"])
                        if ("url" in mediaObject.data.keys()):
                            newAttachmentsList.append(mediaObject.data["url"])
                        else:
                            newAttachmentsList.append("")
    
            tweet.list_of_attachments = newAttachmentsList
            
        return

    ###########################################################################
    ###########################################################################

    def retrieveTweetsForUser(self, user, defaultStartTime):
        tweet_fields_list = ["id",
                             "text",
                             "author_id",
                             "created_at",
                             "conversation_id",
                             "in_reply_to_user_id",
                             "referenced_tweets",
                             "attachments",
                             "entities"]
        expansions_list = ["referenced_tweets.id", "attachments.media_keys"]
        media_fields_list = ["media_key","type","url"]
    
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)
        
        if (user.mostRecentTweetId > 0):
            self.logger.log("retrieving tweets for handle " + user.twitterHandle + " since_id=" + str(user.mostRecentTweetId))
            responses = tweepy.Paginator(client.get_users_tweets, user.idStr, 
                                         since_id=user.mostRecentTweetId,
                                         max_results=100, # per page
                                         tweet_fields=tweet_fields_list,
                                         media_fields=media_fields_list,
                                         expansions=expansions_list)
        else:
            self.logger.log("retrieving tweets for handle " + user.twitterHandle + " start_time=" + defaultStartTime)
            responses = tweepy.Paginator(client.get_users_tweets, user.idStr, 
                                         start_time=defaultStartTime,
                                         max_results=100, # per page
                                         tweet_fields=tweet_fields_list,
                                         media_fields=media_fields_list,
                                         expansions=expansions_list)
    
        tweets = []
        dictOfUrls = {}
        listOfMedia = []
    
        for response in responses:
            
            if (response.data is None):
                continue
            
            # get the tweets in the data, the oldest tweet will always be in the front of the list
            for rawTweet in response.data:
                tweet, urls = self.copyTweetData(rawTweet, False)
                tweets.insert(0, tweet)
                dictOfUrls.update(urls)
                
            # get the tweets in the includes which detail the referenced tweets, if there are any,
            # these will always be at the back of the list
            if "tweets" in response.includes.keys():
                for rawTweet in response.includes["tweets"]:
                    tweet, urls = self.copyTweetData(rawTweet, True)
                    tweets.append(tweet)
                    dictOfUrls.update(urls)
    
            # grab the media keys if there are any
            if "media" in response.includes.keys():
                listOfMedia = listOfMedia + response.includes["media"]
    
            # get the newest id, this will be used as since_id for the next request
            if int(response.meta["newest_id"]) > user.mostRecentTweetId:
                user.mostRecentTweetId = int(response.meta["newest_id"])
    
        # replace the media keys with the actual data
        self.replaceMediaKeysWithData(tweets, listOfMedia)
        
        self.logger.log("received " + str(len(tweets)) + " for handle " + user.twitterHandle)
        return tweets, dictOfUrls
    
    ###########################################################################
    ###########################################################################

    # The Twitter documentation says the limit for retrieving a user's timeline is 
    # 900 requests per 15 minutes. This is the same as 60 requests per minute. If we 
    # go faster than this limit we could have problems.
    
    # We have about 1000 Twitter handles. If we do 1 handle every 2 seconds, it will take 
    # 2000 seconds or 33.3 minutes. Thus, we will do 1000 requests per 33.3 minutes = 
    # 30 requests per minute. This gives us a little buffer room in case some people tweet
    # excessively or when we are scanning for the first time.
    
    def run(self, secsBetweenHandles=2, numberOfDaysForFirstScan=2):
        currentDate = Utilities.getCurrentDate()
        startTime = Utilities.getPastTimeString(numberOfDaysForFirstScan)
    
        listOfMembers = Utilities.loadCongressMembers()
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        userLookupDict = Utilities.loadUserLookup(listOfMembers, dictOfTwitterUsers)
        
        try:
            self.findMissingUserIds(userLookupDict)
        except BaseException as e:
            self.logger.log("Error: failed to find missing user ids: " + str(e.args))
        logMessage = Utilities.saveUserLookup(userLookupDict)
        self.logger.log(logMessage)
    
        numHandlesRetrieved = 0
        numTweetsSaved = 0
        tweetsToSave = []
        urlsToSave = {}
        for member in listOfMembers:
            for handle in member.twitter:
                if (handle == ""):
                    continue
            
                user = userLookupDict[handle]
                
                for retries in range(0, 3):
                    try:
                        newTweets, urls = self.retrieveTweetsForUser(user, startTime)
                        newTweets.insert(0, "#" + handle) # this will be used to separate tweets between different twitter handles
                        tweetsToSave = tweetsToSave + newTweets
                        urlsToSave.update(urls)
                        break
                    except BaseException as e:
                        if (retries <= 1):
                            self.logger.log("Warning: failed to retrieve tweets for handle " + handle)
                        else:
                            self.logger.log("Error: failed to retrieve tweets for handle " + handle)
                        self.logger.log(str(e.args))
                        time.sleep(2)
                

                if (len(tweetsToSave) > TWEETS_PER_FILE):
                    self.logger.log("saving " + str(len(tweetsToSave)) + " tweets")
                    logMessage = Utilities.saveTweets(tweetsToSave, currentDate)
                    self.logger.log(logMessage)
                    numTweetsSaved += len(tweetsToSave)
                    tweetsToSave = []
    
                numHandlesRetrieved += 1
                time.sleep(secsBetweenHandles) # slow down the requests so we don't exceed the rate limit, and to be nice to Twitter
    
        # save any remaining tweets
        if (len(tweetsToSave) > 0):
            self.logger.log("saving " + str(len(tweetsToSave)) + " tweets")
            logMessage = Utilities.saveTweets(tweetsToSave, currentDate)
            self.logger.log(logMessage)
            numTweetsSaved += len(tweetsToSave)

        # save the urls, run might be called more than once so need to append urls to the file
        self.logger.log("Saving {} urls".format(len(urlsToSave)))
        logMessage = Utilities.saveURLs(urlsToSave, currentDate)
        self.logger.log(logMessage)

        # save the most recent tweet ids so we don't grab the same tweets again
        logMessage = Utilities.saveUserLookup(userLookupDict)
        self.logger.log(logMessage)
        
        self.logger.log("Retrieved a total of " + str(numTweetsSaved) + " tweets")
        self.logger.log("Finished retrieving tweets for " + str(numHandlesRetrieved) + " handles")
        return numTweetsSaved

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    logger.prepareLogFile()
    instance = RetrieveTweets(logger)
    instance.run(2, 2)
    

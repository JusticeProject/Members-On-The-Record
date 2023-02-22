import sys
sys.path.append("../src")

import tweepy
import Utilities
import Classes

TWITTER_HANDLE = "RepMattGaetz"

listOfMembers = Utilities.loadCongressMembers()
dictOfTwitterUsers = Utilities.loadTwitterUsers()
userLookupDict = Utilities.loadTwitterLookup(listOfMembers, dictOfTwitterUsers)
user = userLookupDict[TWITTER_HANDLE.lower()]

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

defaultStartTime = Utilities.getPastTimeString(2)
responses = tweepy.Paginator(client.get_users_tweets, user.idStr, 
                             start_time=defaultStartTime,
                             max_results=100, # per page
                             tweet_fields=tweet_fields_list,
                             media_fields=media_fields_list,
                             expansions=expansions_list)



for response in responses:
    print("got response")
    break

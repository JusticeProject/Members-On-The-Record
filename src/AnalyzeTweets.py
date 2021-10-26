import re

import Utilities
import Classes

###############################################################################
###############################################################################

class AnalyzeTweets:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################
    
    def getTweetsForHandle(self, listOfAllTweets, handle):
        # split tweets into two categories
        dictUserTweets = {}
        dictRefTweets = {}
        
        foundHandle = False
        for line in listOfAllTweets:
            if (line[0] == "#"):
                potentialHandle = line[1:]
                if (potentialHandle == handle):
                    foundHandle = True
                else:
                    foundHandle = False
            elif (foundHandle == True):
                tweet = Classes.Tweet()
                tweet.setData(line)
    
                if (tweet.is_ref_tweet == True):
                    dictRefTweets[tweet.id] = tweet
                else:
                    dictUserTweets[tweet.id] = tweet
        
        return dictUserTweets,dictRefTweets

    ###########################################################################
    ###########################################################################

    def getConversation(self, firstTweet, dictUserTweets, dictRefTweets):
        conversation = [firstTweet]
        
        # add tweets if they are part of the conversation
        for tweetId in dictUserTweets.keys():
            if (firstTweet.conversation_id == dictUserTweets[tweetId].conversation_id):
                conversation.append(dictUserTweets[tweetId])
            
        # all tweets in this conversation should be removed from the big list of tweets so we don't search them again later
        for tweet in conversation:
            if (tweet.id in dictUserTweets.keys()):
                dictUserTweets.pop(tweet.id)
        
        # insert refTweets in the right place, don't pop from the dict because they may be needed more than once
        for tweet in conversation:
            if (tweet.list_of_referenced_tweets == None):
                continue
            
            for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                tweetId = tweet.list_of_referenced_tweets[i+1]
                # we cannot rely on this tweetId being in the ref tweets because the user may have deleted their tweet
                if (tweetId in dictRefTweets.keys()):
                    refTweet = dictRefTweets[tweetId]
                else:
                    refTweet = Classes.Tweet() # just use an empty tweet
                tweet.list_of_referenced_tweets[i+1] = refTweet
        
        return conversation

    ###########################################################################
    ###########################################################################

    def initializeResults(self, dictOfKeywords):
        dictCategorizedConvs = {}
        
        for category in dictOfKeywords.keys():
            dictCategorizedConvs[category] = []
        
        return dictCategorizedConvs

    ###########################################################################
    ###########################################################################

    def categorizeConversation(self, conversation, dictOfKeywords):
        combinedText = ""
        regexWordBoundary = re.compile(r"\b(\S+)\b")
        
        for tweet in conversation:
            combinedText = combinedText + " " + tweet.text
            
            if (tweet.list_of_referenced_tweets == None):
                continue
            
            for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                combinedText = combinedText + " " + tweet.list_of_referenced_tweets[i+1].text
        
        # make all single quotes standard, sometimes the funny single quotes appear
        if ("’" in combinedText) or ("ʻ" in combinedText):
            regexQuote = re.compile(r"[’ʻ]")
            combinedText = regexQuote.sub("'", combinedText)
        
        links = self.findAllLinks(combinedText)
        for link in links:
            link = self.cleanLink(link)
            combinedText = combinedText.replace(link, " ")
        
        combinedTextLower = combinedText.lower()
        
        for category in dictOfKeywords.keys():
            for phrase in dictOfKeywords[category]:
                matched = True
                for word in phrase:
                    if (word[0] == '^'):
                        if (word[1:] not in combinedText):
                            matched = False
                    elif (word[0] == '~'):
                        if (word[1:] in combinedTextLower):
                            matched = False
                    elif (word[0] == '_'):
                        textSplit = regexWordBoundary.findall(combinedTextLower)
                        if (word[1:] not in textSplit):
                            matched = False
                    else:
                        if (word not in combinedTextLower):
                            matched = False
                            
                if (matched == True):
                    return category
        
        return None
        
    ###########################################################################
    ###########################################################################
    
    def getInfoOfTweeter(self, author_id, userLookupDict, listOfMembers):
        # get handle
        for user in userLookupDict.values():
            if (user.idStr == str(author_id)):
                foundUser = user
                break
        
        # get member
        for member in listOfMembers:
            for handle in member.twitter:
                if (foundUser.twitterHandle == handle):
                    name = member.last_name
                    party = member.party
                    state = member.state
                    if (member.district.strip() != ""):
                        state += "-" + member.district
        
        return name,party,state

    ###########################################################################
    ###########################################################################

    def isConvARetweet(self, conv):
        if (conv[0].list_of_referenced_tweets == None):
            return False
        
        for i in range(0, len(conv[0].list_of_referenced_tweets), 2):
            if (conv[0].list_of_referenced_tweets[i] == "retweeted"):
                return True
            
        return False

    ###########################################################################
    ###########################################################################
    
    def isTweetAReplyToSomeoneElse(self, tweet):        
        if (tweet.in_reply_to_user_id > 0) and (tweet.in_reply_to_user_id != tweet.author_id):
            return True
        else:
            return False

    ###########################################################################
    ###########################################################################
    
    def getRepliedToLink(self, tweet, visibleText):
        if (tweet.list_of_referenced_tweets == None):
            return ""
            
        for j in range(0, len(tweet.list_of_referenced_tweets), 2):
            if (tweet.list_of_referenced_tweets[j] == "replied_to"):
                link = "https://twitter.com/i/web/status/" + str(tweet.list_of_referenced_tweets[j+1].id)
                result = '<a href="' + link + '">' + visibleText + '</a>'
                return result

        return ""

    ###########################################################################
    ###########################################################################
    
    def findAllLinks(self, text):
        regex = re.compile(r"(https://\S+)")
        links = regex.findall(text)
        return links

    ###########################################################################
    ###########################################################################

    def cleanLink(self, link):
        endChar = link[-1]
        if (endChar == '.') or (endChar == '"') or (endChar == "'"):
            return link[:-1]
        else:
            return link
    
    ###########################################################################
    ###########################################################################

    def convertLink(self, text, linkToReplace, newLink, descr):
        html = '<a href="' + newLink + '">' + descr + '</a>'
        convertedText = text.replace(linkToReplace, html)
        return convertedText
    
    ###########################################################################
    ###########################################################################

    def formatLinksInText(self, tweet):
        foundQuoted = False
        foundAttachments = False
        typeOfAttachment = "media"
        
        if (tweet.list_of_referenced_tweets != None):
            for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                if (tweet.list_of_referenced_tweets[i] == "quoted"):
                    foundQuoted = True
        
        if (tweet.list_of_attachments != None):
            foundAttachments = True
            for i in range(0, len(tweet.list_of_attachments), 2):
                typeOfAttachment = tweet.list_of_attachments[i].replace("_", " ") # e.g. animated_gif
        
        links = self.findAllLinks(tweet.text)
        text = tweet.text
    
        # link to the quoted tweet will be at the end of the tweet text
        if (foundQuoted == True):
            text = self.convertLink(text, links[-1], links[-1], "Link to quoted tweet")
            links.pop(-1)
        
        if (foundAttachments == True):
            text = self.convertLink(text, links[-1], links[-1], "Link to " + typeOfAttachment)
            links.pop(-1)
    
        # handle any remaining links, these links could be in the middle of the text and run into other text, thus
        # creating a bad link, but we'll try our best to clean it up
        for link in links:
            link = self.cleanLink(link)
            realURL, message = Utilities.unshortenURL(link)
            if (message != ""):
                self.logger.log(message)
            
            domain = Utilities.getDomainOfURL(realURL)
    
            if (domain == ""):
                self.logger.log("Warning: failed to parse url " + link)
                continue # we couldn't parse the url properly, leave it as is and move on to the next link
            elif ("twitter.com" in realURL) and ("/photo/" in realURL):
                descr = "Link to photo"
            elif ("twitter.com" in realURL) and ("/video/" in realURL):
                descr = "Link to video"
            else:
                descr = "Link to " + domain
            text = self.convertLink(text, link, realURL, descr)
    
        return text
    
    ###########################################################################
    ###########################################################################

    def formatConversation(self, conversation, userLookupDict, listOfMembers):
        formattedTweet = Classes.FormattedTweet()
    
        formattedTweet.id = conversation[0].id
        name,party,state = self.getInfoOfTweeter(conversation[0].author_id, userLookupDict, listOfMembers)
        formattedTweet.name = name
        if (party == "") or (state == ""):
            formattedTweet.partyAndState = ""
        else:
            formattedTweet.partyAndState = " (" + party + "-" + state + ")"
        formattedTweet.day = conversation[0].created_at
            
        if (self.isConvARetweet(conversation) == True):
            retweetHandle = re.findall(r"(@\w+):", conversation[0].text)[0]
            formattedTweet.type = "Retweet of " + retweetHandle
            for i in range(0, len(conversation[0].list_of_referenced_tweets), 2):
                if (conversation[0].list_of_referenced_tweets[i] == "retweeted"):
                    formattedTweet.text = self.formatLinksInText(conversation[0].list_of_referenced_tweets[i+1])
        elif (self.isTweetAReplyToSomeoneElse(conversation[0]) == True):
            link = self.getRepliedToLink(conversation[0], "Tweet")
            if (link == ""):
                formattedTweet.type = "Tweet"
            else:
                formattedTweet.type = "In reply to " + link
            formattedTweet.text = self.formatLinksInText(conversation[0])
        else:
            if (len(conversation) == 1):
                formattedTweet.type = "Tweet"
            else:
                formattedTweet.type = "Twitter thread"
            formattedTweet.text = self.formatLinksInText(conversation[0])
    
        # if they replied to their tweet, add the additional tweet(s)
        for i in range(1, len(conversation)):
            currentTweet = conversation[i]
            # if they replied to someone else's tweet in between
            if (self.isTweetAReplyToSomeoneElse(currentTweet)):
                formattedTweet.text += " " + self.getRepliedToLink(currentTweet, "Link to reply")
            formattedTweet.text += " " + self.formatLinksInText(currentTweet)
    
        # if there are multiple hyperlinks in a row, put a little space in between for readability
        regexLinkSpace = re.compile(r"</a>\s*<a")
        formattedTweet.text = regexLinkSpace.sub(r"</a> &nbsp; <a", formattedTweet.text)
    
        return formattedTweet

    ###########################################################################
    ###########################################################################

    def run(self):
        dictOfKeywords = Utilities.getKeywords()
        dictCategorizedConvs = self.initializeResults(dictOfKeywords)
        listOfMembers = Utilities.loadCongressMembers()
        resultsFolder = Utilities.getMostRecentResultsFolder()
        self.logger.log("Analyzing results for " + resultsFolder)
        listOfAllTweets = Utilities.loadTweets(1)
        
        
        for member in listOfMembers:
            for handle in member.twitter:
                if (handle == ""):
                    continue
        
                dictUserTweets,dictRefTweets = self.getTweetsForHandle(listOfAllTweets, handle)
                
                while (len(dictUserTweets) > 0):
                    listOfTweetIds = list(dictUserTweets.keys())
                    currentTweet = dictUserTweets.pop(listOfTweetIds[0])
                    conversation = self.getConversation(currentTweet, dictUserTweets, dictRefTweets)
                    
                    category = self.categorizeConversation(conversation, dictOfKeywords)
                    if (category != None):
                        dictCategorizedConvs[category].append(conversation)
        
        self.logger.log("Finished categorizing conversations")
        
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        userLookupDict = Utilities.loadUserLookup(listOfMembers, dictOfTwitterUsers)
        
        dictFormattedConvs = {}
        for category in dictCategorizedConvs.keys():
            for conversation in dictCategorizedConvs[category]:
                self.logger.log("formatting conversation id " + str(conversation[0].conversation_id))
                formattedTweet = self.formatConversation(conversation, userLookupDict, listOfMembers)
                
                if category in dictFormattedConvs.keys():
                    dictFormattedConvs[category].append(formattedTweet)
                else:
                    dictFormattedConvs[category] = [formattedTweet]
        
        
        timestamp = Utilities.getWashingtonTime()
        listOfMessages = ["Last updated on " + timestamp]
        if (len(dictFormattedConvs) == 0):
            listOfMessages.append("No relevant tweets found yet for today. Try looking at yesterday's results.")
        
        htmlTemplate = Utilities.getHTMLTemplate()
        dateSortable = re.findall(r"/(20\S+)/", resultsFolder)[0]
        dateReadable = Utilities.convertDateToReadable(dateSortable)
        htmlResults = htmlTemplate.render(date=dateReadable, dictFormattedConvs=dictFormattedConvs, listOfMessages=listOfMessages)
        logMessage, resultsFileName = Utilities.saveHTMLResults(resultsFolder, dateSortable + ".html", htmlResults)
        self.logger.log(logMessage)
        
        return resultsFileName

###############################################################################
###############################################################################
    
if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = AnalyzeTweets(logger)
    instance.run()
    

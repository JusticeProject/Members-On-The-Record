import re
import os.path
import time
import requests
import pytesseract

import Utilities
import Classes

###############################################################################
###############################################################################

class AnalyzeTweets:
    def __init__(self, logger):
        self.logger = logger
        self.resultsFolder = ""
        self.scanImages = False
        
        # These HTML tags are used to highlight the keyword in the Tweet.
        self.leftHighlightSpan = '<span class="MOTR_Keyword">'
        self.rightHighlightSpan = '</span>'

        # These HTML tags are used to show the text captured from images/photos
        self.leftBlockQuote = ' [Text captured from image:<blockquote style="white-space: pre-line">'
        self.rightBlockQuote = "</blockquote>]"
        
        # This dictionary will keep track of the phrases to highlight for each conversation id.
        # Key = conversation id, value = phrase.
        self.dictConvPhrases = {}

    ###########################################################################
    ###########################################################################

    def getTweetsForHandle(self, listOfAllTweets, handle):
        # Split tweets into two categories, userTweets are the actual user's Tweets, the refTweets
        # are the Tweets that the user is referencing (quoted Tweet, retweet, a Tweet they are replying to)
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
    
    def downloadPhoto(self, url):
        filename = url.rsplit("/", 1)[1]
        localPath = self.resultsFolder + filename
        
        if (os.path.exists(localPath)):
            self.logger.log(localPath + " already exists")
            return localPath
        else:
            time.sleep(1) # be nice to Twitter, don't hit them too fast with lots of requests for downloads

            for retries in range(0, 3):
                try:
                    seconds = retries + 2  # first 2 seconds, then 3, then 4
                    req = requests.get(url, headers=Utilities.CUSTOM_HTTP_HEADER, timeout=seconds)
                    file = open(localPath, "wb")
                    file.write(req.content)
                    file.close()
                    self.logger.log("After " + str(retries) + " retries, image saved to " + localPath)
                    return localPath
                except BaseException as e:
                    if (retries < 2):
                        time.sleep(1)
                    else:
                        self.logger.log("Warning: could not download photo: " + str(e.args))
            
        return ""

    ###########################################################################
    ###########################################################################

    def convertPhotoToText(self, localPath):
        if (localPath == ""):
            return ""
        else:
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            text = pytesseract.image_to_string(localPath)
            text = text.replace("<", "") # clean up the text, these symbols could cause problems with html formatting
            text = text.replace(">", "")
            return text

    ###########################################################################
    ###########################################################################
    
    # Group all Tweets with the same conversation id into one list of Tweets. This will
    # be referred to as the "conversation"
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

        for tweet in conversation:
            # insert refTweets in the right place, don't pop from the dict because they may be needed more than once
            if (tweet.list_of_referenced_tweets is not None):
                for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                    tweetId = tweet.list_of_referenced_tweets[i+1]
                    # we cannot rely on this tweetId being in the ref tweets because the user may have deleted their tweet
                    if (tweetId in dictRefTweets.keys()):
                        refTweet = dictRefTweets[tweetId]
                    else:
                        refTweet = Classes.Tweet() # just use an empty tweet
                    tweet.list_of_referenced_tweets[i+1] = refTweet

            # If any photos were attached to the tweets then grab them. We will not include photos attached to
            # ref tweets. We are mainly trying to get released statements from the Congress members.
            if (self.scanImages) and (tweet.list_of_attachments is not None):
                for i in range(0, len(tweet.list_of_attachments), 2):
                    if (tweet.list_of_attachments[i] == "photo"):
                        url = tweet.list_of_attachments[i+1]
                        localPath = self.downloadPhoto(url)
                        capturedText = self.convertPhotoToText(localPath)
                        tweet.list_of_attachments[i+1] = capturedText
                    else:
                        # for all other types of attachments we won't search the text
                        tweet.list_of_attachments[i + 1] = ""

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

    # Look for the keywords in all Tweets of the conversation. This includes quoted
    # Tweets
    def categorizeConversation(self, conversation, dictOfKeywords):
        combinedText = ""
        regexWordBoundary = re.compile(r"\b(\S+)\b")
        
        for tweet in conversation:
            combinedText = combinedText + " " + tweet.text

            # Add text from each ref tweet
            if (tweet.list_of_referenced_tweets is not None):
                for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                    combinedText = combinedText + " " + tweet.list_of_referenced_tweets[i+1].text
                    
            # Add text from each attachment (image)
            if (self.scanImages) and (tweet.list_of_attachments is not None):
                for i in range(0, len(tweet.list_of_attachments), 2):
                    combinedText = combinedText + " " + tweet.list_of_attachments[i+1]

        # make all single quotes standard, sometimes the funny single quotes appear
        if ("’" in combinedText) or ("ʻ" in combinedText):
            regexQuote = re.compile(r"[’ʻ]")
            combinedText = regexQuote.sub("'", combinedText)
        
        # We won't be searching in the links for keywords. Twitter uses a URL shortener and sometimes
        # keywords like BDS will appear in the link. Ex: https://t.co/Lo4kVBDsop
        links = self.findAllLinks(combinedText)
        for link in links:
            link = self.cleanLink(link)
            combinedText = combinedText.replace(link, " ")
        
        combinedTextLower = combinedText.lower()
        
        # Search the combined text of the conversation, use the categories from Keywords.txt
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
                    self.dictConvPhrases[conversation[0].conversation_id] = phrase
                    return category
        
        return None
        
    ###########################################################################
    ###########################################################################
    
    # Add html tags to highlight the keyword that was found. Super handy when you're 
    # staring at a huge Twitter thread and wondering "why did the search grab these Tweets?!"
    def highlightKeywordsInConversation(self, conversation, phrase):        
        # Do the highlighting for each Tweet and the referenced Tweets
        for tweet in conversation:
            tweet.text = self.highlightKeywords(tweet.text, phrase)

            # highlight text in any referenced tweets
            if (tweet.list_of_referenced_tweets is not None):
                for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                    refTweet = tweet.list_of_referenced_tweets[i+1]
                    refTweet.text = self.highlightKeywords(refTweet.text, phrase)

            # highlight text in any attachments
            if (self.scanImages) and (tweet.list_of_attachments is not None):
                for i in range(0, len(tweet.list_of_attachments), 2):
                    highlightedText = self.highlightKeywords(tweet.list_of_attachments[i+1], phrase)
                    tweet.list_of_attachments[i+1] = highlightedText
        return

    ###########################################################################
    ###########################################################################
    
    def highlightKeywords(self, text, wordsToHighlight):
        # if <span> tag is already in there then don't do it again, this might be a ref tweet that multiple
        # tweets are referencing
        if (self.leftHighlightSpan in text):
            return text
        
        # first grab the links, if we screw up the links by adding the highlights then
        # we need to restore them
        preHighlightLinks = self.findAllLinks(text)
        
        highlightedText = text
        for word in wordsToHighlight:
            if (word[0] == '^'):
                instances = re.findall(word[1:], text)
            elif (word[0] == '~'):
                continue
            elif (word[0] == '_'):
                regex = re.compile(r"\b(" + word[1:] + r")\b", flags=re.IGNORECASE)
                instances = regex.findall(text)
            else:
                instances = re.findall(word, text, flags=re.IGNORECASE)
            
            uniqueInstances = list(set(instances)) # converting to a set then to a list will remove duplicates
            for instance in uniqueInstances:
                replacement = self.leftHighlightSpan + instance + self.rightHighlightSpan
                highlightedText = re.sub(instance, replacement, highlightedText)
        
                # Grab the links again to see if they have been affected
                postHighlightLinks = self.findAllLinks(highlightedText)
                
                # If the links are seriously affected then don't continue, just return the un-highlighted text
                if (len(preHighlightLinks) != len(postHighlightLinks)):
                    self.logger.log("Warning: highlighting screws up the links, removing the highlights")
                    return text
            
                # Restore any links while keeping the other words highlighted. Example:
                # https://t.co/FXQMlIranHDYw6  could get accidentally changed to
                # https://t.co/FXQMl<span class="MOTR_Keyword">Iran</span>HDYw6
                for link in postHighlightLinks:
                    if ("<span" in link):
                        self.logger.log("Warning: highlighting modified a link, trying to fix the link: " + link)
                        linkBeginning = link.split("<span")[0]
                        highlightedText = highlightedText.replace(linkBeginning + replacement, 
                                                                  linkBeginning + instance)
        
        return highlightedText

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
                    url = member.url
        
        return name,party,state,url

    ###########################################################################
    ###########################################################################

    def isConvARetweet(self, conv):
        if (conv[0].list_of_referenced_tweets is None):
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
    
    def isTweetAReplyToThemself(self, tweet):
        if (tweet.in_reply_to_user_id > 0) and (tweet.in_reply_to_user_id == tweet.author_id):
            return True
        else:
            return False

    ###########################################################################
    ###########################################################################
    
    def getRepliedToLink(self, tweet, visibleText):
        if (tweet.list_of_referenced_tweets is None):
            return ""
        
        for j in range(0, len(tweet.list_of_referenced_tweets), 2):
            if (tweet.list_of_referenced_tweets[j] == "replied_to"):
                refTweet = tweet.list_of_referenced_tweets[j+1]
                if (refTweet.text == ""):
                    return "" # the tweet was probably deleted, so don't link to it
                else:
                    link = "https://twitter.com/i/web/status/" + str(refTweet.id)
                    result = self.createLinkWithTooltip(link, visibleText, refTweet.text)
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
    
    # Tooltips will be used to display the text of a quoted Tweet or a reply in the
    # conversation. These are Tweets from other users, not the main user we are dealing
    # with. The link will be available for clicking on as well so you can see the 
    # actual Tweet on Twitter.com.
    def createLinkWithTooltip(self, newLink, visibleText, tooltipText):
        html = '<a class="MOTR_Tooltip" href="' + newLink + '">' + visibleText + \
            '<span class="MOTR_Tooltiptext">' + tooltipText + '</span></a>'
        return html

    ###########################################################################
    ###########################################################################

    # Convert something like https://t.co/Lo4kVBDsop to an HTML hyperlink with the appropriate
    # tags around it. Sometimes we will be replacing the link with an unshortened URL so it's more
    # user friendly.
    def convertLink(self, text, linkToReplace, newLink, visibleText, addTooltip=False, tooltipText = ""):
        if (addTooltip and len(tooltipText) > 0):
            html = self.createLinkWithTooltip(newLink, visibleText, tooltipText)
        else:
            html = '<a href="' + newLink + '">' + visibleText + '</a>'
        convertedText = text.replace(linkToReplace, html)
        return convertedText
    
    ###########################################################################
    ###########################################################################

    # For each link in the Tweet's text we will make it an HTML hyperlink.
    def formatLinksInText(self, tweet):
        foundQuoted = False
        quotedTweet = Classes.Tweet() # use an empty tweet for now
        foundAttachments = False
        typeOfAttachment = "media"
        
        if (tweet.list_of_referenced_tweets is not None):
            for i in range(0, len(tweet.list_of_referenced_tweets), 2):
                if (tweet.list_of_referenced_tweets[i] == "quoted"):
                    foundQuoted = True
                    quotedTweet = tweet.list_of_referenced_tweets[i+1]
        
        if (tweet.list_of_attachments is not None):
            foundAttachments = True
            for i in range(0, len(tweet.list_of_attachments), 2):
                typeOfAttachment = tweet.list_of_attachments[i].replace("_", " ") # e.g. animated_gif
                typeOfAttachment = typeOfAttachment.replace("photo", "image")
        
        links = self.findAllLinks(tweet.text)
        text = tweet.text
    
        # link to the quoted tweet will be at the end of the tweet text
        if (foundQuoted == True) and (len(links) > 0):
            if (isinstance(quotedTweet, int)):
                quotedTweet = Classes.Tweet() # user may have deleted their quoted tweet, so set it to a blank
            text = self.convertLink(text, links[-1], links[-1], "Link to quoted tweet", True, quotedTweet.text)
            links.pop(-1)
        
        if (foundAttachments == True) and (len(links) > 0):
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
                descr = "Link to image"
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
        name,party,state,url = self.getInfoOfTweeter(conversation[0].author_id, userLookupDict, listOfMembers)
        formattedTweet.name = name
        if (party == "") or (state == ""):
            formattedTweet.partyAndState = ""
        else:
            formattedTweet.partyAndState = " (" + party + "-" + state + ")"
        formattedTweet.day = conversation[0].created_at
        
        # highlight the keywords in the conversation
        convID = conversation[0].conversation_id
        phrase = self.dictConvPhrases[convID]
        self.highlightKeywordsInConversation(conversation, phrase)
        
        # Start grouping the text together and formatting the links.
        if (self.isConvARetweet(conversation) == True):
            cleanText = conversation[0].text.replace(self.leftHighlightSpan, "").replace(self.rightHighlightSpan, "")
            allHandles = re.findall(r"(@\w+):", cleanText)
            retweetHandle = allHandles[0]
            retweetHandle = self.highlightKeywords(retweetHandle, phrase) # keyword may be part of the handle that was retweeted
            formattedTweet.type = "Retweet of " + retweetHandle
            for i in range(0, len(conversation[0].list_of_referenced_tweets), 2):
                if (conversation[0].list_of_referenced_tweets[i] == "retweeted"):
                    # Double check we have a valid ref tweet that was received from Twitter
                    refTweet = conversation[0].list_of_referenced_tweets[i+1]
                    if (refTweet.text == ""):
                        formattedTweet.text = self.formatLinksInText(conversation[0])
                    else:
                        formattedTweet.text = self.formatLinksInText(refTweet)
        elif (self.isTweetAReplyToSomeoneElse(conversation[0]) == True) or (self.isTweetAReplyToThemself(conversation[0]) == True):
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

        # Gather all of the text from the attachments.
        attachmentText = ""
        for tweet in conversation:
            if (self.scanImages) and (tweet.list_of_attachments is not None):
                for i in range(0, len(tweet.list_of_attachments), 2):
                    attachmentText = attachmentText + " " + tweet.list_of_attachments[i+1]
        # Replace single newlines with a space, keep multi-newlines. We find a pattern with char-newline-char
        # and replace it with char-space-char. Groups \1 and \3 are the chars that we need to keep in the string.
        #attachmentText = re.sub(r"(\S)(\n)(\S)", r"\1 \3", attachmentText)

        # We will include the attachment text if it meets certain conditions
        if (len(attachmentText) < 200):
            if (self.leftHighlightSpan not in formattedTweet.text) and (self.leftHighlightSpan in attachmentText):
                formattedTweet.text += self.leftBlockQuote + attachmentText + self.rightBlockQuote
        elif (len(attachmentText) < 5000):
            if (self.leftHighlightSpan in attachmentText):
                formattedTweet.text += self.leftBlockQuote + attachmentText + self.rightBlockQuote
        else:
            if (self.leftHighlightSpan not in formattedTweet.text) and (self.leftHighlightSpan in attachmentText):
                # TODO: should I trim the text? ex: "... blah blah keyword blah blah ..."
                formattedTweet.text += self.leftBlockQuote + attachmentText + self.rightBlockQuote

        return formattedTweet

    ###########################################################################
    ###########################################################################
    
    def findOriginalConv(self, conversation, listOfConvs):
        if (conversation[0].list_of_referenced_tweets is None):
            return None
        
        for i in range(0, len(conversation[0].list_of_referenced_tweets), 2):
            if (conversation[0].list_of_referenced_tweets[i] == "retweeted"):
                refTweetId = conversation[0].list_of_referenced_tweets[i+1].id
                
                for potentialConv in listOfConvs:
                    if (refTweetId == potentialConv[0].id):
                        return potentialConv
            
        return None

    ###########################################################################
    ###########################################################################
    
    def convsBelongToSamePerson(self, conv1, conv2, userLookupDict, listOfMembers):
        name1,party1,state1,url1 = self.getInfoOfTweeter(conv1[0].author_id, userLookupDict, listOfMembers)
        name2,party2,state2,url2 = self.getInfoOfTweeter(conv2[0].author_id, userLookupDict, listOfMembers)
        
        if (name1 == name2) and (party1 == party2) and (state1 == state2) and (url1 == url2):
            return True,name1
        else:
            return False,""
    
    ###########################################################################
    ###########################################################################
    
    def removeRepeatConvs(self, dictCategorizedConvs, userLookupDict, listOfMembers):
        convsToRemove = []
        
        for category in dictCategorizedConvs.keys():
            for conversation in dictCategorizedConvs[category]:
                if (self.isConvARetweet(conversation) == True):
                    
                    # check if this tweet and the original tweet are in this same category
                    originalConv = self.findOriginalConv(conversation, dictCategorizedConvs[category])
                    if (originalConv is not None):
                        
                        # check if this tweet and the original tweet are from author id's that belong to the same person
                        same,name = self.convsBelongToSamePerson(conversation, originalConv, userLookupDict, listOfMembers)
                        if (same == True):
                    
                            # check if this conversation only has one tweet
                            if (len(conversation) == 1):
                                self.logger.log("Removing duplicate conv from " + name + ": " + conversation[0].text)
                                self.logger.log("Keeping original conv from " + name + ": " + originalConv[0].text)
                                convsToRemove.append( (category, conversation) )
                
        # delete the conversations that are repeats
        for category,conv in convsToRemove:
            dictCategorizedConvs[category].remove(conv)
        
        return dictCategorizedConvs

    ###########################################################################
    ###########################################################################

    def run(self, path = "", scanImages = False):
        dictOfKeywords = Utilities.getKeywords()
        dictCategorizedConvs = self.initializeResults(dictOfKeywords)
        listOfMembers = Utilities.loadCongressMembers()
        if (path == ""):
            self.resultsFolder = Utilities.getMostRecentResultsFolder()
        else:
            self.resultsFolder = path
        self.logger.log("Analyzing results for " + self.resultsFolder)
        self.scanImages = scanImages
        listOfAllTweets = Utilities.loadTweets(self.resultsFolder)
        
        
        for member in listOfMembers:
            for handle in member.twitter:
                if (handle == ""):
                    continue
        
                # Get the Tweets for one Twitter handle at a time.
                dictUserTweets,dictRefTweets = self.getTweetsForHandle(listOfAllTweets, handle)
                #self.logger.log("Analyzing " + str(len(dictUserTweets)) + " tweets for handle " + handle)
                
                # Go through each Tweet and remove it from the dictionary so we don't process it again.
                # Tweets from the same conversation will be removed from the dictionary in getConversation.
                # Categorize the entire conversation. And keep doing this until no more Tweets left.
                while (len(dictUserTweets) > 0):
                    listOfTweetIds = list(dictUserTweets.keys())
                    currentTweet = dictUserTweets.pop(listOfTweetIds[0])
                    conversation = self.getConversation(currentTweet, dictUserTweets, dictRefTweets)
                    
                    category = self.categorizeConversation(conversation, dictOfKeywords)
                    if (category is not None):
                        dictCategorizedConvs[category].append(conversation)
        
        self.logger.log("Finished categorizing conversations")
        
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        userLookupDict = Utilities.loadUserLookup(listOfMembers, dictOfTwitterUsers)
        
        # Look for repeats, i.e. when someone retweets the same message from multiple accounts that they own
        self.logger.log("Looking for repeats")
        dictCategorizedConvs = self.removeRepeatConvs(dictCategorizedConvs, userLookupDict, listOfMembers)
        
        # Now we will format each conversation so that it will appear neatly in the HTML results.
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
        
        # Use jinja2 to put our results into the HTML template
        htmlTemplate = Utilities.getHTMLTemplate()
        dateSortable = re.findall(r"/(20\S+)/", self.resultsFolder)[0]
        dateReadable = Utilities.convertDateToReadable(dateSortable)
        htmlResults = htmlTemplate.render(date=dateReadable, dictFormattedConvs=dictFormattedConvs, listOfMessages=listOfMessages)
        logMessage, resultsFileName = Utilities.saveHTMLResults(self.resultsFolder, dateSortable + ".html", htmlResults)
        self.logger.log(logMessage)
        
        return resultsFileName

###############################################################################
###############################################################################
    
if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = AnalyzeTweets(logger)
    instance.run("", False)
    

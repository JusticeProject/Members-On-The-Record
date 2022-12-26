class CongressMember:
    def __init__(self):
        self.last_name = ""
        self.first_name = ""
        self.middle_name = ""
        self.suffix = ""
        self.nickname = ""
        self.full_name = ""
        self.house = ""
        self.state = ""
        self.district = ""
        self.party = ""
        self.url = ""
        self.url_press = ""
        self.twitter = []
        
    def setData(self, lineOfData):
        line_split = lineOfData.split(",")
        self.last_name = line_split[0]
        self.first_name = line_split[1]
        self.middle_name = line_split[2]
        self.suffix = line_split[3]
        self.nickname = line_split[4]
        self.full_name = line_split[5]
        self.house = line_split[6]
        self.state = line_split[7]
        self.district = line_split[8]
        self.party = line_split[9]
        self.url = line_split[10]
        self.url_press = line_split[11]
        self.twitter = []
        for handle in line_split[12].split(";"):
            self.twitter.append(handle.lower().strip())
    
    def __str__(self):
        totalString = self.last_name + "," + self.first_name + "," + self.middle_name + "," + \
            self.suffix + "," + self.nickname + "," + self.full_name + "," + self.house + "," + \
            self.state + "," + self.district + "," + self.party + "," + self.url + "," + self.url_press + ","

        joinedHandles = ";".join(self.twitter)
        totalString += joinedHandles + ","

        totalString = totalString.replace("\n", "")
        return totalString
    
    def __lt__(self, other):
        return self.last_name < other.last_name

###############################################################################
###############################################################################

class TwitterUser:
    def __init__(self, twitterHandle = "", idStr="", mostRecentTweetId=0, website = "", name = "", description = ""):
        self.twitterHandle = twitterHandle.lower() # save some headaches later
        self.idStr = idStr
        self.mostRecentTweetId = mostRecentTweetId
        
        if (website is None):
            self.website = ""
        else:
            self.website = website
        
        self.name = name.replace(",", "") # if there are commas in the name it could cause problems
        
        if (description is None):
            self.description = ""
        else:
            cleanDescription = description.replace("\r", "")
            cleanDescription = cleanDescription.replace("\n", "")
            self.description = cleanDescription
        
    def setData(self, lineOfData):
        line_split = lineOfData.split(",", 5)
        self.twitterHandle = line_split[0].lower()
        self.idStr = line_split[1]
        self.mostRecentTweetId = int(line_split[2])
        self.website = line_split[3]
        self.name = line_split[4]
        self.description = line_split[5]
    
    def minimize(self):
        self.website = ""
        self.name = ""
        self.description = ""
        
    def __str__(self):
        return self.twitterHandle + "," + self.idStr + "," + str(self.mostRecentTweetId) + "," + \
            self.website + "," + self.name + "," + self.description

###############################################################################
###############################################################################

class Tweet:
    def __init__(self):
        self.id = 0
        self.id_str = ""
        self.author_id = 0
        self.author_id_str = ""
        self.created_at = ""
        self.conversation_id = 0
        self.in_reply_to_user_id = 0
        self.is_ref_tweet = False
        self.list_of_referenced_tweets = []
        self.list_of_attachments = []
        self.list_of_urls = [] # just the shortened urls
        self.text = ""

        # These items are not stored to a file
        self.keyword_phrase = ""
        self.dictLinks = {} # key = shortened url, value = URL object
        
    def setData(self, lineOfData):
        line_split = lineOfData.split(",", 11)
        
        self.id = int(line_split[0])
        self.id_str = line_split[1]
        self.author_id = int(line_split[2])
        self.author_id_str = line_split[3]
        self.created_at = line_split[4]
        self.conversation_id = int(line_split[5])
        self.in_reply_to_user_id = int(line_split[6])
        
        if (line_split[7] == "False"):
            self.is_ref_tweet = False
        else:
            self.is_ref_tweet = True
            
        if (line_split[8] == ""):
            self.list_of_referenced_tweets = None
        else:
            self.list_of_referenced_tweets = line_split[8].split(";")
            for i in range(0, len(self.list_of_referenced_tweets), 2):
                self.list_of_referenced_tweets[i+1] = int(self.list_of_referenced_tweets[i+1])
        
        if (line_split[9] == ""):
            self.list_of_attachments = None
        else:
            self.list_of_attachments = line_split[9].split(";")

        if (line_split[10] == ""):
            self.list_of_urls = None
        else:
            self.list_of_urls = line_split[10].split(";")
        
        self.text = line_split[11].strip()
        # make all single quotes standard, sometimes the funny single quotes appear
        if ("’" in self.text) or ("ʻ" in self.text):
            self.text = self.text.replace("’", "'")
            self.text = self.text.replace("ʻ", "'")
        
    def __str__(self):
        totalString = str(self.id) + "," + self.id_str + "," + str(self.author_id) + "," + self.author_id_str + "," + \
            self.created_at + "," + str(self.conversation_id) + ","
        
        if (self.in_reply_to_user_id is None):
            totalString += "-1,"
        else:
            totalString = totalString + str(self.in_reply_to_user_id) + ","
        
        totalString = totalString + str(self.is_ref_tweet) + ","
        
        if (self.list_of_referenced_tweets is None) or (len(self.list_of_referenced_tweets) == 0):
            totalString += ","
        else:
            for item in self.list_of_referenced_tweets:
                totalString = totalString + str(item) + ";"
            totalString = totalString[:-1] + "," # get rid of last ; and add a ,
        
        if (self.list_of_attachments is None) or (len(self.list_of_attachments) == 0):
            totalString += ","
        else:
            for item in self.list_of_attachments:
                totalString = totalString + item + ";"
            totalString = totalString[:-1] + "," # get rid of last ; and add a ,

        if (self.list_of_urls is None) or (len(self.list_of_urls) == 0):
            totalString += ","
        else:
            for item in self.list_of_urls:
                totalString = totalString + item.replace(",", "%2C") + ";" # remove commas from URLs
            totalString = totalString[:-1] + ","  # get rid of last ; and add a ,
        
        self.text = self.text.replace("\n", " ")
        self.text = self.text.replace("\r", " ")
        totalString += self.text
        
        return totalString

###############################################################################
###############################################################################

class URL:
    def __init__(self):
        self.shortened_url = ""
        self.expanded_url = ""
        self.title = ""

    def setData(self, lineOfData):
        line_split = lineOfData.split(",", 2)
        self.shortened_url = line_split[0]
        self.expanded_url = line_split[1]
        self.title = line_split[2]

    def __str__(self):
        totalString = self.shortened_url.replace(",", "%2C") + "," + self.expanded_url.replace(",", "%2C") + "," + self.title

        # make all single quotes standard, sometimes the funny single quotes appear
        if ("’" in totalString) or ("ʻ" in totalString):
            totalString = totalString.replace("’", "'")
            totalString = totalString.replace("ʻ", "'")

        totalString = totalString.strip()
        totalString = totalString.replace("\n", "")
        totalString = totalString.replace("\r", "")
        return totalString

###############################################################################
###############################################################################

class FormattedTweet:
    def __init__(self):
        self.link = ""
        self.namePartyState = ""
        self.day = ""
        self.type = ""
        self.text = ""

    def __lt__(self, other):
        return self.namePartyState < other.namePartyState

###############################################################################
###############################################################################

class Page:
    def __init__(self):
        self.subfolder = ""
        self.filename = ""
        self.visibleText = ""
        
###############################################################################
###############################################################################

class Credentials:
    def __init__(self):
        self.Bearer_Token = ""
        self.GitHub_Token = ""
    
    def setData(self, lineOfData):
        if ("Twitter_Bearer_Token=" in lineOfData):
            self.Bearer_Token = lineOfData.split("Twitter_Bearer_Token=")[1].strip()
        elif ("GitHub_Token=" in lineOfData):
            self.GitHub_Token = lineOfData.split("GitHub_Token=")[1].strip()

###############################################################################
###############################################################################

class Config:
    def __init__(self):
        self.Scan_On_Startup = ""
        self.Scan_Images = ""
    
    def setData(self, lineOfData):
        if ("Scan_On_Startup=" in lineOfData):
            text = lineOfData.split("Scan_On_Startup=")[1].strip()
            self.Scan_On_Startup = bool(int(text))
        elif ("Scan_Images=" in lineOfData):
            text = lineOfData.split("Scan_Images=")[1].strip()
            self.Scan_Images = bool(int(text))

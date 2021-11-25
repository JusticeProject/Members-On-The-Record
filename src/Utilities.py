import platform
import os
import os.path
import pathlib
import datetime
import re
import jinja2
import requests
from urllib.parse import urlparse
import urllib.request
import time

import Classes

CONFIG_FILE_NAME = "../config/Config.txt"
CUSTOMIZED_HANDLES_FILE_NAME = "../config/CustomizedTwitterHandles.txt"
LIST_OF_CONGRESS_MEMBERS_FILENAME = "../output/ListOfCongressMembers.txt"
TWITTER_USERS_FROM_LISTS_FILENAME = "../output/TwitterUsersFromTwitterLists.txt"
USER_LOOKUP_FILENAME = "../output/UserLookup.txt"
DEFAULT_LOG_FOLDER = "../output/logs/"
KEYWORDS_FILE_NAME = "../config/Keywords.txt"
TEMPLATE_HTML_FILE_NAME = "template.html"
TEMPLATE_INDEX_RESULTS_FILE_NAME = "template-index-of-results.html"

BYPASS_URL_UNSHORTENER = False

CUSTOM_HTTP_HEADER_WIN10 = {
    "Sec-Ch-Ua":'Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    "Device-Memory":"8",
    "Sec-Ch-Ua-Model":'',
    "Rtt":"50",
    "Sec-Ch-Ua-Mobile":"?0",
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Sec-Ch-Ua-Arch":'"x86"',
    "Viewport-Width":"1536",
    "Sec-Ch-Ua-Full-Version":'"96.0.4664.45"',
    "Sec-Ch-Ua-Platform-Version":'"10.0.0"',
    "Dpr":"1.25",
    "Downlink":"10",
    "Ect":"4g",
    "Sec-Ch-Prefers-Color-Scheme":"light",
    "Sec-Ch-Ua-Platform":'"Windows"',
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Sec-Fetch-Site":"none",
    "Sec-Fetch-Mode":"navigate",
    "Sec-Fetch-Dest":"document",
    "Accept-Encoding":"gzip, deflate",
    "Accept-Language":"en-US,en;q=0.9",
    "Sec-Fetch-User":"?1",
    "Upgrade-Insecure-Requests":"1"
}

CUSTOM_HTTP_HEADER_WIN7 = {
    "Sec-Ch-Ua":'" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
    "Device-Memory":"4",
    "Sec-Ch-Ua-Model":'',
    "Rtt":"50",
    "Sec-Ch-Ua-Mobile":"?0",
    "User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
    "Sec-Ch-Ua-Arch":'"x86"',
    "Viewport-Width":"1600",
    "Sec-Ch-Ua-Full-Version":'"96.0.4664.45"',
    "Sec-Ch-Ua-Platform-Version":'"0.0.0"',
    "Dpr":"1",
    "Downlink":"4.15",
    "Ect":"4g",
    "Sec-Ch-Prefers-Color-Scheme":"light",
    "Sec-Ch-Ua-Platform":'"Windows"',
    "Accept":"application/signed-exchange;v=b3;q=0.7,*/*;q=0.8",
    "Sec-Fetch-Site":"none",
    "Sec-Fetch-Mode":"navigate",
    "Sec-Fetch-Dest":"document",
    "Accept-Encoding":"gzip, deflate",
    "Accept-Language":"en-US,en;q=0.9",
    "Sec-Fetch-User":"?1",
    "Upgrade-Insecure-Requests":"1"
}

###############################################################################
###############################################################################

def getCustomHeader():
    if ("Windows-10" in platform.platform()):
        return CUSTOM_HTTP_HEADER_WIN10
    else:
        return CUSTOM_HTTP_HEADER_WIN7

###############################################################################
###############################################################################

def loadCredentials():
    cred = Classes.Credentials()
    configLines = open(CONFIG_FILE_NAME, "r").readlines()
    for line in configLines:
        cred.setData(line)
    
    return cred

###############################################################################
###############################################################################

def getCustomizedTwitterHandles():
    listOfExcludes = []
    listOfIncludes = []
    listOfSamePersons = []
    
    lines = open(CUSTOMIZED_HANDLES_FILE_NAME, "r").readlines()
    for line in lines:
        if ("exclude=@" in line):
            handle = line.split("@")[1]
            handle = handle.strip().lower()
            listOfExcludes.append(handle)
        elif ("include=@" in line):
            handle = line.split("@")[1]
            handle = handle.strip().lower()
            listOfIncludes.append(handle)
        elif ("same_person=" in line):
            line_split = line.split("@")
            handle1 = line_split[1].replace(",", "").strip().lower()
            handle2 = line_split[2].strip().lower()
            listOfSamePersons.append((handle1, handle2))
    
    return listOfExcludes,listOfIncludes,listOfSamePersons

###############################################################################
###############################################################################

# write the given list of data to a file

def saveCongressMembers(listOfMembers):
    listFile = open(LIST_OF_CONGRESS_MEMBERS_FILENAME, "w", encoding="utf-8")
    for member in listOfMembers:
        listFile.write(str(member) + "\n")
    listFile.close()
    
    logMessage = "data written to file " + LIST_OF_CONGRESS_MEMBERS_FILENAME
    return logMessage

###############################################################################
###############################################################################

def loadCongressMembers():
    listOfMembers = []
    listFileLines = open(LIST_OF_CONGRESS_MEMBERS_FILENAME, "r", encoding="utf-8").readlines()
    for line in listFileLines:
        member = Classes.CongressMember()
        member.setData(line)
        listOfMembers.append(member)
    
    return listOfMembers

###############################################################################
###############################################################################

def isCongressListAvailable():
    if (os.path.exists(LIST_OF_CONGRESS_MEMBERS_FILENAME) == False):
        return False
    
    if (os.path.exists(TWITTER_USERS_FROM_LISTS_FILENAME) == False):
        return False
    
    return True

###############################################################################
###############################################################################

def loadTwitterUsers():
    dictOfTwitterUsers = {}
    twitterHandlesLines = open(TWITTER_USERS_FROM_LISTS_FILENAME, "r", encoding="utf-8").readlines()
    for line in twitterHandlesLines:
        user = Classes.TwitterUser()
        user.setData(line)
        dictOfTwitterUsers[user.twitterHandle] = user
    
    return dictOfTwitterUsers

###############################################################################
###############################################################################

def saveTwitterUsers(dictOfTwitterUsers):
    if (os.path.exists("../output/") == False):
        os.mkdir("../output/")
    
    listFile = open(TWITTER_USERS_FROM_LISTS_FILENAME, "w", encoding="utf-8")
    for handle in dictOfTwitterUsers.keys():
        listFile.write(str(dictOfTwitterUsers[handle]) + "\n")
    listFile.close()

    logMessage = "data written to file " + TWITTER_USERS_FROM_LISTS_FILENAME
    return logMessage

###############################################################################
###############################################################################

# The UserLookup.txt file is used to connect each Twitter @handle to its user id number. 
# It also stores the most recent tweet we retrieved for that handle, thus when we retrieve
# again we will start after that last tweet.

def loadUserLookup(listOfMembers, dictOfTwitterUsers):
    userLookupDict = {}
    
    if (os.path.exists(USER_LOOKUP_FILENAME)):
        file = open(USER_LOOKUP_FILENAME, "r", encoding="utf-8")
        lines = file.readlines()
        file.close()
    
        for line in lines:
            user = Classes.TwitterUser()
            user.setData(line)
            user.minimize()
            userLookupDict[user.twitterHandle] = user
        
        # check if there are any new twitter handles that need to be added
        for member in listOfMembers:
            for handle in member.twitter:
                if (handle != "") and (handle not in userLookupDict.keys()):
                    user = Classes.TwitterUser()
                    user.twitterHandle = handle
                    userLookupDict[handle] = user                        
    else:
        # file does not exist, so we need to gather the data
        for member in listOfMembers:
            for handle in member.twitter:
                if handle in dictOfTwitterUsers.keys():
                    user = Classes.TwitterUser()
                    user.twitterHandle = handle
                    user.idStr = dictOfTwitterUsers[handle].idStr
                    userLookupDict[handle] = user
                else:
                    if (handle != ""):
                        user = Classes.TwitterUser()
                        user.twitterHandle = handle
                        userLookupDict[handle] = user
            
    return userLookupDict

###############################################################################
###############################################################################

def saveUserLookup(userLookupDict):
    file = open(USER_LOOKUP_FILENAME, "w", encoding="utf-8")
    for handle in userLookupDict.keys():
        file.write(str(userLookupDict[handle]) + "\n")
    file.close()
    
    logMessage = "data written to file " + USER_LOOKUP_FILENAME
    return logMessage

###############################################################################
###############################################################################

def getPastTimeString(daysAgo=1):
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = datetime.timedelta(days=-daysAgo)
    result = now + delta
    resultStr = result.isoformat(sep='T', timespec='seconds')
    resultStr = resultStr.split("+")[0] + "Z"
    return resultStr

###############################################################################
###############################################################################

def getLocalTime():
    local = time.localtime()
    resultStr = time.strftime("%a, %d %b %Y %H:%M:%S", local)
    return resultStr

###############################################################################
###############################################################################

def getCurrentDate():
    now = datetime.datetime.now()
    resultStr = now.strftime("%Y-%m-%d-%a")
    return resultStr

###############################################################################
###############################################################################

def convertDateToReadable(date):
    dateObj = datetime.datetime.strptime(date, "%Y-%m-%d-%a")
    resultStr = dateObj.strftime("%a %B %d, %Y")
    return resultStr

###############################################################################
###############################################################################

def convertYearMonthToReadable(yearMonth):
    dateObj = datetime.datetime.strptime(yearMonth, "%Y-%m")
    resultStr = dateObj.strftime("%B %Y")
    return resultStr

###############################################################################
###############################################################################

def getWashingtonTime():
    # TODO: update Python and use the new timezone functionality
    now = datetime.datetime.now()
    delta = datetime.timedelta(hours=1)
    result = now + delta
    resultStr = result.strftime("%a %B %d, %Y at %I:%M %p Washington DC time.")
    return resultStr

###############################################################################
###############################################################################

def getCurrentHour():
    now = datetime.datetime.now()
    return now.hour

###############################################################################
###############################################################################

def saveTweets(listOfTweets, scanDate):
    RESULTS_FOLDER = "../output/" + scanDate
    if (os.path.exists(RESULTS_FOLDER) == False):
        os.mkdir(RESULTS_FOLDER)

    nextNumber = 0
    files = os.listdir(RESULTS_FOLDER)
    for fileName in files:
        if ("Tweets" in fileName):
            number = fileName.split("Tweets")[1].split(".")[0]
            number = int(number)
            if (number > nextNumber):
                nextNumber = number
    nextNumber += 1
    
    TWEETS_FILENAME = RESULTS_FOLDER + "/Tweets" + str(nextNumber) + ".txt"
    
    file = open(TWEETS_FILENAME, "w", encoding="utf-8")
    for tweet in listOfTweets:
        file.write(str(tweet) + "\n")
    file.close()
    
    logMessage = "data written to file " + TWEETS_FILENAME
    return logMessage

###############################################################################
###############################################################################

def getMostRecentResultsFolder():
    OUTPUT_FOLDER = "../output/"
    filesAndFolders = os.listdir(OUTPUT_FOLDER)
    filesAndFolders.sort(reverse=True)
    for item in filesAndFolders:
        if (item == "logs") or (item == "test"):
            continue
        
        p = pathlib.Path(OUTPUT_FOLDER + item)
        if p.is_dir():
            RESULTS_FOLDER = OUTPUT_FOLDER + item + "/"
            return RESULTS_FOLDER

###############################################################################
###############################################################################

def loadTweets(path):
    allFileNames = os.listdir(path)
    allFileNames.sort()
    
    tweetFileNames = []
    for fileName in allFileNames:
        if ("Tweets" in fileName) and (".txt" in fileName):
            tweetFileNames.append(path + fileName)
    
    listOfAllTweets = []
    for fileName in tweetFileNames:
        fileLines = open(fileName, "r", encoding="utf-8").readlines()
        for line in fileLines:
            listOfAllTweets.append(line.strip())

    return listOfAllTweets

###############################################################################
###############################################################################

def saveURLs(dictOfURLs, scanDate):
    RESULTS_FOLDER = "../output/" + scanDate
    if (os.path.exists(RESULTS_FOLDER) == False):
        os.mkdir(RESULTS_FOLDER)

    URLS_FILENAME = RESULTS_FOLDER + "/URLs.txt"

    # we are appending to the file because we could retrieve tweets more than once
    file = open(URLS_FILENAME, "a", encoding="utf-8")
    for shortened_url in dictOfURLs.keys():
        url_obj = dictOfURLs[shortened_url]
        file.write(str(url_obj) + "\n")
    file.close()

    logMessage = "Data written to file " + URLS_FILENAME
    return logMessage

###############################################################################
###############################################################################

def loadURLs(path):
    dictOfURLs = {}

    fileLines = open(path + "URLs.txt", "r", encoding="utf-8").readlines()
    for line in fileLines:
        url_obj = Classes.URL()
        url_obj.setData(line.strip())
        key = url_obj.shortened_url
        dictOfURLs[key] = url_obj

    return dictOfURLs

###############################################################################
###############################################################################

def getKeywords():
    dictOfKeywords = {}
    
    # each word will start with 0 or 1 special characters [+_^~]
    # then have 1 or more non-special characters
    regex = re.compile(r"[+_^~]?[^+_^~]+")
    
    fileLines = open(KEYWORDS_FILE_NAME, "r", encoding="utf-8").readlines()
    
    currentCategory = ""
    for line in fileLines:
        lineStripped = line.strip()
        
        # we don't pay attention until we see the first category
        if ("Category=" in lineStripped):
            currentCategory = lineStripped.split("=")[1]
            dictOfKeywords[currentCategory] = []
        elif (len(currentCategory) > 0) and (len(lineStripped) > 0):
            if ("Keywords=" in lineStripped):
                lineStripped = lineStripped.split("=")[1]
            
            listOfWords = regex.findall(lineStripped)
            
            for i in range(0, len(listOfWords)):
                if (listOfWords[i][0] != '^'):
                    listOfWords[i] = listOfWords[i].lower()
                if (listOfWords[i][0] == '+'):
                    listOfWords[i] = listOfWords[i][1:]
                # make all single quotes standard, sometimes the funny single quotes appear
                if ("’" in listOfWords[i]) or ("ʻ" in listOfWords[i]):
                    regexQuote = re.compile(r"[’ʻ]")
                    listOfWords[i] = regexQuote.sub("'", listOfWords[i])
                
            dictOfKeywords[currentCategory].append(listOfWords)
            
    return dictOfKeywords

###############################################################################
###############################################################################

def getHTMLTemplate():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("../config/"))
    htmlTemplate = env.get_template(TEMPLATE_HTML_FILE_NAME)
    return htmlTemplate

###############################################################################
###############################################################################

def getHTMLTemplateIndexResults():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader("../config/"))
    htmlTemplate = env.get_template(TEMPLATE_INDEX_RESULTS_FILE_NAME)
    return htmlTemplate

###############################################################################
###############################################################################

def saveHTMLResults(folder, filename, html):
    OUTPUT_FILE_NAME = folder + filename
    outputFile = open(OUTPUT_FILE_NAME, "w", encoding="utf-8")
    outputFile.write(html)
    outputFile.close()
    
    logMessage = "data written to file " + OUTPUT_FILE_NAME
    return logMessage, OUTPUT_FILE_NAME

###############################################################################
###############################################################################

# TODO: remove this
def unshortenURL(url):
    # This is when testing new keywords and we don't want to wait
    if (BYPASS_URL_UNSHORTENER == True):
        return url, ""

    time.sleep(1)  # be nice to Twitter

    # Visit Twitter's shortened url, grab the html data, and look for the redirect url.
    redirectURL = getRedirectURL(url)
    if (redirectURL == ""):
        message = "Warning: could not find a redirect URL for " + url
        return "", message

    # Clean up some of the links. Example:
    # https://www.google.com/amp/s/www.cbsnews.com/amp/news/child-tax-credit-november-2021-fifth-check-deposit/
    if ("/www.google.com/amp/s/" in redirectURL):
        redirectURL = redirectURL.replace("www.google.com/amp/s/", "")

    return redirectURL, ""

###############################################################################
###############################################################################

# TODO: remove this
def getRedirectURL(url):
    html = getWebsiteHTML(url)

    if ("URL=" in html):
        redirectURL = html.split("URL=")[1]
        redirectURL = redirectURL.split('"')[0]
        return redirectURL
    else:
        return ""

###############################################################################
###############################################################################

def getDomainOfURL(url):
    if (url == ""):
        return ""
    else:
        domain = urlparse(url).netloc
        return domain

###############################################################################
###############################################################################

# helper function for retrieving all HTML data from a website

def getWebsiteHTML(url):
    if (url == ""):
        return ""

    # for retries in range(0, 3):
    #     try:
    #         # some websites don't like Python scripts scraping their data, so use a custom
    #         # header which makes us look like an innocent web browser
    #         req = urllib.request.Request(url, headers=getCustomHeader())
    #         conn = urllib.request.urlopen(req, timeout=3)
    #         data = conn.read()
    #         conn.close()
    #         decodedData = data.decode('utf-8')
    #         return decodedData
    #     except:
    #         if (retries <= 1):
    #             time.sleep(1)

    for retries in range(0, 3):
        try:
            # some websites don't work with urlopen, so we'll try the requests library
            result = requests.get(url, headers=getCustomHeader(), timeout=3)
            decodedData = result.text
            result.close()
            return decodedData
        except:
            if (retries <= 1):
                time.sleep(1)

    return ""

###############################################################################
###############################################################################

class Logger:
    def __init__(self):
        self.filename = ""
        self.messages = []
        
    def prepareLogFile(self, logFolder=DEFAULT_LOG_FOLDER):
        # before starting a new log file, check if we still need to write any messages to the prev log
        if (self.filename != "") and (len(self.messages) > 0):
            self.flushLogs()

        # put it in a subfolder year-month
        yearMonth = getCurrentDate()[:7]
        logFolder = logFolder + yearMonth + "/"
        if (os.path.exists(logFolder) == False):
            os.mkdir(logFolder)

        self.filename = logFolder + getCurrentDate() + "-log.txt"
        
    def log(self, text):
        print(text)
        
        if (self.filename == ""):
            return
        
        self.messages.append(text)
        if (len(self.messages) > 20):
            self.flushLogs()
        
    def flushLogs(self):
        for retries in range(0, 3):
            try:
                f = open(self.filename, "a", encoding="utf-8")
                for message in self.messages:
                    f.write(message + "\n")
                f.close()
                self.messages = []
                return
            except BaseException as e:
                strError = str(e.args)
                print("Error: problem flushing logs, someone might have the log file open")
                print(strError)
                time.sleep(10)
        
    def isErrorInLog(self):
        self.flushLogs()
        f = open(self.filename, "r", encoding="utf-8")
        data = f.read()
        f.close()
        if ("Error:" in data):
            return True
        else:
            return False
        
        
import platform
import os
import subprocess
import os.path
import pathlib
import datetime
import re
import jinja2
import requests
import brotlicffi
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
from typing import Tuple
from multiprocessing import Queue

import Classes

CONFIG_FILE_NAME = "../config/Config.txt"
CREDENTIALS_FILE_NAME = "../config/Credentials.txt"
CUSTOMIZED_TWITTER_HANDLES_FILE_NAME = "../config/CustomizedTwitterHandles.txt"
LIST_OF_CONGRESS_MEMBERS_FILENAME = "../output/ListOfCongressMembers.txt"
TWITTER_USERS_FROM_LISTS_FILENAME = "../output/TwitterUsersFromTwitterLists.txt"
TWITTER_LOOKUP_FILENAME = "../output/TwitterLookup.txt"
DEFAULT_LOG_FOLDER = "../output/logs/"
KEYWORDS_FILE_NAME = "../config/Keywords.txt"
TEMPLATE_HTML_FILE_NAME = "template.html"
TEMPLATE_INDEX_RESULTS_FILE_NAME = "template-index-of-results.html"

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
    "Accept-Encoding":"gzip, deflate, br",
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
    "Accept-Encoding":"gzip, deflate, br",
    "Accept-Language":"en-US,en;q=0.9",
    "Sec-Fetch-User":"?1",
    "Upgrade-Insecure-Requests":"1"
}

CUSTOM_HTTP_HEADER_IPHONE = {
    "User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding":"gzip, deflate, br",
    "Accept-Language":"en-US,en;q=0.9",
    "Referer":"https://www.google.com/"
}

CUSTOM_HTTP_HEADER_ANDROID = [
    # the first header (authority) will be customized for each request
    '-H', 'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="98", "Google Chrome";v="98"',
    '-H', 'sec-ch-ua-mobile: ?1',
    '-H', 'sec-ch-ua-platform: "Android"',
    '-H', 'upgrade-insecure-requests: 1',
    '-H', 'user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.82 Mobile Safari/537.36',
    '-H', 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    '-H', 'sec-fetch-site: none',
    '-H', 'sec-fetch-mode: navigate',
    '-H', 'sec-fetch-user: ?1',
    '-H', 'sec-fetch-dest: document',
    '-H', 'accept-language: en-US,en;q=0.9'

]

###############################################################################
###############################################################################

def getCustomHeader(currentPlatform = True):
    if (currentPlatform):
        if ("Windows-10" in platform.platform()):
            return CUSTOM_HTTP_HEADER_WIN10
        else:
            return CUSTOM_HTTP_HEADER_WIN7
    else:
        return CUSTOM_HTTP_HEADER_IPHONE

###############################################################################
###############################################################################

def getCustomHeaderForCurl(url: str):
    headerList = CUSTOM_HTTP_HEADER_ANDROID.copy()
    
    try:
        domain = urlparse(url).netloc
    except:
        return headerList

    # the format is -H 'authority: m.jpost.com'
    frontList = ["-H", "authority: " + domain]

    return frontList + headerList

###############################################################################
###############################################################################

def loadCredentials():
    cred = Classes.Credentials()
    credLines = open(CREDENTIALS_FILE_NAME, "r").readlines()
    for line in credLines:
        cred.setData(line)
    
    return cred

###############################################################################
###############################################################################

def loadConfig():
    config = Classes.Config()
    configLines = open(CONFIG_FILE_NAME, "r").readlines()
    for line in configLines:
        config.setData(line)
    
    return config

###############################################################################
###############################################################################

def getCustomizedTwitterHandles():
    listOfExcludes = []
    listOfIncludes = []
    listOfSamePersons = []
    
    lines = open(CUSTOMIZED_TWITTER_HANDLES_FILE_NAME, "r").readlines()
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

# The TwitterLookup.txt file is used to connect each Twitter @handle to its user id number. 
# It also stores the most recent tweet we retrieved for that handle, thus when we retrieve
# again we will start after that last tweet.

def loadTwitterLookup(listOfMembers, dictOfTwitterUsers):
    userLookupDict = {}
    
    if (os.path.exists(TWITTER_LOOKUP_FILENAME)):
        file = open(TWITTER_LOOKUP_FILENAME, "r", encoding="utf-8")
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

def saveTwitterLookup(userLookupDict):
    file = open(TWITTER_LOOKUP_FILENAME, "w", encoding="utf-8")
    for handle in userLookupDict.keys():
        file.write(str(userLookupDict[handle]) + "\n")
    file.close()
    
    logMessage = "data written to file " + TWITTER_LOOKUP_FILENAME
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

# udate is the number of milliseconds since the epoch in utc timezone
def convertUdateToReadable(udate: int):
    result = datetime.datetime.fromtimestamp(udate / 1000, datetime.timezone.utc)
    result = result.astimezone()
    date = result.strftime("%m/%d/%Y")
    return date

###############################################################################
###############################################################################

def daysSinceUdate(udate: int):
    then = datetime.datetime.fromtimestamp(udate / 1000, datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - then
    # Not counting partial days. It's just needed as a rough estimate.
    return diff.days

###############################################################################
###############################################################################

def getWashingtonTime():
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
    
    TWEETS_FILENAME = RESULTS_FOLDER + "/Tweets.txt"
    
    file = open(TWEETS_FILENAME, "a", encoding="utf-8")
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

def saveURLs(dictOfURLs, scanDate, socialMedia = "Twitter", append=True):
    RESULTS_FOLDER = "../output/" + scanDate
    if (os.path.exists(RESULTS_FOLDER) == False):
        os.mkdir(RESULTS_FOLDER)

    URLS_FILENAME = RESULTS_FOLDER + "/" + socialMedia + "URLs.txt"

    if (append):
        mode = "a"
    else:
        mode = "w"
    
    file = open(URLS_FILENAME, mode, encoding="utf-8")
    for shortened_url in dictOfURLs.keys():
        url_obj = dictOfURLs[shortened_url]
        file.write(str(url_obj) + "\n")
    file.close()

    logMessage = "Data written to file " + URLS_FILENAME
    return logMessage

###############################################################################
###############################################################################

def loadURLs(path, socialMedia = "Twitter"):
    dictOfURLs = {}

    fileName = socialMedia + "URLs.txt"
    fileLines = open(path + fileName, "r", encoding="utf-8").readlines()
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
    
    # each word will start with 0 or 1 special characters [+{^~]
    # then have 1 or more non-special characters. We need to escape the { with a \
    regex = re.compile(r"[+\{^~]?[^+\{^~]+")
    
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

def getDomainOfURL(url):
    if (url == ""):
        return ""

    try:
        domain = urlparse(url).netloc
    except:
        return ""

    if (domain.startswith("www.")):
        domain = domain[4:]

    return domain

###############################################################################
###############################################################################

# helper function for retrieving all HTML data from a website

def getWebsiteData(url, currentPlatformHeaders = True) -> Tuple[str,bytes,int]:
    if (url == ""):
        return "", bytes(), 0

    for retries in range(0, 3):
        try:
            text_data = ""
            binary_data = bytes()
            status_code = 1001
            
            custom_header = getCustomHeader(currentPlatformHeaders)
            result = requests.get(url, headers=custom_header, timeout=3, stream=True)
            status_code = result.status_code
            result.raise_for_status() # if an HTTP error occurred, it will raise an exception
            encoding = result.headers.get("Content-Encoding", "")
            content_type = result.headers.get("Content-Type", "")

            start = time.time()
            for chunk in result.iter_content(4096, decode_unicode=False):
                if isinstance(chunk, str):
                    text_data += chunk
                elif isinstance(chunk, bytes):
                    binary_data += chunk

                if (time.time() - start) > 60: # if it's taking more than 60 seconds, don't wait any longer
                    result.close()
                    raise ValueError("timeout reached")
            
            result.close()

            # Check if we need to decode anything.
            if ("br" in encoding) and (len(binary_data) > 0):
                if (b"html" in binary_data):
                    try:
                        text_data = binary_data.decode()
                        binary_data = bytes()
                    except ValueError:
                        text_data = brotlicffi.decompress(binary_data).decode()
                        binary_data = bytes()
                else:
                    text_data = brotlicffi.decompress(binary_data).decode()
                    binary_data = bytes()
            elif ("html" in content_type.lower()) and (len(binary_data) > 0):
                try:
                    text_data = binary_data.decode()
                    binary_data = bytes()
                except:
                    # We may have to specify the charset, so let's find it.
                    # Format is "Content-Type: text/html; charset=iso-8859-1"
                    if ("charset" in content_type.lower()):
                        pattern = re.compile(r"charset\s*=\s*(.+)", re.IGNORECASE)
                        charset = pattern.findall(content_type)[0]
                        text_data = binary_data.decode(encoding=charset)
                        binary_data = bytes()

            return text_data, binary_data, status_code
        except ValueError:
            # This occurs on a specific timeout: reading the chunked data.
            return text_data, binary_data, status_code
        except:
            # If it's a 403 or 404 then don't keep bugging the server, just move on.
            if (status_code // 100 == 4):
                return text_data, binary_data, status_code

            # This could occur if the website took too long to respond to the initial request. Try again.
            if (retries <= 1):
                time.sleep(1)

    return "", bytes(), 1000

###############################################################################
###############################################################################

def getWebsiteFromGoogleCache(url, currentPlatformHeaders = True):
    return getWebsiteData("https://webcache.googleusercontent.com/search?q=cache:" + url, currentPlatformHeaders)

###############################################################################
###############################################################################

def runCurlCommand(url) -> Tuple[str,bytes,int]:
    headerList = getCustomHeaderForCurl(url)

    # TODO: "~/custom_curl/bin/curl"
    fullCmd = ["curl", url]
    fullCmd += headerList
    fullCmd.append("--compressed")
    fullCmd.append("--verbose")

    result = subprocess.run(fullCmd, capture_output=True)
    if (result.returncode != 0):
        return "", bytes(), 1011

    output = result.stderr.decode() + result.stdout.decode()
    lines = [line for line in output.split("\n") if line.strip() != ""]

    text = ""
    status_code = 1010
    resp_started = False

    for line in lines:
        if ("> accept-language: " in line):
            resp_started = True

        if resp_started:
            if ("< HTTP/2 " in line):
                line_split = line.strip().split(' ')
                status_code = int(line_split[-1])
            elif ("< location: " in line) and (status_code // 100 == 3):
                line_split = line.strip().split(' ')
                text = line_split[-1]
                break
            else:
                text += line

    return text, bytes(), status_code

###############################################################################
###############################################################################

def getWebsiteUsingCurl(url: str) -> Tuple[str,bytes,int]:
    # sanitize the inputs
    if (" " in url) or (".." in url):
        return "", bytes(), 0

    # TODO: add try/except

    html, binary_data, status_code = runCurlCommand(url)

    if (status_code // 100 == 3) and (len(html) > 0):
        html, binary_data, status_code = runCurlCommand(html)

    return html, binary_data, status_code

###############################################################################
###############################################################################

def extractTitleFromHTML(html):
    if (html == ""):
        return ""

    try:
        parsed_html = BeautifulSoup(html, 'html.parser')
    except:
        return ""

    if (parsed_html.title is not None) and (parsed_html.title.string is not None):
            title = parsed_html.title.string
            title = title.strip()
            title = title.replace("\n", "")
            title = title.replace("\r", "")
            return title
    
    return ""

###############################################################################
###############################################################################

def integerToBase36(number: int):
    alphabet="0123456789abcdefghijklmnopqrstuvwxyz"

    if (number < len(alphabet)):
        return alphabet[number]

    base36 = ""
    while number != 0:
        number, remainder = divmod(number, len(alphabet)) # gives (x//y, x%y)
        base36 = alphabet[remainder] + base36

    return base36

###############################################################################
###############################################################################

def base36ToInteger(number: str):
    return int(number, 36)

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
        
###############################################################################
###############################################################################

class RemoteLogger:
    def __init__(self, msgq: Queue):
        self.msgq = msgq

    def log(self, text):
        self.msgq.put(text)

###############################################################################
###############################################################################

def gitPull(logger):
    logger.log("Updating local git repository...")
    result = subprocess.run(["git", "pull"], capture_output=True)
    output = result.stdout.decode() + result.stderr.decode()
    lines = [line for line in output.split("\n") if line.strip() != ""]
    for line in lines:
        logger.log(line)
    if (result.returncode == 0):
        logger.log("Successfully pulled latest git repo")
        return True
    else:
        logger.log("Warning: failed to pull latest git repo")
        return False

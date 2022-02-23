import os
import tweepy
import urllib.request
import time

import Classes
import Utilities

stateDict = {"AL":"Alabama", "AK":"Alaska", "AZ":"Arizona", "AR":"Arkansas", "CA":"California",
             "CO":"Colorado", "CT":"Connecticut", "DE":"Delaware", "FL":"Florida", "GA":"Georgia", 
             "HI":"Hawaii", "ID":"Idaho", "IL":"Illinois", "IN":"Indiana", "IA":"Iowa", "KS":"Kansas",
             "KY":"Kentucky", "LA":"Louisiana", "ME":"Maine", "MD":"Maryland", "MA":"Massachusetts",
             "MI":"Michigan", "MN":"Minnesota", "MS":"Mississippi", "MO":"Missouri", "MT":"Montana",
             "NE":"Nebraska", "NV":"Nevada", "NH":"New Hampshire", "NJ":"New Jersey", "NM":"New Mexico",
             "NY":"New York", "NC":"North Carolina", "ND":"North Dakota", "OH":"Ohio", "OK":"Oklahoma",
             "OR":"Oregon", "PA":"Pennsylvania", "RI":"Rhode Island", "SC":"South Carolina", 
             "SD":"South Dakota", "TN":"Tennessee", "TX":"Texas", "UT":"Utah", "VT":"Vermont",
             "VA":"Virginia", "WA":"Washington", "WV":"West Virginia", "WI":"Wisconsin", "WY":"Wyoming",
             "PR":"Puerto Rico Resident Commissioner", "DC":"District of Columbia Delegate",
             "VI":"Virgin Islands Delegate", "AS":"American Samoa Delegate", 
             "MP":"Mariana Islands Delegate", "GU":"Guam Delegate"}

partyDict = {"Democrat":"D", "Republican":"R", "Independent":"I"}

commonNicknameDict = {"Tom":"Thomas", "Chris":"Christopher", "Dick":"Richard", 
                      "Rob":"Robert", "Bob":"Robert", "Ben":"Benjamin", "Dan":"Daniel",
                      "Don":"Donald", "Greg":"Gregory", "Mike":"Michael", "Jerry":"Jerrold",
                      "Jim":"James", "Dave":"David", "Matt":"Matthew", "Lou":"Luis", "Jeff":"Jefferson"}

###############################################################################
###############################################################################

class CreateListOfCongressMembers:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################
    
    def findLegislatorsFile(self):
        legislatorsFilePath = ""
        dateOfOurData = ""
        files = os.listdir("../output/")
        for fileName in files:
            if ("legislators-current" in fileName) and (".csv" in fileName):
                legislatorsFilePath = "../output/" + fileName
                dateOfOurData = fileName.rsplit("-", 1)[1] # ex: legislators-current-Aug 2, 2021.csv
                dateOfOurData = dateOfOurData.split(".")[0]
        
        return legislatorsFilePath,dateOfOurData
    
    ###########################################################################
    ###########################################################################

    def downloadCongressMemberData(self):
        # First see what data we already have.
        legislatorsFilePath,dateOfOurData = self.findLegislatorsFile()

        if (legislatorsFilePath == ""):
            self.logger.log("No .csv file of legislators found")
        else:
            self.logger.log("Detected .csv file of legislators: " + legislatorsFilePath)
            self.logger.log("The date of our .csv file is: " + dateOfOurData)

        # Now let's see when the legislator data on GitHub was last updated.
        dateOfLatestData = ""
        commitHistoryURL = "https://github.com/unitedstates/congress-legislators/commits/gh-pages/legislators-current.csv"
        html, binary_data, respcode = Utilities.getWebsiteData(commitHistoryURL)
        lines = html.split("\n")
        for line in lines:
            if ("Commits on " in line):
                dateOfLatestData = line.split("Commits on ")[1] # ex: "Commits on Aug 2, 2021"
                dateOfLatestData = dateOfLatestData.split("<")[0].strip()
                break # We only want the most recent commit

        if (dateOfLatestData == ""):
            self.logger.log("Warning: could not determine date of .csv data on GitHub")
        else:
            self.logger.log("The latest .csv data available from GitHub is dated: " + dateOfLatestData)

        # Check to see if we should download the data or keep what we already have.
        if (dateOfOurData == dateOfLatestData):
            self.logger.log("Keeping our .csv file of lesislators")
            return
        else:
            newPath = "../output/legislators-current-" + dateOfLatestData + ".csv"
            self.logger.log("Retrieving the latest .csv file of legislators")
            urllib.request.urlretrieve("https://raw.githubusercontent.com/unitedstates/congress-legislators/gh-pages/legislators-current.csv", 
                                       newPath)
            self.logger.log("Latest file of legislators saved to " + newPath)
            
            # If we got this far then the download was successful (no exceptions thrown), so now it is safe
            # to delete the old .csv file if there was one.
            if (legislatorsFilePath != ""):
                self.logger.log("Removing " + legislatorsFilePath)
                os.remove(legislatorsFilePath)
            
            return

    ###########################################################################
    ###########################################################################

    # Retrieve each member's website, last name, first name, state, party, and 
    # official Twitter account from the .csv file we downloaded. The house is 
    # either rep or sen (representative or senator).
    def getMembers(self, house):
        members = []
        
        legislatorsFilePath,dateOfOurData = self.findLegislatorsFile()
        file = open(legislatorsFilePath, "r", encoding="utf-8")
        lines = file.readlines()
        file.close()
        
        header = lines[0].split(",")
        LAST_NAME_INDEX = header.index("last_name")
        FIRST_NAME_INDEX = header.index("first_name")
        MIDDLE_NAME_INDEX = header.index("middle_name")
        SUFFIX_INDEX = header.index("suffix")
        NICKNAME_INDEX = header.index("nickname")
        FULL_NAME_INDEX = header.index("full_name")
        HOUSE_INDEX = header.index("type")
        STATE_INDEX = header.index("state")
        DISTRICT_INDEX = header.index("district")
        PARTY_INDEX = header.index("party")
        URL_INDEX = header.index("url")
        TWITTER_INDEX = header.index("twitter")
        
        for i in range(1, len(lines)):
            # Remove commas within double quotes, remove the quotes as well. We won't lose
            # any important information and this will allow us to split the line by commas
            # and still maintain the correct number of columns.
            line_list = list(lines[i])
            foundLeftQuotes = False
            for j in range(0, len(line_list)):
                if (foundLeftQuotes == False) and (line_list[j] == '"'):
                    foundLeftQuotes = True
                    line_list[j] = ''
                
                if (foundLeftQuotes == True) and (line_list[j] == ','):
                    line_list[j] = ''
                
                if (foundLeftQuotes == True) and (line_list[j] == '"'):
                    foundLeftQuotes = False
                    line_list[j] = ''
                
                # handle funny single quotes
                if (line_list[j] == "’") or (line_list[j] == "ʻ"):
                    line_list[j] = "'"
                    
            
            line_string = "".join(line_list)
            line_split = line_string.split(",")
            
            if (line_split[HOUSE_INDEX].lower() != house):
                continue
            
            member = Classes.CongressMember()
            member.last_name = line_split[LAST_NAME_INDEX]
            member.first_name = line_split[FIRST_NAME_INDEX]
            member.middle_name = line_split[MIDDLE_NAME_INDEX]
            member.suffix = line_split[SUFFIX_INDEX]
            member.nickname = line_split[NICKNAME_INDEX]
            member.full_name = line_split[FULL_NAME_INDEX]
            member.house = line_split[HOUSE_INDEX]
            member.state = line_split[STATE_INDEX]
            member.district = line_split[DISTRICT_INDEX]
            party = line_split[PARTY_INDEX]
            member.party = partyDict[party]
            member.url = line_split[URL_INDEX]
            handle = line_split[TWITTER_INDEX].lower().strip()
            if (handle == ""):
                member.twitter = []
            else:
                member.twitter = [handle]
            
            members.append(member)
        
        members.sort()
        return members

    ###########################################################################
    ###########################################################################
    
    # helper function for checking if a handle is already in a list of CongressMember objects
    def isHandleInList(self, handle, listOfCongressMembers):
        for member in listOfCongressMembers:
            for hnd in member.twitter:
                if (handle.lower() == hnd.lower()):
                    return True
        return False

    ###########################################################################
    ###########################################################################

    # helper function for trying to match a twitter user to a known member of Congress
    def isMatch(self, user, member):
        
        # check if full name matches
        if (member.full_name != ""):
            if (member.full_name.lower() in user.name.lower()):
                return True
            # check if full name matches without the .
            if (member.full_name.lower().replace(".", "") in user.name.lower().replace(".", "")):
                return True
        
        # use first name + last name, use first name + middle name + last name
        if (member.first_name != "") and (member.last_name != ""):
            combined_name = member.first_name + " " + member.last_name
            if (combined_name.lower() in user.name.lower()):
                return True
            if (combined_name.lower() in user.description.lower()):
                return True
            combined_name = member.first_name + " " + member.middle_name + " " + member.last_name
            if (combined_name.lower() in user.name.lower()):
                return True
            combined_name_no_space = member.first_name + member.last_name
            if (combined_name_no_space.lower() in user.twitterHandle.lower()):
                stateName = stateDict[member.state]
                if (member.state in user.name) or (member.state in user.description) or (stateName in user.description):
                    return True
            
        # Try nickname from the .csv file we downloaded.
        # use nickname + middle name + last name, use nickname + last name
        if (member.nickname != "") and (member.last_name != ""):
            combined_name = member.nickname + " " + member.middle_name + " " + member.last_name
            if (combined_name.lower() in user.name.lower()):
                return True
            combined_name = member.nickname + " " + member.last_name
            if (combined_name.lower() in user.name.lower()):
                return True
            if (combined_name.lower() in user.description.lower()):
                return True
        
        # try common nicknames from OUR dictionary
        for nickname in commonNicknameDict.keys():
            if (nickname in user.name):
                if (commonNicknameDict[nickname] in member.first_name) or (commonNicknameDict[nickname] in member.full_name):
                    combined_name = nickname + " " + member.last_name
                    if (combined_name.lower() in user.name.lower()):
                        return True
                    if (combined_name.lower() in user.description.lower()):
                        return True
            birthName = commonNicknameDict[nickname]
            if (birthName in member.first_name):
                combined_name = nickname + " " + member.last_name
                if (combined_name.lower() in user.description.lower()) and (member.state.lower() in user.description.lower()):
                    return True
                combined_name = nickname + member.last_name + member.state
                if (combined_name.lower() in user.twitterHandle.lower()):
                    return True
        
        # try middle name + last name
        if (len(member.middle_name) > 2) and (member.last_name != ""):
            combined_name = member.middle_name + " " + member.last_name
            if (combined_name.lower() in user.name.lower()):
                return True
        
        # try last name + state + district
        if (member.last_name != "") and (member.district != ""):
            stateAndDistrict = member.state + format(int(member.district), "02d")
            if (member.last_name.lower() in user.name.lower()) and (stateAndDistrict.lower() in user.description.lower()):
                return True
            stateHyphenDistrict = member.state + "-" + format(int(member.district), "02d")
            if (member.last_name.lower() in user.name.lower()) and (stateHyphenDistrict.lower() in user.description.lower()):
                return True
        
        # check if one of the Congress member's known Twitter handles is in the Twitter user's bio
        for handle in member.twitter:
            if (handle.strip() == ""):
                continue
            fullHandle = "@" + handle
            if (fullHandle.lower() in user.description.lower()):
                return True
        
        if (member.house == "sen") and (member.last_name != ""):
            if ("press" in user.name.lower()) or ("office" in user.name.lower()): 
                if (member.last_name.lower() in user.name.lower()):
                    return True
    
        return False

    ###########################################################################
    ###########################################################################
    
    # The CustomizedTwitterHandles.txt file can be used to manually tell the 
    # software which official Twitter account and which personal Twitter account
    # actually represent the same person.
    def tryToManuallyAdd(self, unmatchedUser, listOfSamePersons, listOfMembers):
        unknownHandle = unmatchedUser.twitterHandle

        for person in listOfSamePersons:
            knownHandle = ""
            if (unknownHandle == person[0]):
                knownHandle = person[1]
            elif (unknownHandle == person[1]):
                knownHandle = person[0]
            
            if (knownHandle != ""):
                for member in listOfMembers:
                    if (knownHandle in member.twitter) and (unknownHandle not in member.twitter):
                        member.twitter.append(unknownHandle)
                        return True
                return False
        
        return False

    ###########################################################################
    ###########################################################################

    # Personal Twitter accounts will be matched with the appropriate member of Congress.
    def addPersonalAccounts(self, listOfMembers, dictOfTwitterUsers):
        unmatchedTwitterUsers = []
            
        for handle in dictOfTwitterUsers.keys():
            potentialMatches = []
            user = dictOfTwitterUsers[handle]
            inList = self.isHandleInList(user.twitterHandle, listOfMembers)
            if (inList == False):
                matchFound = False
                for member in listOfMembers:
                    matchFound = self.isMatch(user, member)
                    if (matchFound == True):
                        potentialMatches.append(member)
                if (len(potentialMatches) == 1):
                    potentialMatches[0].twitter.append(handle)
                elif (len(potentialMatches) == 0):
                    unmatchedTwitterUsers.append(user)
                else:
                    self.logger.log("Warning: found too many matches: " + str(len(potentialMatches)) + " for " + handle)
                    unmatchedTwitterUsers.append(user)
                    
        
        # Some Twitter handles are manually set because our algorithm isn't smart enough to match them all.
        listOfExcludes,listOfIncludes,listOfSamePersons = Utilities.getCustomizedTwitterHandles()
    
        # for every unmatched Twitter handle, check if we need to manually add it to an existing person, 
        # otherwise add it as a new member at the end of the list
        totalUnmatched = 0
        for unmatchedUser in unmatchedTwitterUsers:
            manuallyAdded = self.tryToManuallyAdd(unmatchedUser, listOfSamePersons, listOfMembers)
            
            if (manuallyAdded == False):
                self.logger.log("no match for @" + unmatchedUser.twitterHandle + ", " + unmatchedUser.name)
                newMember = Classes.CongressMember()
                newMember.last_name = unmatchedUser.name
                newMember.twitter.append(unmatchedUser.twitterHandle)
                listOfMembers.append(newMember)
                totalUnmatched += 1
        if (totalUnmatched > 0):
            self.logger.log("Warning: " + str(totalUnmatched) + " handles were not matched")
        else:
            self.logger.log("All handles were matched")
        
        return listOfMembers

    ###########################################################################
    ###########################################################################

    def lookForMissingTwitterHandles(self, listOfMembers):
        # if any members don't have a Twitter handle, look for one
        for member in listOfMembers:
            if (len(member.twitter) == 0) or ((len(member.twitter) == 1) and (member.twitter[0] == "")):
                self.logger.log("Warning: no Twitter handle for " + member.last_name + ", " + member.first_name)
        
        return

    ###########################################################################
    ###########################################################################
    
    def doMultipleUserLookup(self, handlesToLookup, verbose):
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)
        
        params = ",".join(handlesToLookup)
        response = client.get_users(usernames=params)
        self.logger.log("received response in doMultipleUserLookup")
        
        idStrDict = {}
        for item in response.data:
            if (verbose):
                self.logger.log("received username=" + item.username + ", id=" + str(item.id))
            idStrDict[item.username.lower()] = str(item.id)
        
        time.sleep(1)

        return idStrDict

    ###########################################################################
    ###########################################################################

    # check if a twitter handle has no id string, do user lookup if needed
    def findMissingUserIds(self, twitterLookupDict):
        self.logger.log("Looking for missing user ID numbers")

        handlesToLookup = []
        for handle in twitterLookupDict.keys():
            if (twitterLookupDict[handle].idStr == ""):
                self.logger.log("need idStr for handle " + handle)
                handlesToLookup.append(handle)

        if (len(handlesToLookup) > 0):
            for i in range(0, len(handlesToLookup), 100):
                # grab 0-99, 100-199, etc. because the api can only handle 100 at a time
                batch = handlesToLookup[i:i + 100]
                idStrDict = self.doMultipleUserLookup(batch, True)

                if (len(batch) != len(idStrDict)):
                    self.logger.log("Warning: after user lookup, length of batch: {} does not equal length of idStrDict: {}".format(len(batch), len(idStrDict)))

                for handle in idStrDict.keys():
                    twitterLookupDict[handle].idStr = idStrDict[handle]

    ###########################################################################
    ###########################################################################

    def removeStaleTwitterHandles(self, listOfMembers, twitterLookupDict):
        self.logger.log("Checking for stale Twitter handles")

        # first, we will look through the listOfMembers to see if their Twitter handles are valid according to www.twitter.com
        handlesToLookup = []
        for member in listOfMembers:
            for handle in member.twitter:
                if (handle.strip() != ""):
                    handlesToLookup.append(handle)

        for i in range(0, len(handlesToLookup), 100):
            # grab 0-99, 100-199, etc. because the api can only handle 100 at a time
            batch = handlesToLookup[i:i + 100]
            idStrDict = self.doMultipleUserLookup(batch, False)

            for handle in batch:
                # for each handle that was found, verify the id matches
                if (handle in idStrDict) and (handle in twitterLookupDict):
                    user = twitterLookupDict[handle]
                    if (user.idStr != idStrDict[handle]):
                        self.logger.log("Warning: id for handle {} changed from {} to {}".format(handle, user.idStr, idStrDict[handle]))
                        user.idStr = idStrDict[handle]
                elif (handle not in idStrDict):
                    # the handle was not found
                    self.logger.log("Warning: handle {} is stale, removing it from ListOfCongressMembers.txt and TwitterLookup.txt".format(handle))

                    # remove from listOfMembers
                    for member in listOfMembers:
                        if (handle in member.twitter):
                            member.twitter.remove(handle)

                    # remove from twitterLookupDict
                    if (handle in twitterLookupDict.keys()):
                        twitterLookupDict.pop(handle)

        # second, we will look at all handles in the twitterLookupDict to see if any are not in the listOfMembers,
        # which means they can be removed from the LookupDict
        handlesFromLookupDict = list(twitterLookupDict.keys())
        for handle in handlesFromLookupDict:
            foundHandle = False
            for member in listOfMembers:
                if (handle in member.twitter):
                    foundHandle = True
                    break

            if (not foundHandle):
                twitterLookupDict.pop(handle)
                self.logger.log("warning: handle {} is not connected to a member. Removing it from TwitterLookup.txt".format(handle))

    ###########################################################################
    ###########################################################################

    def addGettrHandles(self, listOfMembers):
        listOfIncludes = Utilities.getCustomizedGettrHandles()
        self.logger.log("Looking for matches for Gettr handles")

        numberMatched = 0
        for handle,url in listOfIncludes:
            for member in listOfMembers:
                if (member.url == url):
                    member.gettr.append(handle)
                    numberMatched += 1
                    self.logger.log("Gettr handle {} matched".format(handle))
                    break

        if (numberMatched != len(listOfIncludes)):
            self.logger.log("Warning: have {} Gettr handles but only {} were matched".format(len(listOfIncludes), numberMatched))

    ###########################################################################
    ###########################################################################

    def run(self):
        
        # Download a .csv file that has a lot of info for each member of Congress.
        try:
            self.downloadCongressMemberData()
        except BaseException as e:
            self.logger.log("Warning: couldn't download congress member data: " + str(e.args))
        
        # Go through the .csv file and get the Reps, then get the Senators
        houseMembers = self.getMembers("rep")
        senateMembers = self.getMembers("sen")
        listOfMembers = houseMembers + senateMembers
        
        # Load the list of Twitter handles that we previously retrieved. These were from
        # the public lists on Twitter.
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        
        # The .csv file already gave us the official Twitter accounts for each member
        # of Congress. Now we have the fun job of trying to figure out which personal 
        # Twitter account goes with which member of Congress. We'll do some various
        # name matching to try and complete the job.
        self.logger.log("Trying to match personal Twitter accounts with their owners in Congress")
        listOfMembers = self.addPersonalAccounts(listOfMembers, dictOfTwitterUsers)
        self.lookForMissingTwitterHandles(listOfMembers)

        # Load (or create) the twitterLookup file which relates a Twitter handle to an ID number
        twitterLookupDict = Utilities.loadTwitterLookup(listOfMembers, dictOfTwitterUsers)

        try:
            self.removeStaleTwitterHandles(listOfMembers, twitterLookupDict)
        except BaseException as e:
            self.logger.log("Warning: failed to remove stale Twitter handles: " + str(e.args))

        try:
            self.findMissingUserIds(twitterLookupDict)
        except BaseException as e:
            self.logger.log("Warning: failed to find missing user ids: " + str(e.args))

        # add the gettr handles
        self.addGettrHandles(listOfMembers)

        logMessage = Utilities.saveTwitterLookup(twitterLookupDict)
        self.logger.log(logMessage)

        logMessage = Utilities.saveCongressMembers(listOfMembers)
        self.logger.log(logMessage)

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = CreateListOfCongressMembers(logger)
    instance.run()
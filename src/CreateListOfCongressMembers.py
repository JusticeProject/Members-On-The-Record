import urllib.request

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
                      "Jim":"James"}

###############################################################################
###############################################################################

class CreateListOfCongressMembers:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################

    def downloadCongressMemberData(self):
        urllib.request.urlretrieve("https://theunitedstates.io/congress-legislators/legislators-current.csv", "../output/legislators-current.csv")
        return

    ###########################################################################
    ###########################################################################

    # Retrieve each member's website, last name, first name, state, and party
    def getMembers(self, house):
        members = []
        
        file = open("../output/legislators-current.csv", "r", encoding="utf-8")
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
            # remove commas within double quotes, remove the quotes as well
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
        if (member.full_name != "") and (member.full_name.lower() in user.name.lower()):
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
        
        # try common nicknames
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

    # merge the data in both of the files
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
        self.logger.log("could not match " + str(totalUnmatched))
        
        return listOfMembers

    ###########################################################################
    ###########################################################################

    def lookForMissingTwitterHandles(self, listOfMembers):
        # if any members don't have a Twitter handle, look for one
        for member in listOfMembers:
            if (len(member.twitter) == 0) or ((len(member.twitter) == 1) and (member.twitter[0] == "")):
                self.logger.log("Warning: no Twitter handle for " + member.last_name + ", " + member.first_name)
    
        # TODO: scrape house.gov and senate.gov?
        
        return

    ###########################################################################
    ###########################################################################

    def run(self):
        try:
            self.downloadCongressMemberData()
        except BaseException as e:
            self.logger.log("Warning: couldn't download congress member data: " + str(e.args))
            
        houseMembers = self.getMembers("rep")
        senateMembers = self.getMembers("sen")
        listOfMembers = houseMembers + senateMembers
        
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        
        listOfMembers = self.addPersonalAccounts(listOfMembers, dictOfTwitterUsers)
        self.lookForMissingTwitterHandles(listOfMembers)
        logMessage = Utilities.saveCongressMembers(listOfMembers)
        self.logger.log(logMessage)

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = CreateListOfCongressMembers(logger)
    instance.run()
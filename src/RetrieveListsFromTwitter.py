import time
import tweepy
import Classes
import Utilities

###############################################################################
###############################################################################

class RetrieveListsFromTwitter():
    def __init__(self, logger):
        self.logger = logger
    
    ###########################################################################
    ###########################################################################
    
    def doMultipleUserLookup(self, handlesToLookup):
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)
    
        names = ",".join(handlesToLookup)
        user_fields_list = ["username",
                            "id",
                            "url",
                            "name",
                            "description"]
        
        response = client.get_users(usernames=names, user_fields=user_fields_list)
        self.logger.log("received response for user lookup")
        
        listOfUsers = []
        for item in response.data:
            handle = item.username
            idStr = str(item.id)
            website = item.url
            fullName = item.name
            bio = item.description
            
            user = Classes.TwitterUser(handle, idStr, 0, website, fullName, bio)
            listOfUsers.append(user)
        
        return listOfUsers

    ###########################################################################
    ###########################################################################

    def lookupUserById(self, idStr):
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)
    
        user_fields_list = ["username",
                            "id",
                            "url",
                            "name",
                            "description"]
        
        response = client.get_user(id=idStr, user_fields=user_fields_list)
        self.logger.log("received response for user lookup by id")

        handle = response.data.username
        idStr = str(response.data.id)
        website = response.data.url
        fullName = response.data.name
        bio = response.data.description    
        user = Classes.TwitterUser(handle, idStr, 0, website, fullName, bio)

        return user

    ###########################################################################
    ###########################################################################

    def isHandleInResults(self, handle, listOfResults):
        for user in listOfResults:
            if (handle.lower() == user.twitterHandle.lower()):
                return True

        return False

    ###########################################################################
    ###########################################################################

    def getUpdatedUser(self, handle):
        newUser = None

        # Load yesterday's TwitterUsersFromTwitterLists.txt which hasn't been updated yet for today.
        # Grab the id for the handle so we can look up the id and see if it has a new handle.
        dictOfTwitterUsers = Utilities.loadTwitterUsers()
        if (handle in dictOfTwitterUsers.keys()):
            oldUser = dictOfTwitterUsers[handle]
            try:
                newUser = self.lookupUserById(oldUser.idStr)
            except BaseException as e:
                self.logger.log("Warning: could not lookup up user by id: " + str(e.args))

        return newUser

    ###########################################################################
    ###########################################################################

    def includeCustomizedHandles(self, dictOfTwitterUsers, handlesToLookup):
        listBadTwitterHandleMsgs = []

        for i in range(0, len(handlesToLookup), 100):
            # grab 0-99, 100-199, etc. because the api can only handle 100 at a time
            batch = handlesToLookup[i:i+100]
            results = self.doMultipleUserLookup(batch)
            time.sleep(5)

            if (len(batch) != len(results)):
                for handle in batch:
                    found = self.isHandleInResults(handle, results)
                    if (found == False):
                        time.sleep(5)
                        newUser = self.getUpdatedUser(handle)
                        if (newUser is None):
                            msg = f"Warning: {handle} does not seem to be a valid Twitter handle"
                            self.logger.log(msg)
                            listBadTwitterHandleMsgs.append(msg)
                        else:
                            msg = f"Warning: handle {handle} has changed to {newUser.twitterHandle}"
                            self.logger.log(msg)
                            listBadTwitterHandleMsgs.append(msg)
                            dictOfTwitterUsers[newUser.twitterHandle] = newUser

            for user in results:
                dictOfTwitterUsers[user.twitterHandle] = user
        
        return listBadTwitterHandleMsgs

    ###########################################################################
    ###########################################################################

    def getTwitterUsersFromTwitterLists(self, listIDNumbers):
        user_fields_list = ["username",
                            "id",
                            "url",
                            "name",
                            "description"]

        # using v2 of the Twitter API
        cred = Utilities.loadCredentials()
        client = tweepy.Client(cred.Bearer_Token)

        dictOfTwitterUsers = {}

        for listID in listIDNumbers:
            self.logger.log("retrieving members for list id " + str(listID))
            responses = tweepy.Paginator(client.get_list_members, str(listID), user_fields=user_fields_list)

            users = []

            for response in responses:
                if (response.data is not None):
                    users += response.data
                time.sleep(1) # don't exceed the rate limit

            self.logger.log("retrieved " + str(len(users)) + " users")
            
            for user in users:
                handle = user.username.lower()
                idStr = str(user.id)
                website = user.url
                fullName = user.name
                bio = user.description
                
                data = Classes.TwitterUser(handle, idStr, 0, website, fullName, bio)
                dictOfTwitterUsers[handle] = data

        return dictOfTwitterUsers

    ###########################################################################
    ###########################################################################

    def run(self):
        # These Twitter list IDs are from the following public lists:
        # US House from @TwitterGov
        # US Senate from @TwitterGov
        # House Members from @HouseDailyPress
        # Senators from @cspan
        #listIDNumbers = (63915247, 63915645, 225745413, 4244910)
        # Note: not using this method anymore, but keeping some of the code here since
        # it might be useful in the future.
        #dictOfTwitterUsers = self.getTwitterUsersFromTwitterLists(listIDNumbers)
        
        # If any Twitter handles no longer exist or changed to a new handle, store those messages here.
        # We will email this list to ourselves later on.
        listBadTwitterHandleMsgs = []

        try:
            dictOfTwitterUsers = {}
            listOfIncludes,listOfSamePersons = Utilities.getCustomizedTwitterHandles()
            listBadTwitterHandleMsgs = self.includeCustomizedHandles(dictOfTwitterUsers, listOfIncludes)
            logMessage = Utilities.saveTwitterUsers(dictOfTwitterUsers)
            self.logger.log(logMessage)
        except BaseException as e:
            self.logger.log("Warning: failed to retrieve Twitter lists: " + str(e.args))
        
        return listBadTwitterHandleMsgs

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = RetrieveListsFromTwitter(logger)
    instance.run()
    

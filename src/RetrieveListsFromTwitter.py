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

    def isHandleInResults(self, handle, listOfResults):
        for user in listOfResults:
            if (handle.lower() == user.twitterHandle.lower()):
                return True

        return False

    ###########################################################################
    ###########################################################################

    def includeCustomizedHandles(self, dictOfTwitterUsers, handlesToLookup):
        for i in range(0, len(handlesToLookup), 100):
            # grab 0-99, 100-199, etc. because the api can only handle 100 at a time
            batch = handlesToLookup[i:i+100]
            results = self.doMultipleUserLookup(batch)

            if (len(batch) != len(results)):
                for handle in batch:
                    found = self.isHandleInResults(handle, results)
                    if (found == False):
                        self.logger.log(f"Warning: {handle} does not seem to be a valid Twitter handle")

            for user in results:
                dictOfTwitterUsers[user.twitterHandle] = user

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
        
        try:
            dictOfTwitterUsers = {}
            listOfIncludes,listOfSamePersons = Utilities.getCustomizedTwitterHandles()
            self.includeCustomizedHandles(dictOfTwitterUsers, listOfIncludes)
            logMessage = Utilities.saveTwitterUsers(dictOfTwitterUsers)
            self.logger.log(logMessage)
        except BaseException as e:
            self.logger.log("Warning: failed to retrieve Twitter lists: " + str(e.args))

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = RetrieveListsFromTwitter(logger)
    instance.run()
    

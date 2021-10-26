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
            self.logger.log("received username=" + item.username + ", id=" + str(item.id))
            
            handle = item.username
            idStr = str(item.id)
            website = item.url
            fullName = item.name
            bio = item.description
            
            user = Classes.TwitterUser(handle, idStr, "0", website, fullName, bio)
            listOfUsers.append(user)
        
        client = 0 # "disconnect"
        
        return listOfUsers
    
    ###########################################################################
    ###########################################################################

    def excludeCustomizedHandles(self, dictOfTwitterUsers, listOfExcludes):
        for handle in listOfExcludes:
            if (handle in dictOfTwitterUsers.keys()):
                dictOfTwitterUsers.pop(handle)
                self.logger.log("removing handle @" + handle)
            else:
                self.logger.log("Warning: could not manually exclude handle @" + handle)

    ###########################################################################
    ###########################################################################

    def includeCustomizedHandles(self, dictOfTwitterUsers, listOfIncludes):
        handlesToLookup = []
        
        for handle in listOfIncludes:
            if (handle in dictOfTwitterUsers.keys()):
                self.logger.log("Warning: handle @" + handle + " already in the list")
            else:
                handlesToLookup.append(handle)
                self.logger.log("adding handle @" + handle)
        
        if (len(handlesToLookup) > 0):
            listOfUsers = self.doMultipleUserLookup(handlesToLookup)
            for user in listOfUsers:
                dictOfTwitterUsers[user.twitterHandle] = user

    ###########################################################################
    ###########################################################################

    def getTwitterUsersFromTwitterLists(self, listIDNumbers):
        dictOfTwitterUsers = {}
        cred = Utilities.loadCredentials()
        
        # using v1.1 of the Twitter API
        auth = tweepy.OAuthHandler(cred.API_Key, cred.API_Secret_Key)
        auth.set_access_token(cred.Access_Token, cred.Access_Token_Secret)
        api = tweepy.API(auth, retry_count=3, retry_delay=10, wait_on_rate_limit=True)
        
        for listID in listIDNumbers:
            # count is the number of results to try and retrieve per page,
            # we will try to do it all in one page
            self.logger.log("retrieving members for list id " + str(listID))
            users = api.get_list_members(list_id=listID, count=1000)
            self.logger.log("retrieved " + str(len(users)) + " users")
            
            for user in users:
                handle = user.screen_name.lower()
                idStr = user.id_str
                website = user.url
                fullName = user.name
                bio = user.description
                
                data = Classes.TwitterUser(handle, idStr, "0", website, fullName, bio)
                dictOfTwitterUsers[handle] = data
        
        api = 0 # "disconnect"
        
        return dictOfTwitterUsers

    ###########################################################################
    ###########################################################################

    def run(self):
        # These Twitter list IDs are from the following public lists:
        # US House from @TwitterGov
        # US Senate from @TwitterGov
        # House Members from @HouseDailyPress
        # Senators from @cspan
        listIDNumbers = (63915247, 63915645, 225745413, 4244910)
        
        try:
            dictOfTwitterUsers = self.getTwitterUsersFromTwitterLists(listIDNumbers)
            listOfExcludes,listOfIncludes,listOfSamePersons = Utilities.getCustomizedTwitterHandles()
            self.excludeCustomizedHandles(dictOfTwitterUsers, listOfExcludes)
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
    
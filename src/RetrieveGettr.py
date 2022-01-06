from gogettr import PublicClient
import datetime
import time

import Utilities
import Classes

###############################################################################
###############################################################################

class RetrieveGettr:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################
    
    def integerToBase36(self, number: int):
        alphabet="0123456789abcdefghijklmnopqrstuvwxyz"

        if (number < len(alphabet)):
            return alphabet[number]

        base36 = ""
        while number != 0:
            number, remainder = divmod(number, len(alphabet)) # gives (x//y, x%y)
            base36 = alphabet[remainder] + base36

        return base36

    ###########################################################################
    ###########################################################################

    def base36ToInteger(self, number: str):
        return int(number, 36)

    ###########################################################################
    ###########################################################################

    def incrementByOne(self, mostRecentId: str):
        asInteger = self.base36ToInteger(mostRecentId)
        asInteger += 1
        incremented = self.integerToBase36(asInteger)
        return incremented

    ###########################################################################
    ###########################################################################

    def retrieveGweetsForUser(self, user: Classes.GettrUser, numberOfPostsForFirstScan):
        client = PublicClient()

        if (user.mostRecentPostIdStr.strip() == ""):
            self.logger.log("Retrieving Gweets for {}, max of {}".format(user.gettrHandle, numberOfPostsForFirstScan))
            posts = client.user_activity(username=user.gettrHandle, max=numberOfPostsForFirstScan, type="posts")
        else:
            # start from most recent post retrieved, but need to add 1 so we don't get the same post as last time
            self.logger.log("Retrieving Gweets for {}, after id {}".format(user.gettrHandle, user.mostRecentPostIdStr))
            until = self.incrementByOne(user.mostRecentPostIdStr)
            posts = client.user_activity(username=user.gettrHandle, until=until, type="posts")

        listOfPosts = [post for post in posts]
        listOfPosts.reverse()

        listOfGweets = []
        for post in listOfPosts:
            gweet = Classes.Tweet()
            gweet.id = self.base36ToInteger(post["_id"])
            gweet.created_at = Utilities.convertUdateToReadable(int(post["udate"]))
            gweet.text = post.get("txt", "")
            listOfGweets.append(gweet)

        # save the most recent post id so we don't retrieve these posts again
        if (len(listOfPosts) > 0):
            user.mostRecentPostIdStr = listOfPosts[-1]["_id"]

        self.logger.log("Retrieved {} gweets for user {}".format(len(listOfGweets), user.gettrHandle))

        return listOfGweets

    ###########################################################################
    ###########################################################################

    def run(self, secsBetweenHandles=10, numberOfPostsForFirstScan=20):
        currentDate = Utilities.getCurrentDate()
        listOfMembers = Utilities.loadCongressMembers()
        gettrLookupDict = Utilities.loadGettrLookup(listOfMembers)

        numHandlesRetrieved = 0
        gweetsToSave = []

        for member in listOfMembers:
            for handle in member.gettr:
                if (handle == ""):
                    continue

                user = gettrLookupDict[handle]

                for retries in range(0, 3):
                    try:
                        newGweets = self.retrieveGweetsForUser(user, numberOfPostsForFirstScan)
                        newGweets.insert(0, "#" + handle) # this will be used to separate gweets between different handles
                        gweetsToSave = gweetsToSave + newGweets
                        break
                    except BaseException as e:
                        if (retries <= 1):
                            self.logger.log("Warning: failed to retrieve Gweets for handle " + handle)
                        else:
                            self.logger.log("Error: failed to retrieve Gweets for handle " + handle)
                        self.logger.log(str(e.args))
                        time.sleep(5)
    
                numHandlesRetrieved += 1
                time.sleep(secsBetweenHandles) # slow down the requests to be nice to their servers

        # save the Gweets to a file
        if (len(gweetsToSave) > 0):
            self.logger.log("saving " + str(len(gweetsToSave)) + " gweets")
            logMessage = Utilities.saveGweets(gweetsToSave, currentDate)
            self.logger.log(logMessage)

        # save the most recent gweet ids so we don't grab the same ones again
        logMessage = Utilities.saveGettrLookup(gettrLookupDict)
        self.logger.log(logMessage)
        
        self.logger.log("Retrieved a total of " + str(len(gweetsToSave)) + " gweets")
        self.logger.log("Finished retrieving gweets for " + str(numHandlesRetrieved) + " handles")
        
        return len(gweetsToSave)

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = RetrieveGettr(logger)
    instance.run()

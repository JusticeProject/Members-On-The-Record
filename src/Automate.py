import time

import Utilities

import RetrieveListsFromTwitter
import CreateListOfCongressMembers
import RetrieveTweets
import AnalyzeTweets
import UploadResults

###############################################################################
###############################################################################

# Every day it will start the scan at this hour, uses 24-hour clock.
SCAN_HOUR = 11

# If True then it will scan right away, then proceed to scan every day at SCAN_HOUR.
# If False then it will only scan at the SCAN_HOUR.
scanOnStartup = True

# If we haven't done any scans yet, this specifies how many days in the past as the starting
# point for the Tweet retrieval. For subsequent scans it will only get new Tweets since the
# last scan.
numberOfDaysForFirstScan = 2

###############################################################################
###############################################################################

logger = Utilities.Logger()

while True:
    hour = Utilities.getCurrentHour()
    
    if (hour == SCAN_HOUR) or (scanOnStartup == True):
        scanOnStartup = False
        logger.prepareLogFile(UploadResults.GOOGLE_DRIVE_LOGS)
        
        # we will time how long everything takes
        startSecs = time.time()
        
        # retrieve the Twitter handles
        step1 = RetrieveListsFromTwitter.RetrieveListsFromTwitter(logger)
        step1.run()
        
        # use the lists we retrieved from Twitter to build our list of Congress members
        step2 = CreateListOfCongressMembers.CreateListOfCongressMembers(logger)
        step2.run()
    
        # retrieve the latest Tweets for each member of Congress
        step3 = RetrieveTweets.RetrieveTweets(logger)
        numTweetsRetrieved = step3.run(2, numberOfDaysForFirstScan)
        
        # If errors then we'll try again. If it still doesn't work then we'll grab the tweets tomorrow.
        # We won't miss any Tweets because we keep track of the most recent Tweet received for each user.
        if (logger.isErrorInLog() == True):
            logger.log("Problem detected in previous retrieval, will try to retrieve Tweets again")
            time.sleep(30 * 60)
            numTweetsRetrieved += step3.run(3, numberOfDaysForFirstScan) # slow it down a tad just in case
        
        # if we retrieved any tweets then analyze them, if not then nothing we can do because we don't want 
        # to upload yesterday's data
        if (numTweetsRetrieved > 0):
            # search every Tweet we just retrieved and look for the keywords
            step4 = AnalyzeTweets.AnalyzeTweets(logger)
            resultsFilePath = step4.run("", True, False)
        
            # upload results to GitHub and Google Drive
            step5 = UploadResults.UploadResults(logger)
            step5.run(resultsFilePath)
        
        stopSecs = time.time()
        diffMins = int((stopSecs - startSecs) / 60.0)
        logger.log("Scan took " + str(diffMins) + " minutes")
        
        logger.flushLogs()
        
        # Done with everything for this latest scan. Wait a bit so that the clock has moved off 
        # the SCAN_HOUR. We don't want to trigger another scan if we are still in the same hour.
        while (Utilities.getCurrentHour() == SCAN_HOUR):
            time.sleep(60)
        
        print("Done with Automate at " + Utilities.getLocalTime())
        print("Will wait until hour " + str(SCAN_HOUR) + " for next scan")
        
    time.sleep(60)

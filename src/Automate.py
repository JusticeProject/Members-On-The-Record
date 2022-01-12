import time
import subprocess
from multiprocessing import Process, Queue

import Utilities

import RetrieveListsFromTwitter
import CreateListOfCongressMembers
import RetrieveTweets
import RetrieveGettr
import ProcessImages
import AnalyzeTweets
import UploadResults
import EmailNotifications

###############################################################################
###############################################################################

# Every day it will start the scan at this hour, uses 24-hour clock.
SCAN_HOUR = 11

# Used by the spawned processes to communicate with the main process
DONE_MESSAGE = "MOTR Done Message"

###############################################################################
###############################################################################

def runScanLoop():
    # If True then it will scan right away, then proceed to scan every day at SCAN_HOUR.
    # If False then it will only scan at the SCAN_HOUR.
    config = Utilities.loadConfig()
    scanOnStartup = config.Scan_On_Startup

    logger = Utilities.Logger()

    while True:
        hour = Utilities.getCurrentHour()

        if (hour == SCAN_HOUR) or (scanOnStartup == True):
            scanOnStartup = False
            logger.prepareLogFile(UploadResults.GOOGLE_DRIVE_LOGS)

            # we will time how long everything takes
            startSecs = time.time()

            # use git to make sure we have the most recent version of some important files that might change often
            logger.log("Retrieving latest Keywords...")
            result = subprocess.run(["git", "pull"], capture_output=True)
            output = result.stdout.decode() + result.stderr.decode()
            lines = [line for line in output.split("\n") if line.strip() != ""]
            for line in lines:
                logger.log(line)
            if (result.returncode == 0):
                logger.log("Successfully pulled latest Keywords")
            else:
                logger.log("Warning: failed to get latest Keywords")

            # retrieve the Twitter handles
            step1 = RetrieveListsFromTwitter.RetrieveListsFromTwitter(logger)
            step1.run()

            # use the lists we retrieved from Twitter to build our list of Congress members
            step2 = CreateListOfCongressMembers.CreateListOfCongressMembers(logger)
            step2.run()

            # launch separate processes to grab the Tweets and Gweets, they will send us log messages using the Queue
            q = Queue()
            remoteLogger = Utilities.RemoteLogger(q)
            p1 = Process(target=twitterProcess, args=(remoteLogger,))
            p2 = Process(target=gettrProcess, args=(remoteLogger,))
            p1.start()
            p2.start()

            # wait until the processes are done
            numberProcessesRunning = 2
            while numberProcessesRunning > 0:
                msg = q.get(block=True, timeout=None)
                logger.log(msg)

                if (msg == DONE_MESSAGE):
                    numberProcessesRunning -= 1
                    logger.log("{} processes still running".format(numberProcessesRunning))
            
            # join with the other processes
            p1.join()
            logger.log("joined with Twitter Process")
            p2.join()
            logger.log("joined with Gettr Process")

            # search every Tweet we just retrieved and look for the keywords
            step3 = AnalyzeTweets.AnalyzeTweets(logger)
            resultsFilePath = step3.run("", config.Scan_Images)

            # upload results to GitHub and Google Drive
            step4 = UploadResults.UploadResults(logger)
            todaysResultsFileName = step4.run(resultsFilePath)

            # wait 5 minutes for the new results to go live, then send email
            if (todaysResultsFileName is not None):
                time.sleep(5 * 60)
                step5 = EmailNotifications.EmailNotifications(logger)
                step5.run(todaysResultsFileName)
            else:
                logger.log("Upload was not successful, not sending email notification")

            stopSecs = time.time()
            diffMins = (stopSecs - startSecs) // 60.0
            logger.log("Scan took about " + str(diffMins) + " minutes")

            logger.flushLogs()

            # Done with everything for this latest scan. Wait a bit so that the clock has moved off 
            # the SCAN_HOUR. We don't want to trigger another scan if we are still in the same hour.
            while (Utilities.getCurrentHour() == SCAN_HOUR):
                time.sleep(60)

            print("Done with Automate at " + Utilities.getLocalTime())
            print("Will wait until hour " + str(SCAN_HOUR) + " for next scan")

        time.sleep(60)

###############################################################################
###############################################################################

def twitterProcess(logger: Utilities.RemoteLogger):
    logger.log("Twitter Process started")

    # If we haven't done any scans yet, this specifies how many days in the past as the starting
    # point for the Tweet retrieval. For subsequent scans it will only get new Tweets since the
    # last scan.
    numberOfDaysForFirstScan = 2

    # retrieve the latest Tweets for each member of Congress
    instance = RetrieveTweets.RetrieveTweets(logger)
    errorOccurred = instance.run(2, numberOfDaysForFirstScan)

    # If errors then we'll try again. If it still doesn't work then we'll grab the tweets tomorrow.
    # We won't miss any Tweets because we keep track of the most recent Tweet received for each user.
    if (errorOccurred):
        logger.log("Problem detected in previous retrieval, will try to retrieve Tweets again")
        time.sleep(30 * 60)
        instance.run(3, numberOfDaysForFirstScan) # slow it down a tad just in case

    # Download the photos that Congress members posted because there could be statements or Congressional letters.
    # But first check if it has been enabled in the config file.
    config = Utilities.loadConfig()
    if (config.Scan_Images):
        imager = ProcessImages.ProcessImages(logger)
        imager.run()

    logger.log("Twitter Process complete.")
    logger.log(DONE_MESSAGE)

###############################################################################
###############################################################################

def gettrProcess(logger: Utilities.RemoteLogger):
    logger.log("  Gettr Process started")
    
    # Retrieve Gweets
    instance = RetrieveGettr.RetrieveGettr(logger)
    instance.run(60)

    logger.log("  Gettr Process complete.")
    logger.log(DONE_MESSAGE)

###############################################################################
###############################################################################
        
if __name__ == "__main__":
    runScanLoop()
    

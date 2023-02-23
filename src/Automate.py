import time

import Utilities

import RetrieveTwitterHandles
import CreateListOfCongressMembers
import RetrieveTweets
import ProcessImages
import AnalyzeTweets
import UploadResults
import EmailNotifications

###############################################################################
###############################################################################

def runScanLoop():
    # If True then it will scan right away, then proceed to scan every day at Scan_Hour.
    # If False then it will only scan at the Scan_Hour.
    config = Utilities.loadConfig()
    scanOnStartup = config.Scan_On_Startup
    lastScanDate = ""

    logger = Utilities.Logger()

    while True:
        hour = Utilities.getCurrentHour()
        date = Utilities.getCurrentDate()

        if (hour == config.Scan_Hour and date != lastScanDate) or (scanOnStartup == True):
            scanOnStartup = False
            lastScanDate = date

            # start a new log file for the current date
            if (config.Use_GitHub_GDrive_Email == True):
                logger.prepareLogFile(UploadResults.GOOGLE_DRIVE_LOGS)
            else:
                logger.prepareLogFile()

            # we will time how long everything takes
            startSecs = time.time()

            # retrieve the Twitter handles, take note of any bad Twitter handles
            step1 = RetrieveTwitterHandles.RetrieveTwitterHandles(logger)
            listBadTwitterHandleMsgs = step1.run(config.Use_GitHub_GDrive_Email)

            # use the Twitter handles we retrieved to build our list of Congress members
            step2 = CreateListOfCongressMembers.CreateListOfCongressMembers(logger)
            step2.run()

            # Retrieve the latest Tweets for each member of Congress.
            # If we haven't done any scans yet, we specify how many days in the past as the starting
            # point for the Tweet retrieval. For subsequent scans it will only get new Tweets since the
            # last scan.
            step3 = RetrieveTweets.RetrieveTweets(logger)
            errorOccurred = step3.run(2, config.Days_For_First_Scan)

            # If errors then we'll try again. If it still doesn't work then we'll grab the tweets tomorrow.
            # We won't miss any Tweets because we keep track of the most recent Tweet received for each user.
            if (errorOccurred):
                logger.log("Problem detected in previous retrieval, will try to retrieve Tweets again")
                time.sleep(10 * 60)
                step3.run(3, config.Days_For_First_Scan) # slow it down a tad just in case

            # Download the photos that Congress members posted because there could be statements or Congressional letters.
            # But first check if it has been enabled in the config file.
            if (config.Scan_Images):
                imager = ProcessImages.ProcessImages(logger)
                imager.run()

            # search every Tweet we just retrieved and look for the keywords
            step4 = AnalyzeTweets.AnalyzeTweets(logger)
            resultsFilePath = step4.run("", config.Scan_Images)

            if (config.Use_GitHub_GDrive_Email == True):
                # upload results to GitHub and Google Drive
                step5 = UploadResults.UploadResults(logger)
                todaysResultsFileName = step5.run(resultsFilePath)

                # wait 5 minutes for the new results to go live, then send email
                if (todaysResultsFileName is not None):
                    time.sleep(5 * 60)
                    step6 = EmailNotifications.EmailNotifications(logger)
                    step6.run(todaysResultsFileName, listBadTwitterHandleMsgs)
                else:
                    logger.log("Warning: Not sending email notification")

            stopSecs = time.time()
            diffMins = (stopSecs - startSecs) // 60.0
            logger.log("Scan took about " + str(diffMins) + " minutes")

            logger.flushLogs()

            # Done with everything for this latest scan. Wait a bit so that the clock has moved off 
            # the SCAN_HOUR. We don't want to trigger another scan if we are still in the same hour.
            while (Utilities.getCurrentHour() == config.Scan_Hour):
                time.sleep(60)

            print("Done with Automate at " + Utilities.getLocalTime())
            print("Will wait until hour " + str(config.Scan_Hour) + " for next scan")

        time.sleep(60)

###############################################################################
###############################################################################
        
if __name__ == "__main__":
    try:
        runScanLoop()
    except BaseException as e:
        strError = str(e.args)
        print("Run failed:" + strError)
        input("Hit Enter to exit")
    

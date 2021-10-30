import distutils.file_util
import distutils.dir_util
import time

from github import Github

import Utilities
import Classes

###############################################################################
###############################################################################

# This assumes that Google Drive for Desktop has been installed
GOOGLE_DRIVE_RESULTS = "C:/GoogleDrive/results/"
GOOGLE_DRIVE_LOGS = "C:/GoogleDrive/logs/"

###############################################################################
###############################################################################

class UploadResults:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################

    def uploadTodaysResults(self, repo, todaysResultsPath):
        # upload today's results file
        file = open(todaysResultsPath, "r", encoding="utf-8")
        data = file.read()
        file.close()
        todaysResultsFileName = todaysResultsPath.rsplit("/", 1)[1]
        todaysMonth = todaysResultsFileName[:7] # ex: convert 2021-10-29-Fri.html to 2021-10
        gitHubPath = "docs/" + todaysMonth + "/" + todaysResultsFileName
        repo.create_file(path=gitHubPath,
                         message="Auto-commit: upload today's results", content=data, branch="main")

        self.logger.log("Uploaded today's results to GitHub: " + gitHubPath)

    ###########################################################################
    ###########################################################################

    def getAllResultsOnGitHub(self, repo):
        # Grab all the folders of results that are currently on GitHub.
        folderNames = []
        contents = repo.get_contents("docs") # contents of the docs folder
        for item in contents:
            if (item.type == "dir"):
                folderNames.append(item.path.strip("/")) # ex: docs/2021-10

        folderNames.sort(reverse=True)

        # Now get all the file names from each folder
        dictOfMonths = {}
        for folder in folderNames:
            subfolder = folder.split("/")[1] # ex: convert docs/2021-10 to 2021-10
            month = Utilities.convertYearMonthToReadable(subfolder) # ex: convert 2021-10 to October 2021
            dictOfMonths[month] = []

            listOfFiles = []
            contents = repo.get_contents(folder) # get contents of this month's folder
            for file in contents:
                listOfFiles.append(file.name) # ex: 2021-10-29-Fri.html

            listOfFiles.sort(reverse=True)

            # Use a data structure to store all the relevant info for each webpage of results
            for fileName in listOfFiles:
                page = Classes.Page()
                page.subfolder = subfolder # ex: 2021-10
                page.filename = fileName # ex: 2021-10-29-Fri.html
                dateSortable = fileName.split(".html")[0]
                page.visibleText = Utilities.convertDateToReadable(dateSortable) # ex: convert to Fri October 29, 2021
                dictOfMonths[month].append(page)

        return dictOfMonths

    ###########################################################################
    ###########################################################################
    
    def updateResultsIndex(self, repo, dictOfMonths):
        # use jinja to create the webpage containing the index of results
        htmlTemplate = Utilities.getHTMLTemplateIndexResults()
        htmlResults = htmlTemplate.render(dictOfMonths=dictOfMonths)
        logMessage, resultsFileName = Utilities.saveHTMLResults("../output/", "index-of-results.html", htmlResults)
        self.logger.log(logMessage)

        # update the file on GitHub
        filename = "../output/index-of-results.html"
        file = open(filename, "r", encoding="utf-8")
        data = file.read()
        file.close()
        contents = repo.get_contents("docs/index-of-results.html")
        repo.update_file(path="docs/index-of-results.html", message="Auto-commit: updating list of days with results",
                         content=data, sha=contents.sha, branch="main")
        self.logger.log("Uploaded index-of-results.html to GitHub")

    ###########################################################################
    ###########################################################################
    
    def uploadToGoogleDrive(self):
        # make a backup of the userLookup file which tells us the most recent tweet id for each Twitter handle
        distutils.file_util.copy_file(Utilities.USER_LOOKUP_FILENAME, GOOGLE_DRIVE_RESULTS)
        self.logger.log("copied " + Utilities.USER_LOOKUP_FILENAME + " to " + GOOGLE_DRIVE_RESULTS)
        
        # make a backup of the raw tweet data in case we need to analyze it again
        recentResultsFolder = Utilities.getMostRecentResultsFolder().rstrip("/")
        justTheFolderName = recentResultsFolder.rsplit("/", 1)[1]
        todaysMonth = justTheFolderName[:7] # ex: convert 2021-10-29-Fri to 2021-10
        destinationPath = GOOGLE_DRIVE_RESULTS + todaysMonth + "/" + justTheFolderName
        distutils.dir_util.copy_tree(recentResultsFolder, destinationPath)
        self.logger.log("copied " + justTheFolderName + " to " + destinationPath)
    
    ###########################################################################
    ###########################################################################

    def run(self, todaysResultsPath):
        # use Google Drive for Desktop to upload the files
        self.uploadToGoogleDrive()
        
        # set up the connection to GitHub
        cred = Utilities.loadCredentials()
        git = Github(cred.GitHub_Token)
        repo = git.get_user().get_repo("Members-On-The-Record")

        # upload today's results to GitHub, if it fails then no point in continuing
        for retries in range(0, 3):
            try:
                self.uploadTodaysResults(repo, todaysResultsPath)
                break # if we got this far without an exception then break out of the for loop
            except BaseException as e:
                strError = str(e.args)
                self.logger.log("Error: failed to upload today's results to GitHub: " + strError)
                if (retries <= 1):
                    time.sleep(5)
                else:
                    return
        
        # Get all the results that are currently stored on GitHub, if it fails then no point in continuing.
        # This info will be used to create the index in the next step.
        for retries in range(0, 3):
            try:
                dictOfMonths = self.getAllResultsOnGitHub(repo)
                break # if we got this far without an exception then break out of the for loop
            except BaseException as e:
                strError = str(e.args)
                self.logger.log("Error: failed to retrieve all results on GitHub: " + strError)
                if (retries <= 1):
                    time.sleep(5)
                else:
                    return
        
        # update the index of results on GitHub
        for retries in range(0, 3):
            try:
                self.updateResultsIndex(repo, dictOfMonths)
                break # if we got this far without an exception then break out of the for loop
            except BaseException as e:
                strError = str(e.args)
                self.logger.log("Error: failed to upload index of results to GitHub: " + strError)
                if (retries <= 1):
                    time.sleep(5)
                else:
                    return
        
###############################################################################
###############################################################################
    
if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = UploadResults(logger)
    # Note: to run this as a standalone script you need to place the path of today's scan 
    # results in the run function
    instance.run("")
    
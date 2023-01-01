from email.mime.text import MIMEText
import smtplib
from bs4 import BeautifulSoup
import re
import time

import Utilities

###############################################################################
###############################################################################

class EmailNotifications:
    def __init__(self, logger):
        self.logger = logger

    ###########################################################################
    ###########################################################################

    def createDeveloperMessage(self, listDeveloperMsgs):
        body = "\n".join(listDeveloperMsgs)

        message = MIMEText(body)
        message['Subject'] = "New developer message for Members on the Record"

        with open("../config/Email.txt") as file:
            lines = file.readlines()
            for line in lines:
                if ("To=" in line):
                    message["To"] = line.split("To=")[1].strip()
                elif ("From=" in line):
                    message["From"] = line.split("From=")[1].strip()

        return message

    ###########################################################################
    ###########################################################################

    def createMessage(self, date):
        body = "For security reasons these emails will never contain a link to the results - you probably already have that page bookmarked.\n\n" + \
            "If the new results don't appear then try refreshing the page in your web browser.\n\n" + \
            "If you don't want to receive these notifications anymore then just respond to this email and let me know."

        message = MIMEText(body)
        message['Subject'] = "New results available for Members on the Record - " + date

        with open("../config/Email.txt") as file:
            lines = file.readlines()
            for line in lines:
                if ("To=" in line):
                    message["To"] = line.split("To=")[1].strip()
                elif ("Bcc=" in line):
                    message["Bcc"] = line.split("Bcc=")[1].strip()
                elif ("From=" in line):
                    message["From"] = line.split("From=")[1].strip()

        return message

    ###########################################################################
    ###########################################################################

    def sendEmail(self, msg):
        username = ""
        password = ""
        with open("../config/Email.txt") as file:
            lines = file.readlines()
            for line in lines:
                if ("Email_Username=" in line):
                    username = line.split("Email_Username=")[1].strip()
                elif ("Email_Password=" in line):
                    password = line.split("Email_Password=")[1].strip()

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(username, password)
        result = s.send_message(msg)
        self.logger.log(str(result))
        s.quit()
        self.logger.log("Finished sending email notification")

    ###########################################################################
    ###########################################################################

    def areNewResultsAvailable(self, todaysResultsFileName):
        self.logger.log("Checking if {} is in the index of results".format(todaysResultsFileName))

        # scrape the index page to verify that the link is there
        html, binary_data, respCode = Utilities.getWebsiteData("https://justiceproject.github.io/Members-On-The-Record/index-of-results.html")
        if (todaysResultsFileName in html):
            try:
                parsed_html = BeautifulSoup(html, "html.parser")
                element = parsed_html.find("a", href=re.compile(todaysResultsFileName))
                url = element["href"]
                self.logger.log("Found url {}".format(url))
            except BaseException as e:
                self.logger.log("Warning: exception in areNewResultsAvailable: {}".format(e.args))
                return False

            # go to the link to verify the data is there
            html, binary_data, respCode = Utilities.getWebsiteData(url)
            self.logger.log("Length of new results html page is {}".format(len(html)))
            if (len(html) > 1000):
                self.logger.log("Seems good, proceeding")
                return True
            else:
                self.logger.log("Seems lacking, something went wrong")
                return False
        
        self.logger.log("Warning: today's results not found in the index of results")
        return False

    ###########################################################################
    ###########################################################################

    def run(self, todaysResultsFileName, listDeveloperMsgs=[]):
        # send developer messages to ourself
        if (len(listDeveloperMsgs) > 0):
            try:
                self.logger.log(f"Sending {len(listDeveloperMsgs)} lines for developer message")
                devMsg = self.createDeveloperMessage(listDeveloperMsgs)
                self.sendEmail(devMsg)
            except BaseException as e:
                self.logger.log("Warning: exception when trying to send developer email: {}".format(e.args))

        # send results to all subscribers
        MAX_TRIES = 5
        for i in range(1, MAX_TRIES + 1):
            uploaded = self.areNewResultsAvailable(todaysResultsFileName)
            if (uploaded):
                break
            else:
                if (i < MAX_TRIES):
                    self.logger.log("Waiting a littler longer to see if the new results appear")
                    time.sleep(60)
                else:
                    self.logger.log("Warning: not waiting any longer for the new results")
                    return

        dateSortable = todaysResultsFileName.split(".html")[0]
        dateReadable = Utilities.convertDateToReadable(dateSortable)
        msg = self.createMessage(dateReadable)

        try:
            self.sendEmail(msg)
        except BaseException as e:
            self.logger.log("Warning: exception when trying to send email: {}".format(e.args))

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = EmailNotifications(logger)
    # need to fill in filename of today's results, ex: 2021-12-19-Sun.html
    instance.run("today.html")

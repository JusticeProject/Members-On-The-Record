import os.path
from email.mime.text import MIMEText
import base64
from bs4 import BeautifulSoup
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import Utilities

###############################################################################
###############################################################################

class EmailNotifications:
    def __init__(self, logger):
        self.logger = logger
    
    ###########################################################################
    ###########################################################################

    def getCredentials(self, userAtTerminal):
        # If modifying these scopes, delete the file token.json.
        SCOPES = ['https://www.googleapis.com/auth/gmail.send']

        creds = None

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('../config/token.json'):
            creds = Credentials.from_authorized_user_file('../config/token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.log("Refreshing the token in the credentials file")
                creds.refresh(Request())
            else:
                if (userAtTerminal):
                    flow = InstalledAppFlow.from_client_secrets_file('../config/credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    self.logger.log("Warning: gmail credentials expired, need to do manual login")
                    return None

        # Save the credentials for the next run
        with open('../config/token.json', 'w') as token:
            token.write(creds.to_json())
            self.logger.log("Credentials have been saved for the next run")

        return creds

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

        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        raw_data = {"raw":raw}

        return raw_data

    ###########################################################################
    ###########################################################################

    def sendEmail(self, creds, msg):
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        user = service.users()
        gmail = user.messages()
        gmail.send(userId="me", body=msg).execute()
        self.logger.log("Finished sending email notification")

    ###########################################################################
    ###########################################################################

    def areNewResultsAvailable(self, todaysResultsFileName):
        self.logger.log("Checking if {} is in the index of results".format(todaysResultsFileName))

        # scrape the index page to verify that the link is there
        html, respCode = Utilities.getWebsiteHTML("https://justiceproject.github.io/Members-On-The-Record/index-of-results.html")
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
            html, respCode = Utilities.getWebsiteHTML(url)
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

    def run(self, todaysResultsFileName, userAtTerminal = False):
        uploaded = self.areNewResultsAvailable(todaysResultsFileName)
        if (not uploaded):
            return

        dateSortable = todaysResultsFileName.split(".html")[0]
        dateReadable = Utilities.convertDateToReadable(dateSortable)
        msg = self.createMessage(dateReadable)

        try:
            creds = self.getCredentials(userAtTerminal)
            if (not creds):
                return
            self.sendEmail(creds, msg)
        except BaseException as e:
            self.logger.log("Warning: exception when trying to send email: {}".format(e.args))

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = EmailNotifications(logger)
    # need to fill in filename of today's results, ex: 2021-12-19-Sun.html
    instance.run("today.html", True)

# Members On The Record (Automated)
This software will perform an automated search for U.S. Congress members' social media posts about the Middle East. Posts are categorized by country and the results are neatly formatted in HTML. Currently supports Tweets (GETTR was supported but removed).

## Directory structure
#### config folder
* Config.txt - Various config parameters.
* Credentials.txt - Access tokens for Twitter and GitHub are placed here. These allow Python to connect to those websites' APIs.
* CustomizedTwitterHandles.txt - The master list of Twitter handles. Add or remove from this list as Congress members come and go.
* Email.txt - Email addresses for sending the daily results.
* Keywords.txt - These are the words that are searched for in the social media posts.
* HTML templates - Python will use these templates and fill in the data before publishing them to the web.
#### docs folder
* Includes this readme file and also the HTML results for all the scans done so far.
#### handleFinder folder
* Various helper scripts to scrape data and look for more Twitter handles. Not part of the daily scan.
#### src folder
* Automate.py - The main entry point of the program which will load all the other scripts and use them as necessary.
* Most of the other scripts can be run stand-alone which is useful when debugging.

## Instructions for installing/running
* Create a [Twitter Developer account](https://developer.twitter.com/en/apply-for-access). You will receive some access tokens which can be placed in the file config/config.txt.
* Install [Python](https://www.python.org/downloads/)
* If uploading results to GitHub or Google Drive then config/Credentials.txt and src/UploadResults.py should be updated.
* Install [Git](https://git-scm.com/downloads) command line utility.
* Run the following commands at a command prompt to finish the installation:
```bash
pip install tweepy
pip install jinja2
pip install PyGithub
pip install pytesseract
pip install numpy
pip install beautifulsoup4
pip install brotlicffi
pip install brotli
```
* Run this command at a command prompt while in the src directory to start the daily automated scan:
```bash
python .\Automate.py
```

## Thanks
Huge thank you to the contributors at the [congress-legislators project](https://github.com/unitedstates/congress-legislators) for making so much data available about each member of Congress.

## Why this project?
Whether I agree or disagree with a member of Congress, I want to know what they are saying about the wars and human rights issues in the Middle East. A daily automated search through their social media posts is a good way to do that. This project was inspired by the great work being done over at the [Foundation for Middle East Peace.](https://fmep.org/resources/?rsearch=&rcat%5B%5D=345)

## Current Results
This page contains a list of all the daily scans that have been uploaded:

[Index of Results](https://justiceproject.github.io/Members-On-The-Record/index-of-results.html)

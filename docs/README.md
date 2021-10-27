# Members-On-The-Record
An automated search for U.S. Congress members' Tweets about the Middle East. Tweets are categorized by country and the results are neatly formatted in HTML.

## Directory structure
#### config folder
Access tokens, manual additions and exclusions of Twitter handles, keywords that are used when searching tweets
#### docs folder
Includes this readme file and also the html results for all the scans done so far.
#### src folder
All the Python source code. The entry point is Automate.py but many of the other scripts can be run stand-alone which is useful when debugging.

## Instructions for installing/running
* Create a [Twitter Developer account](https://developer.twitter.com/en/apply-for-access). You will receive some access tokens which can be place in the file config/config.txt.
* Install [Python](https://www.python.org/downloads/)
* Run the following commands at a command prompt:
```bash
pip install tweepy
pip install jinja2
pip install PyGithub
python Automate.py
```

## TODO list
* Detect repeat Tweets when a member of Congress posts the same message from multiple accounts.
* When a member of Congress posts an image, it could contain a letter with lots of text that could be searched. It seems [this Python project](https://pypi.org/project/pytesseract/) could be used to handle the image-to-text conversion.
* Continuously improve the search algorithm and the list of keyword search terms to ensure only relevant Tweets are in the results and are categorized properly.
* Automate the search of Congress Members' floor speeches and press releases by scraping the data from senate.gov, house.gov, and congress.gov while obeying the sites' robots.txt files.
* Download the legislators-current.csv file only if it has changed.

## Why this project?
Whether I agree or disagree with a member of Congress, I want to know what they are saying about the wars and human rights issues in the Middle East. A daily automated search through their Tweets is a good way to do that. This project was inspired by the great work being done over at the [Foundation for Middle East Peace.](https://fmep.org/resources/?rsearch=&rcat%5B%5D=345)

## Current Results
This page contains a list of all the daily scans that have been uploaded:

[Index of Results](https://justiceproject.github.io/Members-On-The-Record/index-of-results.html)

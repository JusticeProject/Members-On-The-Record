from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
import requests

import time

###################################################################################################

def initialize_selenium():
    # This assumes the chromedriver has already been downloaded from here:
    # https://chromedriver.chromium.org/downloads

    serv=Service("./chromedriver.exe")
    driver = webdriver.Chrome(service=serv)
    driver.delete_all_cookies()
    return driver

###################################################################################################

def get_campaign_site(rep_name):
    print("Looking for campaign site for " + rep_name)
    driver = initialize_selenium()
    driver.get("https://www.google.com/")

    elem = driver.find_element(By.NAME, "q")
    elem.clear()

    search_query = rep_name + " campaign website"
    # for letter in search_query:
    #     elem.send_keys(letter)
    #     time.sleep(1)
    elem.send_keys(search_query)
    time.sleep(1)
    elem.send_keys(Keys.RETURN)
    time.sleep(3)

    # look for the first h3 tag and click it
    elem = driver.find_element(By.TAG_NAME, "h3")
    elem.click()
    time.sleep(5)

    html = driver.page_source
    driver.close()
    return html

###################################################################################################

def get_wiki_page(local : bool):
    if local:
        html = open("wiki.html", "r", encoding="utf-8").read()
    else:
        result = requests.get("https://en.wikipedia.org/wiki/2022_United_States_House_of_Representatives_elections")
        html = result.text
        fh = open("wiki.html", "w", encoding="utf-8")
        fh.write(html)
        fh.close()

    return html

###################################################################################################

def extract_rep_names(html):
    bs = BeautifulSoup(html, "html.parser")
    imgs = bs.find_all("img", {"alt": "Green tick"})

    all_names = []
    for img in imgs:
        parent = img.parent
        a = parent.find("a")
        all_names.append(a.text)

    all_names = list(set(all_names)) # remove any repeats
    return all_names

###################################################################################################

def extract_twitter_handles(html):
    handles = []

    bs = BeautifulSoup(html, "html.parser")
    links = bs.find_all("a")
    for a in links:
        if "href" in a.attrs.keys():
            href = a.attrs["href"].lower()
            if ("www.twitter.com/" in href) or ("http://twitter.com/" in href) or ("https://twitter.com/" in href):
                if ("twitter.com/search?" in href):
                    continue
                
                if ("twitter.com/intent/" in href):
                    href = href.replace("intent/follow?screen_name=", "")

                handles.append(href)

    handles = list(set(handles)) # remove repeats
    print("found handles " + str(handles))
    return handles

###################################################################################################

def save_file(list_to_save, filename):
    print(f"Writing {len(list_to_save)} items to {filename}")
    fh = open(filename, "w", encoding="utf-8")
    for item in list_to_save:
        fh.write(item + "\n")
    fh.close()

###################################################################################################

def save_name_handles(filename, rep_name, handles):
    fh = open(filename, "a", encoding="utf-8")
    fh.write(rep_name + "\n")
    for handle in handles:
        fh.write(handle + "\n")
    fh.close()

###################################################################################################

if __name__ == "__main__":
    # html = open("campaign.html", "r", encoding="utf-8").read()
    # handles = extract_twitter_handles(html)

    # first get all the names of elected reps from a Wiki page
    html = get_wiki_page(local=True)
    all_names = extract_rep_names(html)
    save_file(all_names, "all_rep_names.txt")

    # now look for the campaign site for each rep, and extract a Twitter handle from the html
    all_handles = []
    for name in all_names:
        try:
            html = get_campaign_site(name)
        except BaseException as e:
            strError = str(e.args)
            print("Failed to get campaign site: " + strError)
            time.sleep(300)
            html = '<a href="www.twitter.com/Error">Blah</a>'

        handles = extract_twitter_handles(html)
        for handle in handles:
            all_handles.append(handle)
        # append to file after each handle found, just in case...
        save_name_handles("all_rep_names_handles.txt", name, handles)

        time.sleep(45)

    save_file(all_handles, "all_handles.txt")

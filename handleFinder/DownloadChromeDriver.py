import os.path
import re
from urllib.request import urlopen, urlretrieve
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import zipfile

###################################################################################################

def get_chrome_version():
    paths = ["C:/Program Files/Google/Chrome/Application/", "C:/Program Files (x86)/Google/Chrome/Application/"]

    for folder in paths:
        if (os.path.exists(folder)):
            print("found " + folder)
            contents = os.listdir(folder)
            for item in contents:
                if os.path.isdir(folder + "/" + item):
                    regExp = re.compile(r"\d+\.\d+\.\d+.*") # looking for numbers in the form ddd.ddd.ddd
                    if (regExp.match(item)):
                        print("found chrome version " + item)
                        return item
    
    raise Exception("could not find chrome")

###################################################################################################

def get_chrome_driver_version(chrome_version):
    major_version = chrome_version.split(".")[0]

    # use beautiful soup to grab new links for Chrome downloads
    html = urlopen("https://chromedriver.chromium.org/downloads")
    bs = BeautifulSoup(html, "html.parser")
    regExp = re.compile(r"If you are using Chrome version (\d+), please download ChromeDriver \d+")
    paragraphs = bs.find_all("p")
    for p in paragraphs:
        match = regExp.findall(p.text)
        if len(match) > 0 and (match[0] == major_version):
            print(p.text)
            link = p.find("a").attrs["href"]
            chrome_driver_version = urlparse(link).query.strip("/")
            chrome_driver_version = chrome_driver_version.split("=")[-1]
            print("found chrome driver version " + chrome_driver_version)
            return chrome_driver_version
    
    raise Exception("could not find chrome driver version")

###################################################################################################

def download_zip(chrome_driver_version):
    filename = "chromedriver_win32.zip"
    zip_link = "https://chromedriver.storage.googleapis.com/" + chrome_driver_version + "/" + filename
    print("downloading " + zip_link)
    urlretrieve(zip_link, filename)
    print("extracting zip file")
    with zipfile.ZipFile("./" + filename, 'r') as zip_ref:
        zip_ref.extractall(".")

###################################################################################################

chrome_version = get_chrome_version()
chrome_driver_version = get_chrome_driver_version(chrome_version)
download_zip(chrome_driver_version)
print("done!")

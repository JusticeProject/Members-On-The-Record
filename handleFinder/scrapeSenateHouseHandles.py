import sys
sys.path.append("../src")
import Utilities

from bs4 import BeautifulSoup
import time

###############################################################################
###############################################################################

def getLinksInTable(parsed_html):
    links = []

    tables = parsed_html.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            atag = row.find("a")
            if (atag is None):
                continue
            if ("href" not in atag.attrs.keys()):
                continue
            url = atag.attrs["href"].rstrip("/")
            if (url not in links):
                links.append(url)
            
    return links

###############################################################################
###############################################################################

def getHandlesFromLinks(links):
    handles = []
    
    for link in links:
        print("Looking for Twitter handles at " + link)
        html, binary, code = Utilities.getWebsiteData(link)
        parsed_html = BeautifulSoup(html, "html.parser")

        links = parsed_html.find_all("a")
        for a in links:
            if "href" in a.attrs.keys():
                href = a.attrs["href"].lower()
                if ("www.twitter.com/" in href) or ("http://twitter.com/" in href) or ("https://twitter.com/" in href):
                    if ("twitter.com/search?" in href):
                        continue
                    
                    if ("twitter.com/intent/" in href):
                        href = href.replace("intent/follow?screen_name=", "")

                    # get rid of some symbols that might screw us up
                    href = href.split("?")[0]
                    href = href.replace("#!/", "")
                    href = href.replace("@", "")

                    href_split = href.split("twitter.com/")
                    if len(href_split) <= 1:
                        continue

                    handle = href_split[1].split("/")[0]
                    handle = handle.strip()
                    if (handle not in handles) and (len(handle) > 0) and (handle != "intent") and (handle != "i"):
                        handles.append(handle)
        
        time.sleep(15)

    return handles

###############################################################################
###############################################################################

if __name__ == "__main__":
    html, binary, code = Utilities.getWebsiteData("https://www.house.gov/representatives")
    parsed_html = BeautifulSoup(html, "html.parser")
    house_links = getLinksInTable(parsed_html)
    print(f"Found {len(house_links)} links from house.gov")

    html, binary, code = Utilities.getWebsiteData("https://www.senate.gov/senators/index.htm")
    parsed_html = BeautifulSoup(html, "html.parser")
    senate_links = getLinksInTable(parsed_html)
    print(f"Found {len(senate_links)} links from senate.gov")

    all_links = senate_links + house_links
    
    found_handles = getHandlesFromLinks(all_links)
    print(f"Found {len(found_handles)} handles")

    # if a handle is not already in our list from CustomizedTwitterHandles.txt then log it as new
    currentHandles, samePersons = Utilities.getCustomizedTwitterHandles()
    print("Begin list of new handles:")
    fh = open("scraped_handles.txt", "w", encoding="utf-8")
    for handle in found_handles:
        if (handle not in currentHandles):
            print(handle)
            fh.write(handle + "\n")
    print("End list of new handles.")
    fh.close()


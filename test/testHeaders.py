import sys
sys.path.append("../src")
import Utilities

#url = "https://www.bloomberg.com/news/articles/2021-11-24/israel-morocco-sign-defense-cooperation-pact-gantz-says"
#url = "https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending"
#url = "https://bacon.house.gov/news/documentsingle.aspx?DocumentID=765"
#url = "https://www.jpost.com/opinion/hezbollah-is-a-threat-to-latin-america-opinion-688022"
url = "https://tennesseestar.com/2022/02/10/tennessee-senators-blackburn-and-hagerty-join-texas-senator-ted-cruz-in-sending-letter-to-president-biden-regarding-iran-nuclear-deal/"
#url = "http://newsradio1620.streamguys.org/wnrp"
#url = "https://www.google.com"
#url = "https://www.youtube.com/watch?v=K7HCntVQ02s"

#html, binary_data, respcode = Utilities.getWebsiteUsingCurl(url)
html, binary_data, respcode = Utilities.getWebsiteData(url, True)
title = Utilities.extractTitleFromHTML(html)
print("{} {} {}".format(len(html), len(binary_data), respcode))
print("title = {}".format(title))

# url = "http://192.168.1.12:6512/"
# html, binary_data, respcode = Utilities.getWebsiteData(url, True)
# title = Utilities.extractTitleFromHTML(html)
# print("{} {} {}".format(len(html), len(binary_data), respcode))
# print("title = {}".format(title))

# url = "http://192.168.1.12:6512/gzip"
# html, binary_data, respcode = Utilities.getWebsiteData(url, True)
# title = Utilities.extractTitleFromHTML(html)
# print("{} {} {}".format(len(html), len(binary_data), respcode))
# print("title = {}".format(title))

# url = "http://192.168.1.12:6512/deflate"
# html, binary_data, respcode = Utilities.getWebsiteData(url, True)
# title = Utilities.extractTitleFromHTML(html)
# print("{} {} {}".format(len(html), len(binary_data), respcode))
# print("title = {}".format(title))

# url = "http://192.168.1.12:6512/br"
# html, binary_data, respcode = Utilities.getWebsiteData(url, True)
# title = Utilities.extractTitleFromHTML(html)
# print("{} {} {}".format(len(html), len(binary_data), respcode))
# print("title = {}".format(title))

# url = "https://www.ronjohnson.senate.gov/services/files/F9D5467E-EEC9-4AEC-9156-73C5957CFE57" # PDF
# html, binary_data, respcode = Utilities.getWebsiteData(url, False)
# print("{} {} {}".format(len(html), len(binary_data), respcode))

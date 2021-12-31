import pytesseract
from pytesseract import Output
from PIL import Image
import numpy as np
import time
import os
import requests
from multiprocessing import Process, Queue

import Utilities
import Classes

#####################################################################################
#####################################################################################

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#####################################################################################
#####################################################################################

class ProcessImages:
    def __init__(self, logger):
        self.logger = logger
        self.resultsFolder = ""
        self.imagesFolder = ""

    ###########################################################################
    ###########################################################################
    
    def downloadPhoto(self, url):
        if (os.path.exists(self.imagesFolder) == False):
            os.mkdir(self.imagesFolder)

        filename = url.rsplit("/", 1)[1]
        localPath = self.imagesFolder + filename
        
        if (os.path.exists(localPath)):
            #self.logger.log(localPath + " already exists")
            return localPath
        else:
            time.sleep(2) # be nice to Twitter, don't hit them too fast with lots of requests for downloads

            for retries in range(0, 3):
                try:
                    seconds = retries + 2  # first 2 seconds, then 3, then 4
                    req = requests.get(url, headers=Utilities.getCustomHeader(), timeout=seconds)
                    file = open(localPath, "wb")
                    file.write(req.content)
                    file.close()
                    #self.logger.log("After " + str(retries) + " retries, image saved to " + localPath)
                    return localPath
                except BaseException as e:
                    if (retries < 2):
                        time.sleep(1)
                    else:
                        self.logger.log("Warning: could not download photo: " + str(e.args))
            
        return ""

    #####################################################################################
    #####################################################################################

    def convertToBW(self, grayImage, threshold):
        #Set a threshold value for the image, and save as black & white
        bwImage = grayImage.point(lambda x: 0 if x<threshold else 255)
        return bwImage

    #####################################################################################
    #####################################################################################

    def getConfidence(self, image):
        # For each image-to-text conversion we will get the average confidence (0 - 100) and 
        # multiply it by the number of characters foun in the text. The higher the confidence and 
        # higher the number of characters found, the higher the score. Highest score will win.
        data = pytesseract.image_to_data(image, output_type=Output.DICT)
        text = data['text']
        confidences = []
        numChars = []
        
        for i in range(len(text)):
            conf = float(data['conf'][i])
            if conf > -1:
                confidences.append(conf)
                numChars.append(len(text[i]))

        if (sum(numChars)) > 0:
            score = np.average(confidences, weights=numChars) * sum(numChars)
            return score
        else:
            return 0

    #####################################################################################
    #####################################################################################

    def testThresholds(self, grayImage, start, end, step):
        thresholdsAndScores = []

        for threshold in range(start, end, step):
            bwImage = self.convertToBW(grayImage, threshold)
            score = self.getConfidence(bwImage)
            thresholdsAndScores.append((threshold, score))

        return thresholdsAndScores

    #####################################################################################
    #####################################################################################

    def convertPhotoToText(self, localImagePath):
        # This algorithm was borrowed from:
        #     Web Scraping with Python, Second Edition by Ryan Mitchell (O'Reilly). 
        #     Copyright 2018 Ryan Mitchell, 978-1-491-998557-1

        if (localImagePath == ""):
            return ""
        
        colorImage = Image.open(localImagePath)
        grayImage = colorImage.convert("L")
        colorImage.close()

        # do a wide test of the thresholds after which we can narrow it down a bit
        thresholdsAndScores = self.testThresholds(grayImage, 80, 200, 10)
        thresholdsAndScores.sort(key=lambda tup: tup[1], reverse=True) # sort in descending order according to score
        goodThreshold = thresholdsAndScores[0][0]

        # test above and below the good threshold that we already found, we'll pick the best from that
        thresholdsAndScores += self.testThresholds(grayImage, goodThreshold + 1, goodThreshold + 10, 1)
        thresholdsAndScores += self.testThresholds(grayImage, goodThreshold - 9, goodThreshold, 1)
        thresholdsAndScores.sort(key=lambda tup: tup[1], reverse=True)
        idealThreshold = thresholdsAndScores[0][0]

        bwImage = self.convertToBW(grayImage, idealThreshold)
        text = pytesseract.image_to_string(bwImage)
        
        # clean up the text, these symbols could cause problems with html formatting
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace("&", "&amp;")
        text = text.replace("", "") # this is an up arrow that likes to show up a lot during image conversion
        return text

    #####################################################################################
    #####################################################################################

    def writeTextToFile(self, capturedText, localTextPath):
        if (capturedText == ""):
            return

        file = open(localTextPath, "w", encoding="utf-8")
        file.write(capturedText)
        file.close()

    #####################################################################################
    #####################################################################################

    def converterProcess(self, q: Queue):
        # This process will continue to receive messages on the queue that are pathnames pointing
        # to the downloaded images. We take one message off the queue at a time and convert the 
        # image file into text. When we receive the "Done" message we will exit.
        while True:
            path_msg = q.get(block=True, timeout=None)
            if (path_msg == "Done"):
                return

            # remove jpg (or png) and add txt
            localTextPath = path_msg[:-3] + "txt"
            if (os.path.exists(localTextPath)):
                continue

            capturedText = self.convertPhotoToText(path_msg)
            self.writeTextToFile(capturedText, localTextPath)

    #####################################################################################
    #####################################################################################

    def run(self):
        self.resultsFolder = Utilities.getMostRecentResultsFolder()
        self.imagesFolder = self.resultsFolder + "images/"
        listOfAllTweets = Utilities.loadTweets(self.resultsFolder)

        # The existing process will download the images and send the file path to a second process
        # which will converting the images to text. Both processes will run in parallel.
        q = Queue()
        p = Process(target=self.converterProcess, args=(q,))
        p.start()
        self.logger.log("second process started pid {}".format(p.pid))

        for line in listOfAllTweets:
            if (line[0] == "#"):
                continue

            tweet = Classes.Tweet()
            tweet.setData(line)
            
            if (tweet.is_ref_tweet):
                continue

            # If any photos were attached to the tweets then grab them. We will not include photos attached to
            # ref tweets. We are mainly trying to get released statements from the Congress members.
            if (tweet.list_of_attachments is not None):
                for i in range(0, len(tweet.list_of_attachments), 2):
                    if (tweet.list_of_attachments[i] == "photo"):
                        url = tweet.list_of_attachments[i+1]
                        localImagePath = self.downloadPhoto(url)
                        # let the second process handle the text conversion by sending it the path of the image
                        q.put(localImagePath)

        

        self.logger.log("Notifying second process that all the images have been downloaded")
        q.put("Done") # One message will be picked up by the second process
        q.put("Done") # The other message will be picked up by the current process

        # when done downloading help the other process to convert the images into text
        self.converterProcess(q)

        p.join()
        self.logger.log("joined with second process")
        
        self.logger.log("removing image files, keeping the text files")
        files = os.listdir(self.imagesFolder)
        for filename in files:
            if (filename[-3:] == "txt"):
                continue
            try:
                path = self.imagesFolder + filename
                os.remove(path)
            except:
                self.logger.log("could not remove image {}".format(path))

    #####################################################################################
    #####################################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    instance = ProcessImages(logger)
    start = time.time()
    instance.run()
    #instance.convertPhotoToText("../output/2021-12-25-Sat/images/FHdHXMKXMAYaKeE.jpg")
    end = time.time()
    duration = (end - start) / 60
    print("duration = {} minutes".format(duration))
    
import sys
sys.path.append("../src")

import os
import pathlib
import distutils.file_util

import Utilities

import ProcessImages
import AnalyzeTweets

###############################################################################
###############################################################################


def getAllResultsFolders():
    OUTPUT_FOLDER = "../output/"
    filesAndFolders = os.listdir(OUTPUT_FOLDER)
    filesAndFolders.sort()
    
    resultsFolders = []
    for item in filesAndFolders:
        if (item == "logs") or (item == "test"):
            continue
        
        p = pathlib.Path(OUTPUT_FOLDER + item)
        if p.is_dir():
            RESULTS_FOLDER = OUTPUT_FOLDER + item + "/"
            resultsFolders.append(RESULTS_FOLDER)
    
    return resultsFolders

###############################################################################
###############################################################################

if __name__ == "__main__":
    logger = Utilities.Logger()
    folders = getAllResultsFolders()

    if (os.path.exists("../output/test/") == False):
        os.mkdir("../output/test/")

    logger.prepareLogFile("../output/test/")

    for folder in folders:
        print("\ntesting folder " + folder)

        step1 = ProcessImages.ProcessImages(logger)
        step1.run(folder)

        step2 = AnalyzeTweets.AnalyzeTweets(logger)
        resultsPath = step2.run(folder, True)

        justTheFileName = resultsPath.rsplit("/", 1)[1]
        distutils.file_util.copy_file(resultsPath, "../output/test/" + justTheFileName)

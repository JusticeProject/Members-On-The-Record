import os
import pathlib
import distutils.file_util

import Utilities

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

logger = Utilities.Logger()
folders = getAllResultsFolders()
instance = AnalyzeTweets.AnalyzeTweets(logger)

Utilities.BYPASS_URL_UNSHORTENER = True
if (os.path.exists("../output/test/") == False):
    os.mkdir("../output/test/")

for folder in folders:
    print("\ntesting folder " + folder)
    resultsPath = instance.run(folder)
    justTheFileName = resultsPath.rsplit("/", 1)[1]
    distutils.file_util.copy_file(resultsPath, "../output/test/" + justTheFileName)


import os
import sys
import shutil

from os.path import isfile, join

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

from configs import getConfigs



if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'verifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs

   recreatePath(app['verified'])

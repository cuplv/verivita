
import os
import sys
import shutil

from os.path import isfile, join

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

from configs import getConfigs


def checkTraces(inputPath, outputPath, json, verifierPath, specPaths):
    print "========\n"
    print "Checking traces in %s" % inputPath

    traces = getFilesInPath(inputPath)
    print traces

    truncPath = outputPath + "/truncated"
    createPathIfEmpty(truncPath)

    exceptPath = outputPath + "/exception"
    createPathIfEmpty(exceptPath)

    goodPath = outputPath + "/good"
    createPathIfEmpty(goodPath)

    uselessPath = outputPath + "/useless"
    createPathIfEmpty(uselessPath)

    unknownPath = outputPath + "/unknown"
    createPathIfEmpty(unknownPath)

    for tr in traces:
        result = runVerifierChecks(tr, json=json, specPaths=specPaths, verifierPath=verifierPath, verbose=configs['verbose'])
        if result == GOODTRACE:
            basePath = goodPath
        elif result == TRUNCTRACE:
            basePath = truncPath
        elif result == EXCEPTTRACE:
            basePath = exceptPath
        elif result == USELESSTRACE:
            basePath = uselessPath
        else:
            basePath = unknownPath
        shutil.copyfile(tr, basePath + '/' + os.path.basename(tr)) 


if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'verifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs

   for name,app in configs['apps'].items():
        
       recreatePath(app['checked'])

       checkTraces(app['input'], app['checked'], app['json'], configs['verifier'], app['specs'])  

       if os.path.exists(app['input'] + "/monkeyTraces"): 
           checkTraces(app['input'] + "/monkeyTraces", app['checked'] + "/monkeyTraces", app['json'], configs['verifier'], app['specs'])

       if os.path.exists(app['input'] + "/manualTraces"): 
           checkTraces(app['input'] + "/manualTraces", app['checked'] + "/manualTraces", app['json'], configs['verifier'], app['specs'])




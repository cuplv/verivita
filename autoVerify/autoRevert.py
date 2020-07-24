
import os
import sys
import shutil

from os.path import isfile, join

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

from configs import getConfigs

def moveTraces(destPath, srcPath, groups):
   print "Moving traces of groups %s from %s to %s" % (','.join(groups), srcPath, destPath)
   for group in groups:
      groupPath = srcPath + "/" + group
      if os.path.exists( groupPath ):
         traces = getFilesInPath( groupPath )
         for trace in traces:
            shutil.move(trace, destPath + "/" + os.path.basename(trace))


if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'verifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs

   for name,app in configs['apps'].items():

       createPathIfEmpty(app['input'])
       moveTraces(app['input'], app['checked'], configs['revertgroups'])

       if os.path.exists(app['checked']+"/monkeyTraces"):
          createPathIfEmpty(app['input']+"/monkeyTraces")
          moveTraces(app['input']+"/monkeyTraces", app['checked']+"/monkeyTraces", configs['revertgroups'])

       if os.path.exists(app['checked']+"/manualTraces"):
          createPathIfEmpty(app['input']+"/manualTraces")
          moveTraces(app['input']+"/manualTraces", app['checked']+"/manualTraces", configs['revertgroups'])



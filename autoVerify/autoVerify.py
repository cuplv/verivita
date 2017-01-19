
import os
import sys
import shutil

from os.path import isfile, join

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

from configs import getConfigs

from verify import runVerify

def verifyTraces(checkedPath, verifiedPath, json, verifierPath, specs, verifyGroups, steps, verbose, timeout):
   
   for group in verifyGroups:

       gCheckedPath  = "%s/%s" % (checkedPath,group)
       gVerifiedPath = "%s/%s" % (verifiedPath,group)
       gBugPath = "%s/%s" % (gVerifiedPath,"bug")
       gOkPath  = "%s/%s" % (gVerifiedPath,"ok")
       gTimedoutPath = "%s/%s" % (gVerifiedPath,"timedout")

       createPathIfEmpty( gVerifiedPath )
       createPathIfEmpty( gBugPath )
       createPathIfEmpty( gOkPath )
       createPathIfEmpty( gTimedoutPath )

       print gCheckedPath

       for tracePath in getFilesInPath(gCheckedPath):
           print tracePath
 
           outcome = runVerify(tracePath, specs, verifierPath, json=json, steps=steps, verbose=verbose, timeout=int(timeout))
           if outcome['bugfound']:
               basePath = gBugPath
           elif outcome['timedout']:
               basePath = gTimedoutPath           
           else:
               basePath = gOkPath
           outputPath = "%s/%s.res" % (basePath,os.path.basename(tracePath).split('.')[0])
            
           with open(outputPath, 'w') as f:
               f.write("=============== Stdout ===============")
               if len(outcome['stdout']) > 0:
                  f.write(outcome['stdout'])
               else:
                  f.write("<No Output>")
               f.write("======================================")
               if len(outcome['stderr']) > 0:
                  f.write("=============== Stderr ===============")
                  f.write(outcome['stderr'])
                  f.write("======================================")
               f.flush()

if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'verifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs


   for name,app in configs['apps'].items():
      recreatePath(app['verified'])
      verifyTraces(app['checked'], app['verified'], app['json'], configs['verifier'], app['specs'], app['verifygroups'], configs['verifysteps'], configs['verbose'], configs['timeout'])
      if os.path.exists(app['checked'] + "/monkeyTraces"): 
          verifyTraces(app['checked'] + "/monkeyTraces", app['verified'] + "/monkeyTraces", app['json'], configs['verifier'], app['specs'], app['verifygroups'], configs['verifysteps'], configs['verbose'], configs['timeout'])





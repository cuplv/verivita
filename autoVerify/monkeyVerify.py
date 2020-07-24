
import sys
import os
import shutil

from random import randint
from subprocess import Popen, PIPE

from verify import runVerify
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE
from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath

from autoTracer.startEmulator import startEmulator, killEmulator
from autoTracer.autoMonkey import autoMonkey

traceRunnerPath = "/home/edmund/workshops/git_workshop/active/TraceRunner-monkey/TraceRunner"

verifierPath = "/home/edmund/workshops/git_workshop/active/callback-verification-auto/callback-verification"

specRepoPath = "/home/edmund/workshops/git_workshop/active/callback-verification-specs/callback-verification/cbverifier/android_specs"

specFiles = "activity.spec,button.spec,countdowntimer.spec,fragment.spec,mediaplayer.spec,fragment_v4.spec,button_backup.spec"

andrJarsPath = "/usr/local/android-sdk/platforms"

tmpPath = "/data/tmp"

if __name__ == "__main__":

   if len(sys.argv) != 5:
      print "usage: python monkeyVerify.py <Path to Android App APK> <Output Path> <Number of Monkey Traces> <BMC Steps>"
      sys.exit(1)

   apkFile = sys.argv[1]
   outputPath = sys.argv[2]
   traces  = sys.argv[3]   
   steps   = sys.argv[4]

   # Start Emulator:
   emulatorName = "pokemon-x86"
   sdcardPath   = "/data/workspace"
   emulatorPort = "5560"
   startEmulator(emulatorName, sdcardPath, devicePort=emulatorPort, noWindow=True)
   
   seed = randint(100,100000)
   currTmpPath = tmpPath + "/%s" % seed

   # Instrumenting App APK
   print "Instrumenting and Resigning App APK: %s" % apkFile
   instProc = Popen(['bash', traceRunnerPath + '/autoTracer/instrument.sh', apkFile, currTmpPath, andrJarsPath], stdout=PIPE, stderr=PIPE)
   outcome,errors = instProc.communicate()
   instrumentedAPKPath = currTmpPath + "/" + os.path.basename(apkFile)
   print "Instrumentation and Resigning completed: %s, %s" % (outcome,errors)
   
   # Running monkey traces
   print "Generating %s traces with monkey" % traces
   numOfMonkeyEvents = 60
   numOfMonkeyTries  = 5
   outputProtoPath   = currTmpPath + "/monkeyTraces"
   createPathIfEmpty( outputProtoPath )
   autoMonkey(instrumentedAPKPath, outputProtoPath, traces, numOfMonkeyEvents, numOfMonkeyTries)
   print "Done generating traces"

   # Killing Emulator
   print "Stopping the emulator .."
   killEmulator(emulatorPort)
   print "Emulator Stopped."

   # Checking Usability of Traces 
   print "Filtering useless Traces ..."
   checkedPath   = currTmpPath + "/checked"
   createPathIfEmpty( checkedPath )
   specs = ":".join(map(lambda s: "%s/%s" % (specRepoPath,s), specFiles.split(',')))
   passed = 0
   failed = 0
   for tracePath in getFilesInPath( outputProtoPath ):
      result = runVerifierChecks(tracePath, json=False, specPaths=specs, verifierPath=verifierPath, verbose=True)
      if result == GOODTRACE:
          print "Good Trace: %s" % tracePath
          passed += 1
          shutil.copyfile( tracePath, checkedPath + "/" + os.path.basename(tracePath) )
      else:
          failed += 1

   print "%s traces are found usable. %s traces will be omitted." % (passed, failed)

   if passed == 0:
       print "Monkey failed to generate usable traces. Please run the script again."
       sys.exit(1)

   # Running verifier on usable traces
   print "Running verifier on usable traces ..."

   resultPath = outputPath + "/results%s" % seed 

   gBugPath = "%s/%s" % (resultPath,"bug")
   gOkPath  = "%s/%s" % (resultPath,"ok")
   gTimedoutPath = "%s/%s" % (resultPath,"timedout")

   recreatePath( resultPath )    
   createPathIfEmpty( gBugPath )
   createPathIfEmpty( gOkPath )
   createPathIfEmpty( gTimedoutPath )

   print "Scanning %s for traces" % checkedPath
   for tracePath in getFilesInPath(checkedPath):
           print "Verifying trace %s" % tracePath
 
           outcome = runVerify(tracePath, specs, verifierPath, json=False, steps=steps, verbose=True, timeout=300)
           if outcome['bugfound']:
               basePath = gBugPath
           elif outcome['timedout']:
               basePath = gTimedoutPath           
           else:
               basePath = gOkPath
           outputPath = "%s/%s.res" % (basePath,os.path.basename(tracePath).split('.')[0])
           print "Verification Done."            

           print "Writing output to %s" % outputPath
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

   print "All Done!"

   

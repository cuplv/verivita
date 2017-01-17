
import cbverifier.traces.ctrace as ct
import matchMsg as mt

from subprocess import Popen, PIPE

try:
    from google.protobuf.json_format import MessageToJson, Parse
except ImportError as e:
    import sys
    sys.stderr.write("We require at least protobuf version 3.0")
    raise e

vPath = '/home/edmund/workshops/git_workshop/active/callback-verification-auto/callback-verification'

specPath = '/home/edmund/workshops/git_workshop/active/callback-verification-specs/callback-verification/cbverifier/android_specs'

allSpecPaths = [ specPath + '/activity.spec'
               , specPath + '/button.spec' 
               , specPath + '/countdowntimer.spec'
               , specPath + '/fragment.spec'
               , specPath + '/mediaplayer.spec' ]


def runCmd(cmd):
   proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
   (stdout, error) = proc.communicate()
   return { 'ret'    : proc.returncode
          , 'haserr' : error == None
          , 'stdout' : stdout if stdout != None else ''
          , 'stderr' : error if error != None else '' }

GOODTRACE    = 0
TRUNCTRACE   = 1
EXCEPTTRACE  = 2
USELESSTRACE = 3
UNKNOWNTRACE = 4

def checkCmdErrorExp(cmd, expMap):
    outcome = runCmd(cmd)

    # print "Return code: %s" % outcome['ret'] + "\n============\n"
    # print "Stdout: %s" % outcome['stdout'] + "\n============\n"
    # print "Stderr: %s" % outcome['stderr'] + "\n============\n"

    for errExp,token in expMap.items():
       if errExp in outcome['stderr']:
           return token
    return None

def runVerifierChecks(tracePath, json=False, specPaths=None, verifierPath=vPath):
    vscript = ['python',verifierPath+'/cbverifier/driver.py']
    if json:
       vscript += ['-f','json']
    if specPaths == None:
       specPaths = ':'.join(allSpecPaths)
    vscript += ['-t',tracePath,'-s',specPaths,'-m','check-trace-relevance']
    outcome = runCmd(vscript)

    expMap = { 'MalformedTraceException'   : TRUNCTRACE
             , 'TraceEndsInErrorException' : EXCEPTTRACE
             , 'NoDisableException'        : USELESSTRACE }

    if not outcome['haserr']:
       # No exceptions throw, return a good trace token
       return GOODTRACE

    for errExp,token in expMap.items():
       if errExp in outcome['stderr']:
           # Matched a known trace exception, return the corresponding token
           return token

    # Unknown exception thrown
    return UNKNOWNTRACE

# '-f','json'

def isTruncatedTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "MalformedTraceException", json=json, specPaths=specPaths)

def isExceptionTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "TraceEndsInErrorException", json=json, specPaths=specPaths)

def isUselessTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "NoDisableException", json=json, specPaths=specPaths)




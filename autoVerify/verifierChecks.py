
import cbverifier.traces.ctrace as ct
# import matchMsg as mt

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
          , 'stdout' : stdout if stdout != None else ''
          , 'stderr' : error if error != None else '' }

def checkCmdErrorExp(cmd, expStr):
    outcome = runCmd(cmd)

    # print "Return code: %s" % outcome['ret'] + "\n============\n"
    # print "Stdout: %s" % outcome['stdout'] + "\n============\n"
    # print "Stderr: %s" % outcome['stderr'] + "\n============\n"

    return expStr in outcome['stderr']        

def runVerifierChecks(tracePath, checkExp, json=False, specPaths=None, verifierPath=vPath):
    vscript = ['python',verifierPath+'/cbverifier/driver.py']
    if json:
       vscript += ['-f','json']
    if specPaths == None:
       specPaths = ':'.join(allSpecPaths)
    vscript += ['-t',tracePath,'-s',specPaths,'-m','check-trace-relevance']
    return checkCmdErrorExp(vscript, checkExp)

# '-f','json'

def isTruncatedTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "MalformedTraceException", json=json, specPaths=specPaths, verifierPath=verifierPath)

def isExceptionTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "TraceEndsInErrorException", json=json, specPaths=specPaths, verifierPath=verifierPath)

def isUselessTrace(tracePath, json=False, specPaths=None, verifierPath=vPath):
    return runVerifierChecks(tracePath, "NoDisableException", json=json, specPaths=specPaths, verifierPath=verifierPath)


testSpec = vPath+'/cbverifier/test/examples/spec2.spec'

TruncTrace   = vPath + '/cbverifier/test/examples/trace_no_exit.json'
ErrTrace     = vPath + '/cbverifier/test/examples/trace_exception.json'
UselessTrace = vPath + '/cbverifier/test/examples/trace1.json'

def test():
    isTrunc  = isTruncatedTrace('/data/callback/output/KistenstapelnDistill/TraceCrash.out')
    isExcept = isExceptionTrace('/data/callback/output/KistenstapelnDistill/TraceCrash.out')
    isUseless = isUselessTrace('/data/callback/output/KistenstapelnDistill/TraceCrash.out')
  
    print "T:%s E:%s U:%s" % (isTrunc,isExcept,isUseless)

    isTrunc  = isTruncatedTrace(TruncTrace, json=True, specPaths=testSpec)
    isExcept = isExceptionTrace(TruncTrace, json=True, specPaths=testSpec)
    isUseless = isUselessTrace(TruncTrace, json=True, specPaths=testSpec)

    print "T:%s E:%s U:%s" % (isTrunc,isExcept,isUseless)

    isTrunc  = isTruncatedTrace(ErrTrace, json=True, specPaths=testSpec)
    isExcept = isExceptionTrace(ErrTrace, json=True, specPaths=testSpec)
    isUseless = isUselessTrace(ErrTrace, json=True, specPaths=testSpec)

    print "T:%s E:%s U:%s" % (isTrunc,isExcept,isUseless)

    isTrunc  = isTruncatedTrace(UselessTrace, json=True, specPaths=testSpec)
    isExcept = isExceptionTrace(UselessTrace, json=True, specPaths=testSpec)
    isUseless = isUselessTrace(UselessTrace, json=True, specPaths=testSpec)

    print "T:%s E:%s U:%s" % (isTrunc,isExcept,isUseless)



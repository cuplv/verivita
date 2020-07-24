
import sys

from utils.fsUtils import runCmd

from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

# -t /home/s/Documents/source/scratch/callback-verification/tests/realApplications/Kistenstapeln-Android/bug/trace_150117_0 -m bmc -s /home/s/Documents/source/callback-verification/cbverifier/android_specs/countdowntimer.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/fragment.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/button.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/fragment_v4.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/mediaplayer.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/activity.spec:/home/s/Documents/source/callback-verification/cbverifier/android_specs/button_backup.spec -k 40 -z -i

# python cbverifier/driver.py -t /data/cuplv/callback-verification-tests/callback-verification/tests/realApplications/Kistenstapeln-Android/bug/trace_150117_0 -m bmc -s /data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/countdowntimer.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/fragment.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/button.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/fragment_v4.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/mediaplayer.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/activity.spec:/data/cuplv/callback-verification-specs/callback-verification/cbverifier/android_specs/button_backup.spec -k 40 -z -i

# python verify.py /data/callback/curated/KistenstapelnDistill/good/TraceNoCrash.out proto /home/edmund/workshops/git_workshop/active/callback-verification-auto/callback-verification /home/edmund/workshops/git_workshop/active/callback-verification-specs/callback-verification/cbverifier/android_specs countdowntimer.spec,fragment.spec,button.spec,fragment_v4.spec,mediaplayer.spec,activity.spec,button_backup.spec

# countdowntimer.spec:fragment.spec:button.spec:fragment_v4.spec:mediaplayer.spec:activity.spec:button_backup.spec

def runVerify(tracePath, specPaths, verifierPath, json=False, technique='bmc', steps='40', verbose=True, timeout=180, nuXMVPath=None):
    vscript = ['python',verifierPath+'/cbverifier/driver.py']
    if json:
       vscript += ['-f','json']
    if nuXMVPath == None:
       vscript += ['-t',tracePath,'-m',technique,'-s',specPaths,'-k',steps,'-z','-i']
    else:
       vscript += ['-t',tracePath,'-s',specPaths,'-m','ic3','--ic3_frames','50','-z','-n',nuXMVPath]
    outcome = runCmd(vscript, verbose=verbose, timeout=timeout)
    if 'Counterexample' in outcome['stdout'] or 'Reached an error' in outcome['stdout']:
        outcome['bugfound'] = True
    else:
        outcome['bugfound'] = False
    return outcome

if __name__ == "__main__":

   if len(sys.argv) != 7:
      print "usage: python verify.py <Path to Trace File> <'proto' or 'json'> <Path to Verifier> <Path to Spec Repository> <Comma Separated List of Spec Files> <Steps>"
      sys.exit(1)

   tracePath = sys.argv[1]
   traceType = sys.argv[2]
   verifierPath = sys.argv[3]
   specPath  = sys.argv[4]
   specFiles = sys.argv[5]
   steps     = sys.argv[6]

   if traceType == 'json':
      json = True
   else:
      json = False

   specs = ":".join(map(lambda s: "%s/%s" % (specPath,s), specFiles.split(',')))
  
   results = runVerify(tracePath, specs, verifierPath, json=json, steps=steps)

   print "Found bug: %s" % results['bugfound']




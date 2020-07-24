
import sys

from verify import runVerify

verifierPath = "/home/edmund/workshops/git_workshop/active/callback-verification-auto/callback-verification"

specRepoPath = "/home/edmund/workshops/git_workshop/active/callback-verification-specs/callback-verification"

specFiles = "activity.spec,button.spec,countdowntimer.spec,fragment.spec,mediaplayer.spec,fragment_v4.spec,button_backup.spec"

if __name__ == "__main__":

   if len(sys.argv) != 3:
      print "usage: python traceVerify.py <Path to Trace File> <BMC Steps>"
      sys.exit(1)

   traceFile = sys.argv[1]   
   steps     = sys.argv[2]

   specs = ":".join(map(lambda s: "%s/%s" % (specRepoPath,s), specFiles.split(',')))

   results = runVerify(traceFile, specs, verifierPath, json=False, steps=steps, timeout=600)

   # print "Found bug: %s" % results['bugfound']

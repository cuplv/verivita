
import sys

from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

if __name__ == "__main__":

   if len(sys.argv) != 6:
      print "usage: python check.py <Path to Trace File> <'proto' or 'json'> <Path to Verifier> <Path to Spec Repository> <Comma Separated List of Spec Files>"
      sys.exit(1)

   tracePath = sys.argv[1]
   traceType = sys.argv[2]
   verifierPath = sys.argv[3]
   specPath     = sys.argv[4]
   specFiles    = sys.argv[5]

   if traceType == 'json':
      json = True
   else:
      json = False

   specs = ":".join(map(lambda s: "%s/%s" % (specPath,s), specFiles.split(',')))
  
   results = runVerifierChecks(tracePath, json=json, specPaths=specs, verifierPath=verifierPath, verbose=True)

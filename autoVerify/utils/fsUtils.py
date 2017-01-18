
import os
import shutil

from os.path import isfile, join

from subprocess import Popen, PIPE

def createPathIfEmpty(path):
    if not os.path.exists(path):
       print "Creating directory: %s" % path
       os.makedirs(path)
    
def removePathIfExists(path):
    if os.path.exists(path):
       print "Deleting directory: %s" % path
       shutil.rmtree(path)

def recreatePath(path):
    removePathIfExists(path)
    createPathIfEmpty(path)

def getFilesInPath(path):
    return [join(path, f) for f in os.listdir(path) if isfile(join(path, f))]

def runCmd(cmd, verbose=False):
   print "Running command: %s" % (' '.join(cmd))
   proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
   (stdout, error) = proc.communicate()

   if verbose:
       print "=============== Stdout ==============="
       if len(stdout) > 0:
           print stdout
       else:
           print "<No Output>"
       print "======================================"
       if len(error) > 0:
          print "=============== Stderr ==============="
          print error
          print "======================================"

   # print "Stdout: %s" % stdout + "\n============\n"
   # print "Stderr: %s" % (error if error != None else '<None>') + "\n============\n"

   return { 'ret'    : proc.returncode
          , 'haserr' : len(error) > 0 
          , 'stdout' : stdout if stdout != None else ''
          , 'stderr' : error if error != None else '' }


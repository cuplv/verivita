
import os
import shutil

from os.path import isfile, join

from subprocess import Popen, PIPE

from threading import Thread

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

def runCmd(cmd, verbose=False, timeout=None):
   print "Running command: %s" % (' '.join(cmd))
   if timeout == None:
       proc = Popen(cmd, stdout=PIPE, stderr=PIPE)
       (stdout, error) = proc.communicate()
       timedout = False
       ret = proc.returncode
   else:
       command = Command(cmd)
       (stdout, error, timedout, ret) = command.run(timeout)

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

   return { 'ret'      : ret
          , 'haserr'   : error != None and ('ERROR' in error or 'Traceback (most recent call last)' in error) 
          , 'timedout' : timedout
          , 'stdout'   : stdout if stdout != None else ''
          , 'stderr'   : error if error != None else '' }

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.stdout = None
        self.stderr = None

    def run(self, timeout):
        def target():
            print 'Thread started with timeout at %s seconds' % timeout
            self.process = Popen(self.cmd, stdout=PIPE, stderr=PIPE)
            (stdout,stderr) = self.process.communicate()
            self.stdout = stdout
            self.stderr = stderr
            print 'Thread finished'

        thread = Thread(target=target)
        thread.start()

        thread.join(timeout)
        timedout = False
        if thread.is_alive():
            print 'Terminating process'
            self.process.terminate()
            thread.join()
            timedout = True
            self.stdout = self.stdout + "\n *** Timedout ***" if self.stdout != None else "\n *** Timedout ***"   
        return (self.stdout, self.stderr, timedout, self.process.returncode)


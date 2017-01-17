
import os
import sys
import shutil

from os.path import isfile, join

from ConfigParser import ConfigParser

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import isTruncatedTrace, isExceptionTrace, isUselessTrace


def get(conf, section, option, default=None):
     if conf.has_option(section, option):
         return conf.get(section, option)
     else:
         return default

def splitClean(path, ls):
    return ':'.join( map(lambda x: "%s/%s" % (path,x.strip()), ls.split(',')) )

# Extract configurations from config file.
def getConfigs(iniFilePath='VerifierConfig.ini'):
    conf = ConfigParser()
    conf.read(iniFilePath)

    vopts = 'verifierOptions'

    inputPath  = get(conf, vopts, 'input', default='/data/callback/output')
    outputPath = get(conf, vopts, 'output', default='/data/callback/curated')

    verifierPath = get(conf, vopts, 'verifierpath', default='')
    specPath = get(conf, vopts, 'specpath', default='')
    specs = get(conf, vopts, 'specs', default='activity.spec,button.spec,countdowntimer.spec,fragment.spec,mediaplayer.spec')
 
    configs = { 'input':inputPath, 'output':outputPath, 'verifier':verifierPath
              , 'specs': splitClean(specPath, specs) }

    apps = {}
    for section in conf.sections():
       if section.startswith("app:"):
           appName = section[4:]

           appSpecPath = get(conf, vopts, 'specpath', default='')
           appSpecs = get(conf, vopts, 'specs', default=None)
           if appSpecs == None:
               appSpecs = splitClean(specPath, specs)
           else:
               appSpecs = splitClean(appSpecPath, appSpecs)

           apps[appName] = { 'input'  : '%s/%s' % (inputPath,appName) 
                           , 'output' : '%s/%s' % (outputPath,appName)
                           , 'specs': appSpecs } 
    configs['apps'] = apps

    return configs


def checkTraces(inputPath, outputPath, verifierPath, specPaths):
    print "========\n"
    print "Checking traces in %s" % inputPath

    traces = getFilesInPath(inputPath)
    print traces

    truncPath = outputPath + "/truncated"
    createPathIfEmpty(truncPath)

    exceptPath = outputPath + "/exception"
    createPathIfEmpty(exceptPath)

    goodPath = outputPath + "/good"
    createPathIfEmpty(goodPath)

    badPath = outputPath + "/bad"
    createPathIfEmpty(badPath)

    for tr in traces:
        if isTruncatedTrace(tr, specPaths=specPaths, verifierPath=verifierPath):
            shutil.copyfile(tr, truncPath + '/' + os.path.basename(tr))
        elif isExceptionTrace(tr, specPaths=specPaths, verifierPath=verifierPath):
            shutil.copyfile(tr, exceptPath + '/' + os.path.basename(tr))
        elif isUselessTrace(tr, specPaths=specPaths, verifierPath=verifierPath):
            shutil.copyfile(tr, badPath + '/' + os.path.basename(tr))
        else:
            shutil.copyfile(tr, goodPath + '/' + os.path.basename(tr))


if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'VerifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs

   onlyfiles = [f for f in os.listdir('/data/callback/output/KistenstapelnDistill') if isfile(join('/data/callback/output/KistenstapelnDistill', f))]

   print onlyfiles

   for name,app in configs['apps'].items():
        
       # robotTraces = getFilesInPath( app['input'] )
       # print robotTraces

       # monkeyTraces = getFilesInPath( '%s/%s' % (app['input'],'monkeyTraces') )
       # print monkeyTraces

       recreatePath(app['output'])

       # recreatePath( '%s/%s' % (app['output'],'monkeyTraces') )

       checkTraces(app['input'], app['output'], configs['verifier'], app['specs'])   
       checkTraces(app['input'] + "/monkeyTraces", app['output'] + "/monkeyTraces", configs['verifier'], app['specs'])


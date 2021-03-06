
import os
import sys
import shutil

from os.path import isfile, join

from ConfigParser import ConfigParser

from utils.fsUtils import createPathIfEmpty, recreatePath, getFilesInPath
from verifierChecks import runVerifierChecks, GOODTRACE, TRUNCTRACE, EXCEPTTRACE, USELESSTRACE, UNKNOWNTRACE

def get(conf, section, option, default=None):
     if conf.has_option(section, option):
         return conf.get(section, option).strip()
     else:
         return default

def splitClean(path, ls):
    return ':'.join( map(lambda x: "%s/%s" % (path,x.strip()), ls.split(',')) )

# Extract configurations from config file.
def getConfigs(iniFilePath='verifierConfig.ini'):
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

           appSpecPath = get(conf, section, 'specpath', default='')
           appSpecs = get(conf, section, 'specs', default=None)
           appJson  = True if get(conf, section, 'json', default='False') == 'True' else False

           print "$$$$$$$$$$$$$$$$$$$$$$$ %s" % appJson

           if appSpecs == None:
               appSpecs = splitClean(specPath, specs)
           else:
               appSpecs = splitClean(appSpecPath, appSpecs)

           apps[appName] = { 'input'  : '%s/%s' % (inputPath,appName) 
                           , 'output' : '%s/%s' % (outputPath,appName)
                           , 'json'   : appJson
                           , 'specs'  : appSpecs } 
    configs['apps'] = apps

    return configs


def checkTraces(inputPath, outputPath, json, verifierPath, specPaths):
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

    uselessPath = outputPath + "/useless"
    createPathIfEmpty(uselessPath)

    unknownPath = outputPath + "/unknown"
    createPathIfEmpty(unknownPath)

    for tr in traces:
        result = runVerifierChecks(tr, json=json, specPaths=specPaths, verifierPath=verifierPath)
        if result == GOODTRACE:
            basePath = goodPath
        elif result == TRUNCTRACE:
            basePath = truncPath
        elif result == EXCEPTTRACE:
            basePath = exceptPath
        elif result == USELESSTRACE:
            basePath = uselessPath
        else:
            basePath = unknownPath
        shutil.copyfile(tr, basePath + '/' + os.path.basename(tr)) 


if __name__ == "__main__":

   if len(sys.argv) > 1:
       iniFilePath = sys.argv[1]
   else:
       iniFilePath = 'verifierConfig.ini'
  
   configs = getConfigs(iniFilePath)

   print configs

   # onlyfiles = [f for f in os.listdir('/data/callback/output/KistenstapelnDistill') if isfile(join('/data/callback/output/KistenstapelnDistill', f))]

   # print onlyfiles

   for name,app in configs['apps'].items():
        
       # robotTraces = getFilesInPath( app['input'] )
       # print robotTraces

       # monkeyTraces = getFilesInPath( '%s/%s' % (app['input'],'monkeyTraces') )
       # print monkeyTraces

       recreatePath(app['output'])

       # recreatePath( '%s/%s' % (app['output'],'monkeyTraces') )

       checkTraces(app['input'], app['output'], app['json'], configs['verifier'], app['specs'])  
       if os.path.exists(app['input'] + "/monkeyTraces"): 
           checkTraces(app['input'] + "/monkeyTraces", app['output'] + "/monkeyTraces", app['json'], configs['verifier'], app['specs'])


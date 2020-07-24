

from ConfigParser import ConfigParser

import os

def get(conf, section, option, default=None):
     if conf.has_option(section, option):
         return conf.get(section, option).strip()
     else:
         return default

def splitClean(path, ls):
    return ':'.join( map(lambda x: "%s/%s" % (path,x.strip()), ls.split(',')) )

def splitIt(ls):
    return map(lambda x: x.strip(), ls.split(','))

def findAll(path, ext=None):
   allfiles = []
   for root, dirs, files in os.walk(path):
       for file in files:
           if ext == None or file.endswith("." + ext):
                allfiles.append(os.path.join(root, file))
   return allfiles

def retrieveSpecParams(conf, section, specPathParam, specsParam, defaultSpecPath=None, defaultSpecs=None):
   specPath = get(conf, section, specPathParam, default=defaultSpecPath)
   specs    = get(conf, section, specsParam, default=defaultSpecs)
   specPaths = []
   if specPath != None and specs != None:
      specFiles = splitIt(specs)
      if 'ALL' not in specFiles:
         specPaths = map( lambda x: "%s/%s" % (specPath,x), specFiles)
      else:
         specPaths = findAll(specPath, ext="spec")
      # specPaths = ':'.join(specPaths)
   return (specPath,specs,specPaths)

# Extract configurations from config file.
def getConfigs(iniFilePath='verifierConfig.ini'):
    conf = ConfigParser()
    conf.read(iniFilePath)

    vopts = 'verifierOptions'

    verbose    = True if get(conf, vopts, 'verbose', default='False') == 'True' else False
    inputPath  = get(conf, vopts, 'input', default='/data/callback/output')
    processedPath = get(conf, vopts, 'processed', default='/data/callback/processed')
    checkedPath = get(conf, vopts, 'checked', default='/data/callback/checked')
    verifiedPath = get(conf, vopts, 'verified', default='/data/callback/verified')
    timeout = get(conf, vopts, 'timeout', default='300')
    verifierPath = get(conf, vopts, 'verifierpath', default='')
    nuXmvPath = get(conf, vopts, 'nuxmvpath', default=None)

    enSpecPath,enSpecs,enSpecPaths = retrieveSpecParams(conf, vopts, 'enablespecpath', 'enablespecs')
    alSpecPath,alSpecs,alSpecPaths = retrieveSpecParams(conf, vopts, 'allowspecpath', 'allowspecs')

    specPath = get(conf, vopts, 'specpath', default='')
    specs = get(conf, vopts, 'specs', default='activity.spec,button.spec,countdowntimer.spec,fragment.spec,mediaplayer.spec')
 
    verifyGroups = get(conf, vopts, 'verifygroups', default='good,useless')
    verifySteps  = get(conf, vopts, 'verifysteps', default='40')

    ropts = 'revertOptions'

    revertgroups = splitIt( get(conf, ropts, 'groups', default='good') )
    if 'ALL' in revertgroups:
       revertgroups = ['truncated','exception','good','useless','unknown']
    
    configs = { 'verbose':verbose, 'input':inputPath, 'processed':processedPath 
              , 'checked':checkedPath, 'verified':verifiedPath, 'verifier':verifierPath
              , 'specs': ':'.join(enSpecPaths + alSpecPaths) # splitClean(specPath, specs)
              , 'enspecs': ':'.join(enSpecPaths), 'alspecs': ':'.join(alSpecPaths)
              , 'verifygroups':splitIt(verifyGroups), 'verifysteps':verifySteps, 'timeout':timeout
              , 'revertgroups':revertgroups, 'nuxmv':nuXmvPath }

    apps = {}
    for section in conf.sections():
       if section.startswith("app:"):
           appName = section[4:]

           _,_,appEnSpecPaths = retrieveSpecParams(conf, section, 'enablespecpath', 'enablespecs'
                                                  ,defaultSpecPath=enSpecPath
                                                  ,defaultSpecs=enSpecs)
           _,_,appAlSpecPaths = retrieveSpecParams(conf, section, 'allowspecpath', 'allowspecs'
                                                  ,defaultSpecPath=alSpecPath
                                                  ,defaultSpecs=alSpecs)

           appSpecPath = get(conf, section, 'specpath', default='')
           appSpecs = get(conf, section, 'specs', default=None)

           appJson  = True if get(conf, section, 'json', default='False') == 'True' else False
           appVerifyGroups = get(conf, section, 'verifygroups', default=None)

           if appSpecs == None:
               appSpecs = splitClean(specPath, specs)
           else:
               appSpecs = splitClean(appSpecPath, appSpecs)

           if appVerifyGroups == None:
               appVerifyGroups = splitIt(verifyGroups)
           else:
               appVerifyGroups = splitIt(appVerifyGroups)

           

           apps[appName] = { 'input'  : '%s/%s' % (inputPath,appName) 
                           , 'processed' : '%s/%s' % (processedPath,appName)
                           , 'checked' : '%s/%s' % (checkedPath,appName)
                           , 'verified' : '%s/%s' % (verifiedPath,appName)
                           , 'json'   : appJson
                           , 'specs'  : ':'.join(appEnSpecPaths + appAlSpecPaths) # appSpecs
                           , 'enspecs': ':'.join(appEnSpecPaths)
                           , 'alspecs': ':'.join(appAlSpecPaths)
                           , 'verifygroups' : appVerifyGroups } 
    configs['apps'] = apps

    return configs




from ConfigParser import ConfigParser

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

    verbose    = True if get(conf, vopts, 'verbose', default='False') == 'True' else False
    inputPath  = get(conf, vopts, 'input', default='/data/callback/output')
    checkedPath = get(conf, vopts, 'checked', default='/data/callback/checked')
    verifiedPath = get(conf, vopts, 'verified', default='/data/callback/verified')

    verifierPath = get(conf, vopts, 'verifierpath', default='')
    specPath = get(conf, vopts, 'specpath', default='')
    specs = get(conf, vopts, 'specs', default='activity.spec,button.spec,countdowntimer.spec,fragment.spec,mediaplayer.spec')
 
    configs = { 'verbose':verbose, 'input':inputPath, 'checked':checkedPath, 'verified':verifiedPath
              , 'verifier':verifierPath, 'specs': splitClean(specPath, specs) }

    apps = {}
    for section in conf.sections():
       if section.startswith("app:"):
           appName = section[4:]

           appSpecPath = get(conf, section, 'specpath', default='')
           appSpecs = get(conf, section, 'specs', default=None)
           appJson  = True if get(conf, section, 'json', default='False') == 'True' else False

           if appSpecs == None:
               appSpecs = splitClean(specPath, specs)
           else:
               appSpecs = splitClean(appSpecPath, appSpecs)

           apps[appName] = { 'input'  : '%s/%s' % (inputPath,appName) 
                           , 'checked' : '%s/%s' % (checkedPath,appName)
                           , 'verified' : '%s/%s' % (verifiedPath,appName)
                           , 'json'   : appJson
                           , 'specs'  : appSpecs } 
    configs['apps'] = apps

    return configs


import argparse
import os
#read results and split by app instead of trace

class ResultCount:
    def __init__(self):
        self.safe = 0
        self.unsafe = 0
        self.read_error = 0
        self.timeout = 0
        self.total = 0
    def update(self, resultline):
        if "result Safe" in resultline :
            self.safe += 1
            self.total +=1
        elif "result Unsafe" in resultline:
            self.unsafe += 1
            self.total +=1
        elif "result ReadError" in resultline:
            self.read_error += 1
        elif "time Timeout" in resultline:
            self.timeout += 1
            self.total +=1
    def toString(self):
        return "safe: %i, unsafe: %i, readerr: %i, timeout %i" % (self.safe, self.unsafe, self.read_error, self.timeout)
def pathToAppId(outpath, alias_map):
    outpath_pieces = outputpath.split("/")
    if len(outpath_pieces) > 3:
        appname = outpath_pieces[-3]
    else:
        raise Exception("unparseable path")
    if appname in alias_map:
        return alias_map[appname]
    else: return appname

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sort trace by message ID')
    parser.add_argument('--dir', type=str,
                        help="directory of files to process",required=True)
    parser.add_argument('--apps_list', type=str,
                        help="text file to output list of all apps")
    parser.add_argument('--blacklist', type=str,
                        help="remove apps from results, one per line in file")
    parser.add_argument('--app_alias', type=str,
                        help="file with each line representing the possible aliases for an app separated by commas")

    args = parser.parse_args()

    toProcess = [ x for x in os.listdir(args.dir) if x.endswith("txt")]

    app_blacklist = set()
    if args.blacklist is not None:
        with open(args.blacklist, "r") as ins:
            for line in ins:
                app_blacklist.add(line.strip())

    alias_map = dict() # match this string -> apply it to this string
    if args.app_alias is not None:
        with open(args.app_alias,'r') as ins:
            for line in ins:
                splitline = line.split(",")
                if len(splitline) > 1:
                    replacewith = splitline[0].strip()
                    for mapfrom in splitline[1:]:
                        alias_map[mapfrom.strip()] = replacewith.strip()

    results = {}
    for fname in toProcess:
        f = open(os.path.join(args.dir, fname))
        lines = f.readlines()
        resultlines = [line for line in lines if not line.strip().startswith("#")]
        appResults = {}
        if fname != "summary.txt":
            for resultline in resultlines:
                splitline = resultline.split(" ")
                outputpath = splitline[0]
                # try:
                appname = pathToAppId(outputpath, alias_map)
                if appname not in app_blacklist:
                    if appname not in appResults:
                        appResults[appname] = ResultCount()
                        appResults[appname].update(resultline)
                    else:
                        appResults[appname].update(resultline)
                # except:
                #     print "Unparsable line: %s" % resultline
            results[fname] = appResults

    just_disallow = [x for x in results if "_justdisallow_" in x]
    lifecycle_init = [x for x in results if ("_lifecycle_init_" in x)]
    lifecycle = [x for x in results if ("_lifecycle_" in x) and (not "_lifecycle_init_" in x)]
    lifestate = [x for x in results if "_lifestate_" in x]

    allApps = set()
    for result in results:
        print "-------------------------------------------"
        print "filename: %s , length: %i" % (result, len(results[result]))
        alarmingApps = set()
        totAlarmTraces = 0
        totTraces = 0
        totApps = 0
        timeoutApps = set()
        timeoutTraces = 0
        for appResult in results[result]:
            allApps.add(appResult)
            c = results[result][appResult]
            totTraces += c.total
            totApps +=1
            if c.timeout > 0:
                timeoutApps.add(appResult)
            timeoutTraces += c.timeout
            if c.safe > 0 or c.unsafe > 0:
                print "    app: %s" % appResult
                print c.toString()
                if c.unsafe > 0:
                    totAlarmTraces += c.unsafe
                    alarmingApps.add(appResult)
        print "number of alarming apps: %i" % len(alarmingApps)
        print "number of alarming traces: %i" % totAlarmTraces
        print "number of timeout apps: %i" % len(timeoutApps)
        print "number of timeout traces: %i" % timeoutTraces
        print "trace alarms+timeouts %i" % (timeoutTraces + totAlarmTraces)
        print "app alarms + timeouts %i" % (len(alarmingApps.union(timeoutApps)))
        print "total number of traces: %i" % totTraces
        print "total number of apps %i" % totApps


    # justdisallow
    just_disallow_alarm_apps = set()
    for property in just_disallow:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0:
                just_disallow_alarm_apps.add(app)
    print "just disallow alarming apps total: %i" % len(just_disallow_alarm_apps)

    lifecycle_alarm_apps = set()
    for property in lifecycle:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0:
                lifecycle_alarm_apps.add(app)
    print "lifecycle alarming apps total: %i" % len(lifecycle_alarm_apps)

    lifecycle_init_alarm_apps = set()
    for property in lifecycle_init:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0:
                lifecycle_init_alarm_apps.add(app)

    print "lifecycle init alarming apps totoal: %i" % len(lifecycle_init_alarm_apps)

    lifestate_alarm_apps = set()
    for property in lifestate:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0:
                lifestate_alarm_apps.add(app)

    print "lifestate alarming apps totoal: %i" % len(lifestate_alarm_apps)

    # lifecycle_init

    #lifecycle
    print "total apps: %i" % len(allApps)

    if args.apps_list is not None:
        all_apps_output = open(args.apps_list,'w')
        for app in allApps:
            all_apps_output.write(app + "\n")
        all_apps_output.close()


#    results_split = {}
#    for fname in just_disallow:
#        bucket = fname.split("_justdisallow_")[0]
#        if bucket in results_split:
#            pass #@TODO: finish me
#
#    for test in results:
#        print "=====test   %s=====" %test
#
#    pass


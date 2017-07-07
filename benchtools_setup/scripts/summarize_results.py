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
        else:
            self.timeout += 1
            self.total +=1
    def toString(self):
        return "safe: %i, unsafe: %i, readerr: %i, timeout %i" % (self.safe, self.unsafe, self.read_error, self.timeout)
def pathToAppId(outpath, alias_map):
    outpath_pieces = outpath.split("/")
    if outpath_pieces[5] == "monkey_traces": #TODO: split data not on file path, this is a bad way to do it
        pass
        appname = outpath_pieces[-3]
    else:
        if len(outpath_pieces) > 3:
            appname = outpath_pieces[-4]
            if appname.isdigit():
                appname = outpath_pieces[-5]
        else:
            raise Exception("unparseable path")
    if appname in alias_map:
        return alias_map[appname]
    else:
        return appname

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
    set_alarmingTraces = set()
    set_timeoutTraces = set()
    set_safeTraces = set()
    results = {}
    level_alarming_traces = {"just_disallow": set(), "lifecycle": set(), "lifestateva0": set(), "lifestateva1": set()}
    level_timeout_traces = {"just_disallow": set(), "lifecycle": set(), "lifestateva0": set(), "lifestateva1": set()}
    level_safe_traces = {"just_disallow": set(), "lifecycle": set(), "lifestateva0": set(), "lifestateva1": set()}
    average_safe_trace_runtime = {"just_disallow": [], "lifecycle": [], "lifestateva0": [], "lifestateva1": []}
    for fname in toProcess:
        f = open(os.path.join(args.dir, fname))
        lines = f.readlines()
        resultlines = [line for line in lines if not line.strip().startswith("#")]
        appResults = {}
        if fname != "summary.txt":
            level = ""
            if "_just_disallow" in fname:
                level = "just_disallow"
            if "_lifestate_va0" in fname:
                level = "lifestateva0"
            if "_lifestate_va1" in fname:
                level = "lifestateva1"
            if "_lifecycle" in fname:
                level = "lifecycle"


            for resultline in resultlines:
                splitline = resultline.split(" ")
                outputpath = splitline[0]
                # try:


                appname = pathToAppId(outputpath, alias_map)
                if appname not in app_blacklist:
                    if ("result ?" in resultline) or ("result Timeout" in resultline) or ("result ReadError" in resultline):
                        set_timeoutTraces.add(outputpath)
                        level_timeout_traces[level].add(outputpath)
                    elif ("result Safe" in resultline):
                        set_safeTraces.add(outputpath)
                        level_safe_traces[level].add(outputpath)
                        average_safe_trace_runtime[level].append(float(splitline[4]))
                    elif ("result Unsafe" in resultline):
                        set_alarmingTraces.add(outputpath)
                        level_alarming_traces[level].add(outputpath)
                    else:
                        raise Exception("unparseable line")
                    if appname not in appResults:
                        appResults[appname] = ResultCount()
                        appResults[appname].update(resultline)
                    else:
                        appResults[appname].update(resultline)
                # except:
                #     print "Unparsable line: %s" % resultline
            results[fname] = appResults

    just_disallow = [x for x in results if "_just_disallow" in x]
    #lifecycle_init = [x for x in results if ("_lifecycle_init_" in x)]
    lifecycle = [x for x in results if ("_lifecycle" in x) and (not "_lifecycle_init_" in x)]
    lifestateva0 = [x for x in results if "_lifestate_va0" in x]
    lifestateva1 = [x for x in results if "_lifestate_va1" in x]

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


    for i in xrange(3):
        print ""

    print "===full trace summary=="

    print "total alarming traces: %i" % len(set_alarmingTraces)
    print "total safe traces: %i" % len(set_safeTraces)
    print "total timeout traces: %i" % len(set_timeoutTraces)
    print "total alarm and timeout: %i" % len(set_alarmingTraces.union(set_timeoutTraces))
    print "total traces in summary sets: %i" % len(set_timeoutTraces.union(set_alarmingTraces.union(set_safeTraces)))


    print ""
    print "===level trace summary==="
    for level in level_alarming_traces:
        print "--%s" % level
        print "    alarming traces: %i" % len(level_alarming_traces[level])
        print "    safe traces: %i" % len(level_safe_traces[level])
        print "    timeout traces: %i" % len(level_timeout_traces[level])
        print "    timeout and alarm traces: %i" % len(level_timeout_traces[level].union(level_alarming_traces[level]))
        print "    total traces in summary: %i" % len(level_safe_traces[level].union(level_alarming_traces[level].union(level_timeout_traces[level])))


    print ""
    print "===app alarm summary==="


    # justdisallow
    just_disallow_alarm_apps = set()
    for property in just_disallow:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0 or counts.timeout > 0:
                just_disallow_alarm_apps.add(app)
    print "just disallow alarming apps total: %i" % len(just_disallow_alarm_apps)

    lifecycle_alarm_apps = set()
    for property in lifecycle:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0 or counts.timeout > 0:
                lifecycle_alarm_apps.add(app)
    print "lifecycle alarming apps total: %i" % len(lifecycle_alarm_apps)

    lifestate_va0_alarm_apps = set()
    for property in lifestateva0:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0 or counts.timeout > 0:
                lifestate_va0_alarm_apps.add(app)

    print "lifestate va0 alarming apps totoal: %i" % len(lifestate_va0_alarm_apps)

    lifestate_alarm_apps = set()
    for property in lifestateva1:
        app_results = results[property]
        for app in app_results:
            counts = app_results[app]
            if counts.unsafe > 0 or counts.timeout > 0:
                lifestate_alarm_apps.add(app)

    print "lifestate va1 alarming apps totoal: %i" % len(lifestate_alarm_apps)

    # lifecycle_init

    #lifecycle
    print "total apps: %i" % len(allApps)

    if args.apps_list is not None:
        all_apps_output = open(args.apps_list,'w')
        for app in allApps:
            all_apps_output.write(app + "\n")
        all_apps_output.close()


    print ""
    print "===Average Runtimes===="
    for level in average_safe_trace_runtime:
        print "--%s" %level
        l = average_safe_trace_runtime[level]
        if(len(l) > 0):
            print "    avg: %f" % (sum(l)/len(l))
        else:
            print "    empty"


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


import argparse
import os
#read results and split by app instead of trace

class ResultCount:
    def __init__(self):
        self.safe = 0
        self.unsafe = 0
        self.read_error = 0
        self.timeout = 0
    def update(self, resultline):
        if "result Safe" in resultline :
            self.safe += 1
        elif "result Unsafe" in resultline:
            self.unsafe += 1
        elif "result ReadError" in resultline:
            self.read_error += 1
        elif "time Timeout" in resultline:
            self.timeout += 1
    def toString(self):
        return "safe: %i, unsafe: %i, readerr: %i, timeout %i" % (self.safe, self.unsafe, self.read_error, self.timeout)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sort trace by message ID')
    parser.add_argument('--dir', type=str,
                        help="directory of files to process",required=True)

    args = parser.parse_args()

    toProcess = [ x for x in os.listdir(args.dir) if x.endswith("txt")]

    justDisallowAlarmingTraces = set()
    lifecycleAlarmingTraces = set()
    lifestateAlarmingTraces = set()
    results = {}
    for fname in toProcess:
        f = open(os.path.join(args.dir, fname))
        lines = f.readlines()
        resultlines = [line for line in lines if not line.strip().startswith("#")]
        appResults = {}
        for resultline in resultlines:
            splitline = resultline.split(" ")
            outputpath = splitline[0]
            outpath_pieces = outputpath.split("/")
            if len(outpath_pieces) > 3:
                appname = outpath_pieces[-3]

                result = ""

                if "result Unsafe" in resultline:
                    if "lifecycle" in fname:
                        lifecycleAlarmingTraces.add(resultline)
                    if "lifestate" in fname:
                        lifestateAlarmingTraces.add(resultline)
                    if "justdisallow" in fname:
                        justDisallowAlarmingTraces.add(resultline)

                   

                if appname not in appResults:
                    appResults[appname] = ResultCount()
                    appResults[appname].update(resultline)
                else:
                    appResults[appname].update(resultline)
            else:
                print "Unparsable line: %s" % resultline
        results[fname] = appResults

    just_disallow = [x for x in results if "_justdisallow_" in x]
    lifecycle = [x for x in results if "_lifecycle_" in x]
    lifestate = [x for x in results if "_lifestate_" in x]

    allApps = set()
    justDisallowAlarmingApps = set()
    lifecycleAlarmingApps = set()
    lifestateAlarmingApps = set()
    for result in results:
        print "-------------------------------------------"
        print "filename: %s , length: %i" % (result, len(results[result]))
        alarmingApps = []
        totAlarmTraces = 0
        for appResult in results[result]:
            allApps.add(appResult)
            c = results[result][appResult]
            if c.safe > 0 or c.unsafe > 0:
                print "    app: %s" % appResult
                print c.toString()
                if c.unsafe > 0:
                    totAlarmTraces += c.unsafe
                    alarmingApps.append(appResult)
                    if "lifecycle" in result:
                        lifecycleAlarmingApps.add(appResult)
                    if "lifestate" in result:
                        lifestateAlarmingApps.add(appResult)
                    if "justdisallow" in result:
                        justDisallowAlarmingApps.add(appResult)

        print "number of alarming apps: %i" % len(alarmingApps)
        print "number of alarming traces: %i" % totAlarmTraces
    print "==============================="
    print "total apps: %i" % len(allApps)
    print "unique justdisallow alarming apps: %i" % len(justDisallowAlarmingApps)
    for a in justDisallowAlarmingApps:
        print "    %s" % a
    print "unique lifecycle alarming apps: %i" % len(lifecycleAlarmingApps)
    for a in lifecycleAlarmingApps:
        print "    %s" % a
    print "unique lifestate alarming apps: %i" % len(lifestateAlarmingApps)
    for a in lifestateAlarmingApps:
        print "    %s" % a
    print "justDisallowAlarmingTraces: %i" % len(justDisallowAlarmingTraces)
    print "lifecycleAlarmingTraces: %i" % len(lifecycleAlarmingTraces)
    print "lifestateAlarmingTraces: %i" % len(lifestateAlarmingTraces)
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


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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sort trace by message ID')
    parser.add_argument('--dir', type=str,
                        help="directory of files to process",required=True)

    args = parser.parse_args()

    toProcess = [ x for x in os.listdir(args.dir) if x.endswith("txt")]

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
            appname = outpath_pieces[-3]

            result = ""



            if appname not in appResults:
                appResults[appname] = ResultCount()
                appResults[appname].update(resultline)
            else:
                appResults[appname].update(resultline)
        results[fname] = appResults

    just_disallow = [x for x in results if "_justdisallow_" in x]
    lifecycle = [x for x in results if "_lifecycle_" in x]
    lifestate = [x for x in results if "_lifestate_" in x]


    results_split = {}
    for fname in just_disallow:
        bucket = fname.split("_justdisallow_")[0]
        if bucket in results_split:
            pass #@TODO: finish me

    for test in results:
        print "=====test   %s=====" %test

    pass


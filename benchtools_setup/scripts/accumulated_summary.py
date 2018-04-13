import summarize_results
import argparse
import os
import tabulate
import pandas


FILE_SUFFIX = ".tar.bz2.txt"
#This is a cleaned up version of summarize_results which also prints a plot of how many have been proven by a given time
PRECISION_LEVELS = ["just_disallow","lifecycle","lifestate_va0","lifestate_va1"]
class ResultsFile:
    def __init__(self, fname):
        self.origional_fname = fname
        #parse object/method
        filename_split = fname.split("_")
        assert(filename_split[0] == "results")
        self.method = filename_split[1]
        #parse level
        if filename_split[2] == "just":
            self.precision_level = "just_disallow"
            self.precision_number = 0
        elif filename_split[2] == "lifecycle" + FILE_SUFFIX:
            self.precision_level = "lifecycle"
            self.precision_number = 1
        elif filename_split[2] == "lifestate":
            if filename_split[3] == "va0" + FILE_SUFFIX:
                self.precision_level = "lifestate_va0"
                self.precision_number = 2
            elif filename_split[3] == "va1" + FILE_SUFFIX:
                self.precision_level = "lifestate_va1"
                self.precision_number = 3
            else:
                raise Exception("parse level exception")
        else:
            raise Exception("parse level exception")

class ResultLine:
    #line: line created by benchtools
    #alias_map Dictionary[String,String]: map from directory names to actual name
    #    (use this to merge data from one apps' traces being in different dirs)
    def __init__(self, line, alias_map):
        self.origional_line = line
        split_line = line.split(" ")
        self.trace_path = split_line[0]
        assert("/" in self.trace_path)
        assert(self.trace_path.endswith("repaired"))
        assert(split_line[1] == "result")
        assert(split_line[3] == "time")
        pass
        #appname
        self.app_name = summarize_results.pathToAppId(self.trace_path, alias_map)
        #proof status
        self.proof_status = split_line[2]
        #time
        time_result = split_line[4]
        if time_result != "Timeout":
            self.time = float(time_result)
        else:
            self.time = float("inf")
            self.proof_status = "Timeout"


#ignore lines at top of results file with comments
def ignoreLineInResultFile(line):
    stripped_line = line.strip()
    if line.startswith("#"):
        return True
    return False

def loadDirectory(directory, alias_map):
    file_map = {} #mapping from a filename to a set of ResultLine objects Dictionary[String,(ResultsFile,List[ResultLine])]
    toProcess = [ x for x in os.listdir(args.dir) if x.endswith(FILE_SUFFIX)]
    for fname in toProcess:
        f = open(os.path.join(directory,fname), 'r')
        lines = f.readlines()
        file_map[fname] = (ResultsFile(fname), [])
        for line in lines:
            if not ignoreLineInResultFile(line):
                resultLine = ResultLine(line, alias_map)
                resultsFile,list_resultLine = file_map[fname]
                list_resultLine.append(resultLine)

    return file_map

def loadAliasMap(alias_file):
    alias_map = dict() # match this string -> apply it to this string
    # alias_file = args.app_alias
    if alias_file is not None:
        with open(alias_file, 'r') as ins:
            for line in ins:
                splitline = line.split(",")
                if len(splitline) > 1:
                    replacewith = splitline[0].strip()
                    for mapfrom in splitline[1:]:
                        alias_map[mapfrom.strip()] = replacewith.strip()
    return alias_map

# Return buckets with lowest level required for proof
def getBuckets(file_map):
    safe = {"lifestate_va0":[],"lifestate_va1":[], "lifecycle":[], "just_disallow":[]} #map from proof level to
    unsafe = {"lifestate_va0":[],"lifestate_va1":[], "lifecycle":[], "just_disallow":[]} #map from proof level to
    for f in file_map:
        file_result = file_map[f]
        file_object = file_result[0]
        for result in file_result[1]:
            if result.proof_status == "Safe":
                safe[file_object.precision_level].append((file_object,result))
            if result.proof_status == "Unsafe":
                unsafe[file_object.precision_level].append((file_object,result))
    return safe,unsafe

#Create data files for gnu plot to plot the number of proved traces over time
def gnuplotTime(loadedResults, sample_time_seconds, outdir):
    safe,unsafe = getBuckets(loadedResults)

    for safelevel in safe:
        f = open(os.path.join(outdir, safelevel + ".data"), 'w')


        cbuckets = safe[safelevel]
        sorted_time_safelevel = sorted(cbuckets, key=lambda x: x[1].time)
        for proof in sorted_time_safelevel:
            f.write(proof[1].trace_path + " " + proof[1].proof_status + " " + str(proof[1].time) + "\n")
        f.close()

    #calculate the cumulated proof time
    cum_proof_time = {} #map from trace path to [(proof_number, accumulated time)*]
    for safelevel in safe:
        result_list = safe[safelevel] + unsafe[safelevel]
        for proof in result_list:
            path = proof[1].trace_path
            precision_number = proof[0].precision_number
            disallow_method = proof[0].method
            time = proof[1].time
            proof_status = proof[1].proof_status
            result_key = (disallow_method, path)
            if result_key in cum_proof_time:
                cum_proof_time[result_key].append((proof_status, precision_number, time))
            else:
                cum_proof_time[result_key] = [(proof_status, precision_number, time)]

    # calculate the cumulative time for this added to all lower levels
    accum_proof_time = []

    min_proof_time = []
    for key in cum_proof_time:
        unsorted = cum_proof_time[key]
        #get minimum proof level
        proof_list = sorted([f for f in unsorted if f[0] == "Safe"], key=lambda x:x[1])
        if len(proof_list) > 0:
            min_proof = proof_list[0]
            min_proof_level = min_proof[1]

            #sum all unsafe with lower proof numbers
            unsafe_list = sorted([f for f in unsorted if (isunsafe(f[0])) and f[1] < min_proof_level], key=lambda x:x[1])

            unsafe_time = 0
            for unsafe in unsafe_list:
                unsafe_time += unsafe[2]
            accum_proof_time.append((key[1], " Safe ", str(unsafe_time + min_proof[2])))


    sorted_cumulative_times = sorted(accum_proof_time, key=lambda x: float(x[2]))
    f = open(os.path.join(outdir, "min_level.data"),'w') # cumulative time for this added to all lower levels
    for line in sorted_cumulative_times:
        f.write(line[0] + line[1] + line[2] + "\n")
    f.close()



def isunsafe(trace):
    if(type(trace) == list):
        assert(trace[1].proof_status in {"Unsafe","Safe","Timeout", "ReadError","?"})
        if trace[1].proof_status in {"?"}:
            print ""
            print "unknown, manaully evaluate:"
            print "==========================="
            print "filename:"
            print trace[0].origional_fname
            print "path:"
            print trace[1].trace_path
        return trace[1].proof_status in {"Unsafe","Timeout","?"} #We are ignoring read errors since they are bad traces
    elif(isinstance(trace,ResultLine)):
        return trace.proof_status in {"Unsafe","Timeout","?"}
    else:
        raise Exception("bad type in isUnsafe")

def genTable(loadedResults, outdir):
    column_names = []
    properties = set()
    for precision_level in PRECISION_LEVELS:
        for sc in ["-trace", "-app", "-perc"]:
            level_sc = precision_level + sc
            column_names.append(level_sc)
    for result_filename in loadedResults:
        properties.add(loadedResults[result_filename][0].method)

    properties_list = sorted([p for p in properties])
    df = pandas.DataFrame(index = properties_list, columns=column_names)

    #create mapping from property to list of results at each level
    property_result_map = {}
    for prop in properties_list:
        property_result_map[prop] = [set() for f in PRECISION_LEVELS]

    for result_filename in loadedResults:
        result_file = loadedResults[result_filename][0]
        result_list = loadedResults[result_filename][1]
        property = result_file.method
        precision_level = result_file.precision_level
        precision_number = result_file.precision_number
        for result in result_list:
            property_result_map[property][precision_number].add((result_file,result))


        #df.set_value('C', 'x', 10)


        pass

    result_list = -1
    for property in property_result_map:
        results_list = property_result_map[property]
        for level in xrange(len(results_list)):
            unsafe_trace_count = 0
            unsafe_app_set = set()
            iter_level_list = results_list[level].copy()
            for result in iter_level_list:
                property = result[0].method
                trace_path = result[1].trace_path
                lowerlevels = range(level)
                #check if a lower level proved this result
                # proved_inlowerlevel = False
                for lowerlevel in lowerlevels:
                    lowerlevelset = results_list[lowerlevel]
                    #TODO: if result is proved in lower level then remvoe it from results_list
                    for lower_result in lowerlevelset:
                        pass
                        if lower_result[1].trace_path == trace_path and lower_result[1].proof_status == "Safe":
                            results_list[level].remove(result)

    #populate dataframe
    for property in property_result_map:
        results_list = property_result_map[property]
        for level in xrange(len(results_list)):

            unsafe_trace_list = [ trace for trace in results_list[level] if isunsafe(trace)]
            unsafe_app_set = set([trace[1].app_name for trace in unsafe_trace_list])

            unsafe_trace_count = len(unsafe_trace_list)
            unsafe_app_count = len(unsafe_app_set)
            df.set_value(property,PRECISION_LEVELS[level] + "-trace", unsafe_trace_count)
            df.set_value(property,PRECISION_LEVELS[level] + "-app", unsafe_app_count)

    print tabulate.tabulate(df, headers="keys", tablefmt="latex_booktabs")


def gnuplotAllTime(loadedResults, out):
    pass


def genSimHist(loadedResults, out):
    pass


def genAppTable(loadedResults, out):

    total_trace_count = {}
    tables = {}
    for key in loadedResults:
        fileinf,lines = loadedResults[key]
        assert(fileinf.precision_level in PRECISION_LEVELS)
        current_precision_level = tables.get(fileinf.precision_level,{}) #precision level is first dim
        for line in lines:
            current_app_unsafe_count = current_precision_level.get(line.app_name,0)
            current_app_unsafe_count += 1 if isunsafe(line) else 0
            current_precision_level[line.app_name] = current_app_unsafe_count

            if(fileinf.precision_level == PRECISION_LEVELS[0]):
                total_trace_count[line.app_name] = total_trace_count.get(line.app_name,0)+1

        tables[fileinf.precision_level] = current_precision_level

    del tables['lifestate_va0']
    tables['aa_trace_count'] = total_trace_count
    dataframe = pandas.DataFrame(tables)
    # print dataframe
    print tabulate.tabulate(dataframe, headers="keys", tablefmt="latex_booktabs")
        # current_app_row = current_precision_level.get(fileinf)

    # for precision_level in precision_levels:
    #     df = pandas.DataFrame(index = properties_list, columns=column_names)
    #     pass
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print results table with accumulated proofs')
    parser.add_argument('--dir', type=str,
                        help="directory of files to process",required=True)
    parser.add_argument('--apps_list', type=str,
                        help="text file to output list of all apps")
    parser.add_argument('--blacklist', type=str,
                        help="remove apps from results, one per line in file")
    parser.add_argument('--app_alias', type=str,
                        help="file with each line representing the possible aliases for an app separated by commas")
    parser.add_argument('--out', type=str, help="output directory to dump gnu plot data and other files", required=True)
    parser.add_argument('--mode', type=str, help="timeSafe, timeAll or table")

    args = parser.parse_args()

    #create alias map from file
    alias_map = loadAliasMap(args.app_alias)


    loadedResults = loadDirectory(args.dir, alias_map)
    if args.mode == "timeSafe":
        gnuplotTime(loadedResults, 10, args.out)
    elif args.mode == "timeAll":
        gnuplotAllTime(loadedResults,args.out)
    elif args.mode == "table":
        genTable(loadedResults, args.out)
    elif args.mode == "simTimeHist":
        genSimHist(loadedResults,args.out)
    elif args.mode == "byApp":
        genAppTable(loadedResults,args.out)
    else:
        raise Exception("Please specify mode with --mode")
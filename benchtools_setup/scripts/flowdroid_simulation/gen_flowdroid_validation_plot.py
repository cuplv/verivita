import sys
import os
import optparse
import math
import logging
import subprocess

# index starts from 0
INDEX_RESULT=2
INDEX_TIME=INDEX_RESULT + 2
INDEX_STEPS=INDEX_TIME + 2
INDEX_STEPS_TOTAL=INDEX_STEPS + 2
INDEX_FAILURE_REASON=INDEX_STEPS_TOTAL + 2

def _call_sub(args, cwd=None, wait=True):
    """Call a subprocess.
    """
    logging.info("Executing %s" % " ".join(args))

    # not pipe stdout - processes will hang
    # Known limitation of Popen
    proc = subprocess.Popen(args, cwd=cwd)
    proc.wait()

    return_code = proc.returncode
    if (return_code != 0):
        err_msg = "Error code is %s\nCommand line is: %s\n%s" % (str(return_code), str(" ".join(args)),"\n")

        logging.error("Error executing %s\n%s" % (" ".join(args), err_msg))
        return False

    return True

def inc_bucket_cat(bucket, index, category):
    if index in bucket:
        category_map = bucket[index]
    else:
        category_map = {}
        bucket[index] = category_map

    if category in category_map:
        count = category_map[category]
    else:
        count = 0
    category_map[category] = count + 1


def get_bucket_index(trace_comp, bucket_size):
    index_float = trace_comp / bucket_size
    index_round = int(math.floor(index_float))
    return index_round


def get_max_trace_length(logfile_name, length_index):
    max_length = 0
    with open(logfile_name) as logfile:
        for line in logfile:
            if line.startswith("#"): # skip comments
                continue
            line = line.strip()

            splitted = line.split(" ")

            try:
                steps = float(splitted[length_index])
            except:
                continue

            if steps > max_length:
                max_length = steps
    return max_length

def main(input_args=None):
    p = optparse.OptionParser()

    p.add_option('-f', '--logfile',
                 help="Logfile with the flowdroid simulation results")

    def usage(msg=""):
        if msg: print "----%s----\n" % msg
        p.print_help()
        sys.exit(1)

    if (input_args is None):
        input_args = sys.argv[1:]
    opts, args = p.parse_args(input_args)

    if (not opts.logfile): usage("Missing log file (-f)")
    if (not os.path.exists(opts.logfile)):
        usage("Log file %s does not exists!" % opts.logfile)


    # counts the number of traces that have been completed are >= 
    sim_buckets_cat = {}
    sim_buckets_length_cat = {}
    sim_buckets_total_length_cat = {}

    max_simul_steps = get_max_trace_length(opts.logfile, INDEX_STEPS)
    max_length = get_max_trace_length(opts.logfile, INDEX_STEPS_TOTAL)

    # Divide the traces by completion rate
    if (False):
        total_buckets = 10
        bucket_size_length = max_simul_steps / total_buckets

        total_buckets_total_length = total_buckets
        bucket_total_size_length = max_length / total_buckets_total_length
    else:
        bucket_size_length = 25
        total_buckets = int(math.floor(max_simul_steps / bucket_size_length))

        bucket_total_size_length = bucket_size_length
        total_buckets_total_length = int(math.floor(max_length / bucket_total_size_length))

    total_0_length_traces = 0
    total_error_traces = 0
    total_number_of_traces = 0
    sum_of_lengths = 0
    with open(opts.logfile) as logfile:
        for line in logfile:
            if line.startswith("#"): # skip comments
                continue
            line = line.strip()

            splitted = line.split(" ")
            result = splitted[INDEX_RESULT].strip()
            time = splitted[INDEX_TIME]

            if result == "Ok":
                reason = "Ok"
            elif result == "Block":
                reason = splitted[INDEX_FAILURE_REASON]
            else:
                print("Skipping trace with %s result..." % result)
                total_error_traces += 1
                continue

            try:
                steps = float(splitted[INDEX_STEPS])
            except:
                logging.warning("Cannot convert steps "\
                                "%s" % splitted[INDEX_STEPS])
                continue
            try:
                total = float(splitted[INDEX_STEPS_TOTAL])
            except:
                logging.warning("Cannot convert total steps " \
                                "%s" % splitted[INDEX_STEPS_TOTAL])

            if total == 0:
                total_0_length_traces += 1
                continue

            if reason == "?":
                print("Found trace with ? failure reason! --- %s\n" \
                      "Check that the trace get stuck in the first step \n" \
                      "on a lifecycle-controlled callback!\n" \
                      "We are assuming this when generating the plots" % line)
                reason = "FailureCbNonActive"

            if reason == "FailureFragLc":
                print("Mergin fragment lifecylce errors with activity "\
                      "lifecycle errors!\n")
                reason = "FailureActLc"

            total_number_of_traces += 1
            sum_of_lengths += total

            assert steps <= total

            # Cumulative number of traces
            # Count the traces also in the previous buckets!
            index = get_bucket_index(steps, bucket_size_length)
            assert index >=0 and index <= total_buckets
            for i in range(index+1):
                inc_bucket_cat(sim_buckets_length_cat, i, reason)

            # Total (non-cumulative) number of traces
            index = get_bucket_index(total, bucket_total_size_length)
            assert index >=0 and index <= total_buckets_total_length
            inc_bucket_cat(sim_buckets_total_length_cat, index, reason)

        gen_trace_plot_cat(sim_buckets_length_cat, bucket_size_length,
                           "Steps before unsoundness",
                           "Cumulative number of traces",
                           "flowdroid_trace_completion_trace_cat",
                           101)

        gen_trace_plot_cat(sim_buckets_total_length_cat, bucket_total_size_length,
                           "Total length of the trace to validate",
                           "Number of traces",
                           "flowdroid_total_length_trace_cat",
                           250)


        average_length = float(sum_of_lengths) / float(total_number_of_traces)
        print("Trace statistics:\n" \
              "Skipped 0-length traces: %d\n" \
              "Skipped error traces traces: %d\n" \
              "Total number of processed traces: %d\n" \
              "Average trace length: %f"  % (total_0_length_traces,
                                             total_error_traces,
                                             total_number_of_traces,
                                             average_length))

        for key, value in sim_buckets_length_cat.iteritems():
            print "%s/%s" % (str(key), str(value))


def gen_trace_plot_cat(sim_buckets_cat, bucket_size,xlabel, ylabel,name, max_bucket = None):
    categories = ["Ok",
                  "FailureActInterleaving",
                  "FailureFragNonActive",
                  "FailureActLc",
                  "FailureCbNonActive"]

    readable = {"FailureActInterleaving" : "\"No interleaving of Components\"",
                "FailureActLc" : "\"Wrong lifecycle automata\"",
                "FailureCbNonActive" : "\"Wrong active state\"",
                "FailureFragInterleaving" : "\"No interleaving of Fragments\"",
                "FailureFragNonActive" : "\"Wrong state to start Fragment lifecycle\"",
                "Ok" : "\"No errors\""}

    # Generate trace completion plot
    tc_data_name = "%s.dat" % name
    with open(tc_data_name, "w") as tc_data:
        tc_data.write("# Flowdroid validation results\n" \
                      "#\n"\
                      "Completion")
        for cat in categories:
            tc_data.write(" %s" % readable[cat])
        tc_data.write("\n")

        last_floor = None
        category_sum = [0 for c in categories]
        last_ceiling = None

        for key, category_map in sim_buckets_cat.iteritems():
            completion_floor = int(math.ceil(key * bucket_size))
            completion_ceiling = int(math.floor((key+1) * bucket_size))

            if (max_bucket is None or completion_ceiling < max_bucket):
                tc_data.write("\"%s-%s\"" % (str(completion_floor), str(completion_ceiling)))

                for cat in categories:
                    if cat in category_map:
                        count = category_map[cat]
                    else:
                        count = 0
                    tc_data.write(" %s" % (str(count)))
                tc_data.write("\n")
            else:
                if last_floor is None:
                    last_floor = completion_floor
                last_ceiling = completion_ceiling

                for i in range(len(categories)):
                    cat = categories[i]
                    if cat in category_map:
                        count = category_map[cat]
                    else:
                        count = 0
                    category_sum[i] += count

        if not last_floor is None:
            tc_data.write("\"%s-%s\"" % (str(last_floor), str(last_ceiling)))
            for count in category_sum:
                tc_data.write(" %s" % (str(count)))
            tc_data.write("\n")

        tc_data.close()

    plot_name = "%s.png" % name
    gnuplot_cmd = """
set terminal png   enhanced font "arial,10" fontscale 1.0 size 600, 400 
set output '%s'

set xlabel \"%s\"
set ylabel \"%s\"

set key autotitle columnheader invert
set style data histogram
set style histogram rowstacked gap 1
set style fill solid border -1
set boxwidth 0.75
#set boxwidth 0.9
set xtic rotate by -45 scale 0
#set bmargin 10 

plot '%s' using 2:xtic(1) lc 1 fillstyle pattern 3, \\
for [i=3:%d] '' using i lc i fillstyle pattern i==4 ? i+5 : i+1;""" % (plot_name, xlabel, ylabel, tc_data_name, len(categories)+1)

    gnuplot_file_name = "%s.g" % name
    with open(gnuplot_file_name, 'w') as gpf:
        gpf.write(gnuplot_cmd)
        gpf.close()

    args = ["gnuplot", gnuplot_file_name]
    _call_sub(args)

    print("Generated files:\n"\
          "Data file: %s\n"\
          "Gnuplot cmd: %s\n"\
          "Plot: %s\n" % (tc_data_name, gnuplot_file_name, plot_name))

if __name__ == '__main__':
    main()


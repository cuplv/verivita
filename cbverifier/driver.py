""" Performs the runtime verification.
"""

import sys
import os
import optparse
import logging


from cbverifier.traces.ctrace import CTraceSerializer, CCallin, CMessage
from cbverifier.traces.ctrace import CCallback, MessageFilter
from cbverifier.traces.ctrace import MalformedTraceException, TraceEndsInErrorException
from cbverifier.specs.spec import Spec
from cbverifier.encoding.encoder import TSEncoder
from cbverifier.encoding.cex_printer import CexPrinter
from cbverifier.bmc.bmc import BMC

from cbverifier.utils.stats import Stats

from smv.tosmv import SmvTranslator, NuXmvDriver
from pysmt.shortcuts import Not

class DriverOptions:
    def __init__(self,
                 tracefile,
                 traceformat,
                 spec_file_list,
                 simplify_trace,
                 debug,
                 filter_msgs,
                 allow_exception=True,
                 use_flowdroid_model = False):
        self.tracefile = tracefile
        self.traceformat = traceformat
        self.spec_file_list = spec_file_list
        self.simplify_trace = simplify_trace
        self.debug = debug
        self.filter_msgs = filter_msgs
        self.allow_exception = allow_exception
        self.use_flowdroid_model = use_flowdroid_model

class NoDisableException(Exception):
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


class Driver:
    def __init__(self, opts, ctrace_input=None):
        self.opts = opts

        self.stats = Stats()
        self.stats.enable()

        if ctrace_input is None:
            # Parse the trace
            try:
                self.stats.start_timer(Stats.PARSING_TIME)
                self.trace = CTraceSerializer.read_trace_file_name(self.opts.tracefile,
                                                                   self.opts.traceformat == "json",
                                                                   self.opts.allow_exception)
                self.stats.stop_timer(Stats.PARSING_TIME)
                self.stats.write_times(sys.stdout, Stats.PARSING_TIME)
            except MalformedTraceException as e:
                raise
            except TraceEndsInErrorException as e:
                raise
            except Exception as e:
                raise Exception("An error happened reading the trace in %s (%s)" % (self.opts.tracefile,
                                                                                e.message))
        else:
            self.trace = ctrace_input


        # Parse the specs
        self.spec_list = Spec.get_specs_from_files(self.opts.spec_file_list)
        if self.spec_list is None:
            raise Exception("Error parsing the specification file!")


    def check_files(self, stream):
        stream.write("SPECIFICATIONS:\n")
        for spec in self.spec_list:
            spec.print_spec(stream)
            stream.write("\n")

        stream.write("\nTRACE:\n")
        if (self.opts.filter_msgs != None):
            self.trace.print_trace(stream, self.opts.debug,
                                   MessageFilter.typeFilterFrom(self.opts.filter_msgs))
        else:
            self.trace.print_trace(stream, self.opts.debug)
        stream.write("\n")

    def get_ground_specs(self, get_map = False):
        ts_enc = TSEncoder(self.trace, self.spec_list, False, self.stats, self.opts.use_flowdroid_model)
        if not get_map:
            ground_specs = ts_enc.get_ground_spec()
        else:
            ground_specs = ts_enc.get_orig_ground_spec()
        return ground_specs

    def run_bmc(self, depth, inc=False):
        ts_enc = TSEncoder(self.trace, self.spec_list, self.opts.simplify_trace,
                           self.stats, self.opts.use_flowdroid_model)

        self.stats.start_timer(Stats.VERIFICATION_TIME)

        bmc = BMC(ts_enc.helper,
                  ts_enc.get_ts_encoding(),
                  ts_enc.error_prop)

        cex = bmc.find_bug(depth, inc)

        self.stats.stop_timer(Stats.VERIFICATION_TIME)
        self.stats.write_times(sys.stdout, Stats.VERIFICATION_TIME)


        return (cex, ts_enc.mapback)

    def to_smv(self, smv_file_name):
        ts_enc = TSEncoder(self.trace, self.spec_list,
                           self.opts.simplify_trace,
                           self.stats,
                           self.opts.use_flowdroid_model)
        ts = ts_enc.get_ts_encoding()
        ts2smv = SmvTranslator(ts_enc.pysmt_env,
                               ts.state_vars,
                               ts.input_vars,
                               ts.init,
                               ts.trans,
                               Not(ts_enc.error_prop))

        with open(smv_file_name, "wt") as f:
            ts2smv.to_smv(f)
            f.close()

    def run_ic3(self, nuxmv_path, ic3_frames):
        ts_enc = TSEncoder(self.trace, self.spec_list,
                           self.opts.simplify_trace,
                           self.stats,
                           self.opts.use_flowdroid_model)
        ts = ts_enc.get_ts_encoding()

        self.stats.start_timer(Stats.VERIFICATION_TIME,True)

        nuxmv_driver = NuXmvDriver(ts_enc.pysmt_env, ts, nuxmv_path)
        (result, trace) = nuxmv_driver.ic3(Not(ts_enc.error_prop),
                                           ic3_frames)

        self.stats.stop_timer(Stats.VERIFICATION_TIME,True)
        self.stats.write_times(sys.stdout, Stats.VERIFICATION_TIME)

        return (result, trace, ts_enc.mapback)

    def run_simulation(self, cb_sequence = None): 
        ts_enc = TSEncoder(self.trace, self.spec_list,
                           self.opts.simplify_trace,
                           self.stats,
                           self.opts.use_flowdroid_model)

        self.stats.start_timer(Stats.SIMULATION_TIME)

        bmc = BMC(ts_enc.helper,
                  ts_enc.get_ts_encoding(),
                  ts_enc.error_prop)

        trace_enc = ts_enc.get_trace_encoding(cb_sequence)
        (step, trace, last_trace) = bmc.simulate(trace_enc)

        self.stats.stop_timer(Stats.SIMULATION_TIME)
        self.stats.write_times(sys.stdout, Stats.SIMULATION_TIME)

        return (step, trace, last_trace, ts_enc.mapback)

    def slice(self, object_id, stream):
        if object_id is not None:
            sliced = i_slice(self.trace,object_id)
            self.trace.print_trace(stream, self.opts.debug,
                       None)
        else:
            raise Exception("object id cannot be none")

def i_slice(c_obj, object_id):
    new_children = []
    for item in c_obj.children:
        i_slice(item, object_id).children

        # if not any(e for e in list[item].params if e.object_id == object_id ):

        contains = False
        for param in item.params:
            for obj_id in object_id:
                if param.object_id == obj_id:
                    contains = contains or True

        if isinstance(item,CCallback):
            for obj_id in object_id:
                contains = contains or \
                           ((item.return_value is not None) and \
                           item.return_value.object_id == obj_id)
        elif isinstance(item,CCallin):
            for obj_id in object_id:
                contains = contains or \
                           ((item.return_value is not None) and \
                           item.return_value.object_id == obj_id)
        else:
            raise Exception("Malformed trace")
        if contains or (len(item.children) > 0):
            #item does not contain object ref so remove
            new_children.append(item)
    c_obj.children = new_children

    return c_obj


def print_ground_spec(ground_specs, out=sys.stdout):
    out.write("List of ground specifications:\n")
    for spec in ground_specs:
        spec.print_spec(out)
        out.write("\n")

def print_ground_spec_map(ground_spec_map, out=sys.stdout):
    out.write("List of ground specifications:\n")

    for orig_spec, ground_spec_list in ground_spec_map.iteritems():
        out.write("Ground specs for: ")
        orig_spec.print_spec(out)
        out.write("\n----\n")
        for spec in ground_spec_list:
            spec.print_spec(out)
            out.write("\n")
        out.write("----\n")

def check_disable(ground_specs):
    has_disable = False
    for spec in ground_specs:
        has_disable = has_disable or spec.is_disable()
        if has_disable:
            break

    if (not has_disable):
        raise NoDisableException("No callins can be disabled in the "
                                 "trace with the given specs")


def main(input_args=None):
    p = optparse.OptionParser()

    p.add_option('-t', '--tracefile',
                 help="File containing the concrete trace (protobuf format)")

    p.add_option('-f', '--traceformat', type='choice',
                 choices= ["bin","json"],
                 help="Choose between the binary and json proto formats (default bin)",
                 default = "bin")

    p.add_option('-s', '--specfile', help="Colon (:) seperated list" \
                 "of specifications.")

    p.add_option('-r', '--use_flowdroid_model', action="store_true",
                 default=False, help="Use the flowdroid lifecycle model "\
                 "to encode the enabled callbacks.\n " \
                 "Warning: we ignore the enabled/disable rules in the "\
                 "encoding in this case")

    # Encoding options
    p.add_option('-z', '--simplify_trace', action="store_true",
                 default=False, help="Simplify the trace (possibly unsound)")

    p.add_option('-d', '--debug', action="store_true",
                 default=False,
                 help="Output debug informations")

    def get_len(string, length):
        current = len(string)
        while (current > length):
            current = current - length
        else:
            string = string + "".join([" " for i in range(length - current)])
        return string
    p.add_option('-m', '--mode', type='choice',
                 choices= ["bmc","ic3","check-files","to-smv","show-ground-specs","simulate","check-trace-relevance","slice"],
                 help=(get_len('bmc: run bmc on the trace;', 53) +
                       get_len('ic3: run ic3 on the trace;', 53) +
                       get_len('check-files: check if the input files are well formed and prints them; ', 53) +
                       get_len('show-ground-specs: shows the specifications instantiateed by the given trace; ', 53) +
                       get_len('simulate: simulate the given trace with the existing specification; ', 53) +
                       get_len('to-smv: prints the SMV file of the generated transition system. ', 53) +
                       get_len('check-trace-relevance: check if a trace is well formed, does not end with an exception and can instantiate a disable rule.', 53)) +
                       get_len('slice: slice a trace for relevant transitions with object or transition id', 53),
                 default = "bmc")

    # Bmc options
    p.add_option('-k', '--bmc_depth', help="Depth of the search")
    p.add_option('-i', '--bmc_inc', action="store_true",
                 default=False, help="Incremental search")


    # SMV options
    p.add_option('-o', '--smv_file', help="Output smv file")

    # IC3 options
    p.add_option('-n', '--nuxmv_path', help="Path to the nuXmv executable")
    p.add_option('-q', '--ic3_frames', help="Maximum number of frames explored by IC3")

    # simulation options
    p.add_option("-w", '--cb_sequence', help="Sequence of callbacks " \
                 "(message ids) to be simulated.")

    # Miscellaneous
    p.add_option('-x', '--print_orig_spec', action="store_true",
                 default=False, help="Print the original spec")



    p.add_option('-l', '--filter', help="When running check-files this will only: filter all messages to the ones"
                                        "where type is matched")

    p.add_option('-j', '--object_id', help="When running slice this is a concrete object to target")


    def usage(msg=""):
        if msg: print "----%s----\n" % msg
        p.print_help()
        sys.exit(1)

    if (input_args is None):
        input_args = sys.argv[1:]
    opts, args = p.parse_args(input_args)

    if (not opts.tracefile): usage("Missing trace file (-t)")
    if (not os.path.exists(opts.tracefile)):
        usage("Trace file %s does not exists!" % opts.tracefile)
    if (not opts.specfile): usage("Missing specification file (-s)")

    spec_file_list = opts.specfile.split(":")
    for f in spec_file_list:
        if (not os.path.exists(f)):
            usage("Specification file %s does not exists!" % f)

    if (opts.mode == "bmc"):
        if (not opts.bmc_depth): usage("Missing BMC depth")
        try:
            depth = int(opts.bmc_depth)
        except:
            usage("%s must be a natural number!" % opts.bmc_depth)
        if (depth < 0): usage("%s must be positive!" % opts.bmc_depth)
    else:
        bmc_opt = [(opts.bmc_depth, "--bmc_depth"),
                   (opts.bmc_inc, "--bmc_inc")]
        for (opt, desc) in bmc_opt:
            if opt:
                usage("%s options cannot use in mode %s\n" % (desc, opts.mode))

    if (opts.mode == "simulate"):
        if (opts.cb_sequence):
            cb_sequence = []
            for n in opts.cb_sequence.split(":"):
                cb_sequence.append(int(n))
        else:
            cb_sequence = None

    if (opts.mode == "to-smv"):
        if (not opts.smv_file): usage("Destination SMV file not specified!")
    else:
        if opts.smv_file:
            usage("%s options cannot use in mode " % ("", opts.mode))

    if (opts.mode == "ic3"):
        if (not opts.nuxmv_path):
            usage("Path to the nuXmv executable not provided!")
        if (not os.path.isfile(opts.nuxmv_path)):
            usage("%s is not a valid path tp the nuXmv executable!" % opts.nuxmv_path)

        if (not opts.ic3_frames): usage("Missing IC3 frames (--ic3_frames)")
        try:
            ic3_frames = int(opts.ic3_frames)
        except:
            usage("%s must be a natural number!" % opts.ic3_frames)
        if (ic3_frames < 0): usage("%s must be positive!" % opts.ic3_frames)


    if (opts.debug):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if (opts.print_orig_spec):
        print_orig_spec = True
    else:
        print_orig_spec = False

    driver_opts = DriverOptions(opts.tracefile,
                                opts.traceformat,
                                spec_file_list,
                                opts.simplify_trace,
                                opts.debug,
                                opts.filter,
                                opts.mode != "check-trace-relevance",
                                opts.use_flowdroid_model)
    driver = Driver(driver_opts)

    if opts.use_flowdroid_model:
        logging.warning("\nUSING THE FLOWDROID MODEL...\n")

    if (opts.mode == "check-files"):
        driver.check_files(sys.stdout)
        return 0
    elif (opts.mode == "show-ground-specs"):
        if print_orig_spec:
            ground_specs_map = driver.get_ground_specs(True)
            print_ground_spec_map(ground_specs_map)
        else:
            ground_specs = driver.get_ground_specs()
            print_ground_spec(ground_specs)

    elif (opts.mode == "bmc"):
        (cex, mapback) = driver.run_bmc(depth, opts.bmc_inc)

        if (cex is not None):
            printer = CexPrinter(mapback, cex, sys.stdout, print_orig_spec)
            printer.print_cex()
        else:
            print "No bugs found up to %d steps" % (depth)
        return 0
    elif (opts.mode == "simulate"):
        (steps, cex, last_cex, mapback) = driver.run_simulation(cb_sequence)

        if (cex is not None):
            print "\nThe trace can be simulated in %d steps." % steps
            printer = CexPrinter(mapback, cex, sys.stdout, print_orig_spec)
            printer.print_cex()
        else:
            print("The trace cannot be simulated (it gets stuck at the " +
                  "%d-th transition)" % (steps))


            if (logging.getLogger().getEffectiveLevel() == logging.DEBUG):
                if steps == 1:
                    print("Cannot simulate the first event!")
                else:
                    print("Last simulable trace:")
                    printer = CexPrinter(mapback, last_cex, sys.stdout, print_orig_spec)
                    printer.print_cex()

                    print("\n--- WARNING: the trace *CANNOT* be simulated! ---")

        return 0
    elif (opts.mode == "check-trace-relevance"):
        ground_specs = driver.get_ground_specs()
        check_disable(ground_specs)
    elif (opts.mode == "to-smv"):
        driver.to_smv(opts.smv_file)
        return 0
    elif (opts.mode == "ic3"):
        (res, cex, mapback) = driver.run_ic3(opts.nuxmv_path, opts.ic3_frames)

        if res is None:
            print("An error occurred invoking ic3")
        elif res == NuXmvDriver.UNKNOWN:
            print("The result is still unknown (e.g try to increment " +
                  "the number of frames).")
        elif res == NuXmvDriver.SAFE:
            print("The trace is SAFE")
        elif res == NuXmvDriver.UNSAFE:
            print("The system can reach an error state.")

            if (cex is not None):
                printer = CexPrinter(mapback, cex, sys.stdout, print_orig_spec)
                printer.print_cex()


        return 0
    elif(opts.mode == "slice"):
        driver.slice(opts.object_id.split(':'), sys.stdout)



if __name__ == '__main__':
    main()

""" Utility used to print a counterexample.

"""

import sys
import collections

from pysmt.shortcuts import Symbol, TRUE, FALSE

from verifier import Verifier, EventInfo
from spec import SpecType

# Set to false to get all the information of the trace
PRETTY_PRINT = True


""" Base class used to print a cex.
"""
class CexPrinter:

    def __init__(self, verifier, cex, out_stream=None):
        self._verifier = verifier
        self._cex = cex

        if (None == out_stream):
            self.out_stream = sys.stdout
        else:
            self.out_stream = out_stream

    def _print_sep(self):
        sep = "----------------------------------------\n"
        self.out_stream.write(sep)

    def _print_cex_header(self):
        self.out_stream.write("\n--- Counterexample ---\n")
        self._print_sep()

    def print_cex(self, changed=False, readable=True):
        """ Print the cex. """

        i = 0
        prev_state = {}

        self._print_cex_header()

        for step in self._cex:
            self._print_sep()
            self.out_stream.write("State - %d\n" % i)
            self._print_sep()
            self._print_var_set(self._verifier.ts_state_vars,
                                step, prev_state, False,
                                (readable and i == 0), changed)

            # skip the last input vars
            if (i >= (len(self._cex)-1)): continue

            self.out_stream.write("\n")
            self._print_sep()
            self.out_stream.write("Input - %d\n" % i)
            self._print_sep()
            self._print_var_set(self._verifier.ts_input_vars,
                                step, prev_state, True,
                                False, False, True)
            self.out_stream.write("\n")
            i = i + 1

        self.out_stream.flush()

    def _print_var_set(self,
                       varset, step, prev_state,
                       only_true = False,
                       skipinit = True,
                       only_changed = True,
                       input_var = False):

        if skipinit:
            self.out_stream.write("All events/callins are enabled\n")

        for key in varset:
            assert key in step

            if key in self._verifier.var_to_msgs:
                message = self._verifier.var_to_msgs[key]
            elif key in self._verifier.input_var_to_msgs:
                message = self._verifier.input_var_to_msgs[key]
            else:
                message = None

            value = step[key]
            if only_changed:
                if (key not in prev_state or
                    (key in prev_state and
                    prev_state[key] != value)):
                    if only_true and value == FALSE():
                        continue
                    if not skipinit:
                        self._print_val(key,value,message,input_var)
                prev_state[key] = value
            else:
                if only_true and value == FALSE():
                    continue
                if not skipinit:
                    self._print_val(key,value,message,input_var)

    def _print_val(self, key, val, msg, input_var=False):
        """
        Key: name of the variable in the encoding
        Val: value of the variable (true/false)
        msg: message (event or callin)
        """
        if None != msg:
            if PRETTY_PRINT:
                if msg in self._verifier.readable_msgs:
                    msg = self._verifier.readable_msgs[msg]
                to_print = "(%s): %s\n" % (msg, val)
                self.out_stream.write(to_print)
            else:
                to_print = "(%s): %s: %s\n" % (msg, key, val)
                self.out_stream.write(to_print)
        else:
            to_print = "%s: %s\n" % (key, val)
            self.out_stream.write(to_print)


""" Print a cex directly showing events information
"""
class EventCexPrinter(CexPrinter):

    def __init__(self, verifier, cex, out_stream=None):
        CexPrinter.__init__(self, verifier, cex, out_stream)


    def _print_msg(self, msg, val, input_var):
        # input var, transition
        assert (msg in self._verifier.msgs.evt_info)
        msg_info = self._verifier.msgs.evt_info[msg]
        is_evt = isinstance(msg_info, EventInfo)

        read_msg = self._verifier._get_readable_msg(msg)

        if is_evt:
            # concrete instances
            indexes = []
            match_info = self._verifier.msgs
            for l in  msg_info.conc_msgs:
                for index in match_info.cmsgs_to_index[l]:
                    indexes.append(index)
            indexes.sort()

            if (val == FALSE): status = "disabled"
            else: status = "enabled"

            self.out_stream.write("Event - Indexes: %s\n" % (",".join(indexes)))
            self.out_stream.write("        Status: %s\n" % (status))
            self.out_stream.write("        Callbacks: %s\n" % (read_msg))

            if input_var:
                effects = []
                for (rule, inst, dst_inst) in msg_info.matches:
                    if (dst_inst == None): continue
                    if (rule.specType == SpecType.Enable): act = "enable"
                    elif (rule.specType == SpecType.Allow): act = "disable"
                    elif (rule.specType == SpecType.Disable): act = "disable"
                    elif (rule.specType == SpecType.Disallow): act = "disallow"

                    src = "%s(%s)" % (inst.symbol, ",".join(inst.args))
                    dst = "%s(%s)" % (dst_inst.symbol, ",".join(dst_inst.args))
                    effect = "%s [%s] %s" % (src, act, dst)
                    effects.append(effect)

                first = True
                for e in effects:
                    if first:
                        self.out_stream.write("        effects: %s\n" % (e))
                        first = False
                    else:
                        self.out_stream.write("                 %s\n" % (e))
        else:
            if (val == FALSE): status = "allowed"
            else: status = "disallowed"

            self.out_stream.write("Callin - ")
            self.out_stream.write("Name: %s\n" % (read_msg))
            self.out_stream.write("         Status: %s\n" % (status))

    def _print_val(self, key, val, msg, input_var):
        if None == msg:
            # Non-message variable
            to_print = "Encoding variable %s: %s\n" % (key, val)
            self.out_stream.write(to_print)
        else:
            self._print_msg(msg, val, input_var)






""" Utility used to print a counterexample.

"""

import sys
import collections

from pysmt.shortcuts import Symbol, TRUE, FALSE

from verifier import Verifier

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
            self.out_stream.write("State - %d\n" % i)
            self._print_sep()

            self._print_var_set(self._verifier.ts_state_vars,
                                step, prev_state, False,
                                (readable and i == 0), changed)

            # skip the last input vars
            if (i >= (len(self._cex)-1)): continue
            self._print_sep()
            self.out_stream.write("Input - %d\n" % i)
            self._print_sep()
            self._print_var_set(self._verifier.ts_input_vars,
                                step, prev_state, True,
                                False, False)
            self._print_sep()
            i = i + 1
        self.out_stream.flush()

    def _print_var_set(self,
                       varset, step, prev_state,
                       only_true = False,
                       skipinit = True,
                       only_changed = True):
        def _print_val(key,val,msg):
            if None != msg:
                if PRETTY_PRINT:
                    if msg in self._verifier.readable_msgs:
                        msg = self._verifier.readable_msgs[msg]
                    to_print = "(%s): %s\n" % (msg, value)
                    self.out_stream.write(to_print)
                else:
                    to_print = "(%s): %s: %s\n" % (msg, key, value)
                    self.out_stream.write(to_print)
            else:
                to_print = "%s: %s\n" % (key, value)
                self.out_stream.write(to_print)

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
                        _print_val(key,value,message)
                prev_state[key] = value
            else:
                if only_true and value == FALSE():
                    continue
                if not skipinit:
                    _print_val(key,value,message)




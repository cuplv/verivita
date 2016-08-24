""" Utility used to print a counterexample.

"""

import collections

from pysmt.shortcuts import Symbol, TRUE, FALSE

from verifier import Verifier

# Set to false to get all the information of the trace
PRETTY_PRINT = True


""" Base class used to print a cex.
"""
class CexPrinter:

    def __init__(self, verifier, cex):
        self._verifier = verifier
        self._cex = cex

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
                    print("(%s): %s" % (msg, value))
                else:
                    print("(%s): %s: %s" % (msg, key, value))
            else:
                print("%s: %s" % (key, value))

        if skipinit:
            print "All events/callins are enabled"

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



    def print_cex(self, changed=False, readable=True):
        sep = "----------------------------------------"
        i = 0

        prev_state = {}

        print("")
        print("--- Counterexample ---")
        print(sep)
        for step in self._cex:
            print("State - %d" % i)
            print(sep)

            self._print_var_set(self._verifier.ts_state_vars,
                                step, prev_state, False,
                                (readable and i == 0), changed)

            # skip the last input vars
            if (i >= (len(self._cex)-1)): continue
            print(sep)
            print("Input - %d" % i)
            print(sep)
            self._print_var_set(self._verifier.ts_input_vars,
                                step, prev_state, True,
                                False, False)
            print(sep)
            i = i + 1

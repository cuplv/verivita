"""Convert a ts in pysmt in a smv file.

All the vars are assumed to be Boolean
"""

from pysmt.walkers import DagWalker
from pysmt.printers import TreeWalker
import pysmt.typing as types
from pysmt.typing import BOOL
import pysmt.operators as op
import pysmt.environment
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne

from pysmt.shortcuts import Solver
from pysmt.solvers.solver import Model
from pysmt.logics import QF_BOOL

from cStringIO import StringIO

import logging
import sys
import os
import tempfile
from subprocess import Popen, PIPE

class NuXmvDriver:
    """ Call nuXmv via pipe.

    Rough interface to the tool.

    TODO: Ask AG about the python interface to msatic3.

    """

    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    UNKNOWN = "UNKNOWN"

    def __init__(self, pysmt_env, ts, nuxmv):
        self.pysmt_env = pysmt_env
        if (not os.path.isfile(nuxmv)):
            raise Exception("The nuXmv executable file %s does not exists " % nuXmv)
        self.ts = ts
        self.nuxmv = nuxmv
        self.ts2smv = None

    def get_tmp_file(self, file_suffix, to_delete=True):
        """ Get a tmpfile that is deleted when closed.

        WARNING: reading the file before it is closed works on UNIX
        platform and not on windows

        """

        f = tempfile.NamedTemporaryFile(mode = 'w',
                                        suffix = file_suffix,
                                        delete = to_delete)

        logging.debug("Creating temporary file %s " % f.name)

        return f

    @staticmethod
    def _call_sub(args, result_cb, cwd=None):
        """Call a subprocess.
        """
        logging.info("Executing %s" % " ".join(args))

        # not pipe stdout - processes will hang
        # Known limitation of Popen

        proc = Popen(args, cwd=cwd, stdout=PIPE,  stderr=PIPE)
        (stdout, stderr) = proc.communicate()

        return_code = proc.returncode
        if (return_code != 0):
            err_msg = "Error code is %s\nCommand line is: %s\n%s" % (str(return_code), str(" ".join(args)),"\n")

            logging.error("Error executing %s\n%s" % (" ".join(args), err_msg))

        result = result_cb(stdout, stderr, return_code)
        return result

    def _run_nuxmv(self, cmds, invarspec, result_cb):
        # 1. Writes the SMV model
        self.ts2smv = SmvTranslator(self.pysmt_env,
                                    self.ts.state_vars,
                                    self.ts.input_vars,
                                    self.ts.init,
                                    self.ts.trans,
                                    invarspec)

        smv_file = self.get_tmp_file("smv", True)
        self.ts2smv.to_smv(smv_file)
        smv_file.flush()

        # 2. Writes the CMD file
        cmd_file = self.get_tmp_file("cmd", True)
        # writes the cmd file
        cmd_file.write(cmds)
        cmd_file.flush()

        # call nuXmv
        args = [self.nuxmv, "-source", cmd_file.name, smv_file.name]
        res = NuXmvDriver._call_sub(args, result_cb)

        return res

    def ic3(self, invarspec, max_frames):
        """ Invokes IC3 on the safety property invarspec, and runs
        nuXmv for a maximum of max_frames.

        Return None if the TS |= invarspec or a counterexample.
        """

        def ic3_callback(stdout, stderr, res):
            if (0 != res):
                return None

            res = None
            found_success = False
            result = NuXmvDriver.UNKNOWN

            for line in stdout.split("\n"):
                if (line.startswith("-- invariant ") and
                    line.endswith("is true")):
                    result = NuXmvDriver.SAFE
                if (line.startswith("-- invariant ") and
                    line.endswith("is false")):
                    result = NuXmvDriver.UNSAFE
                elif line.startswith("SUCCESS"):
                    found_success = True

            if (not found_success):
                return None
            else:
                return result

        cmds = """
set on_failure_script_quits "1"
read_model
flatten_hierarchy
encode_variables -n
build_boolean_model
echo "Verifying property..."
check_invar_ic3 -n 0 -k "%s"
echo "%s"
quit
EOF
        """ % (max_frames, "SUCCESS")

        result = self._run_nuxmv(cmds, invarspec, ic3_callback)

        return result


class SmvTranslator:
    def __init__(self, env,
                 state_vars,
                 input_vars,
                 init, trans,
                 invarspec=None):
        self.state_vars = state_vars
        self.input_vars = input_vars
        self.init = init
        self.trans = trans
        self.invarspec = invarspec
        self.translator = SmvFormulaTranslator(env)
        self.env = env

    def to_smv(self, stream):

        stream.write("MODULE main\n")
        self.print_vars(stream, "VAR", self.state_vars)
        self.print_vars(stream, "IVAR", self.input_vars)

        if (self.invarspec is not None):
            stream.write("INVARSPEC\n")
            self._print_formula(stream, self.invarspec)

        stream.write(";\nINIT\n")
        self._print_formula(stream, self.init)
        stream.write(";\nTRANS\n")
        self._print_formula(stream, self.trans)
        stream.write(";\n")

        for (f, define) in self.translator.defines.iteritems():
            (def_name, def_def) = define
            stream.write("DEFINE %s := %s;\n" % (def_name, def_def));

        self.translator = None

    def print_vars(self, stream, var_type, vars_set):
        if len(vars_set) == 0: return

        assert(var_type == "IVAR" or
               var_type == "VAR" or
               var_type == "FROZENVAR")

        stream.write("%s\n" % var_type)

        for v in vars_set:
            stream.write(self.translator.translate(v))
            stream.write(" : boolean;\n")

    def translate_formula(self, formula):
        return self.translator.translate(formula)

    def _print_formula(self, stream, formula):
        stream.write(self.translator.translate(formula))

class SmvFormulaTranslator(DagWalker):
    def __init__(self, env, short_names=True):
        DagWalker.__init__(self, env, None)

        self.short_names = short_names
        self.symb_map = {}

        self.counter = 0
        self.def_counter = 0;

        # Map from formulas to define
        # We explore and build the DAG of the formula
        self.defines = {}

        self.mgr = self.env.formula_manager

    def translate(self, formula):
        s = self.walk(formula)
        return s

    def _get_key(self, formula, **kwargs):
        return formula

    USE_DEF = True
    def _insert_def(self, formula, res):
        if SmvFormulaTranslator.USE_DEF:
            self.def_counter = self.def_counter + 1
            def_var = "define_%d" % self.def_counter
            self.defines[formula] = (def_var, res)
            return def_var
        else:
            return res


    def _my_binary(self, formula, op_str, **kwargs):
        res = "("
        list_args = kwargs['args']
        for s in list_args[:-1]:
            assert type(s) == type("")
            res = "%s%s %s " % (res, s, op_str)
        s = kwargs['args'][-1]
        res = res + s + ")"

        res = self._insert_def(formula, res)

        return res

    def walk_or(self, formula, **kwargs):
        res = self._my_binary(formula, "|", **kwargs)
        return res

    def walk_and(self, formula, **kwargs):
        res = self._my_binary(formula, "&", **kwargs)
        return res

    def walk_implies(self, formula, **kwargs):
        res = self._my_binary(formula, "->", **kwargs)
        return res

    def walk_iff(self, formula, **kwargs):
        res = self._my_binary(formula, "<->", **kwargs)
        return res

    def walk_not(self, formula, **kwargs):
        s = kwargs['args'][0]
        res = self._insert_def(formula, "(! %s)" % s)

        return res

    def walk_symbol(self, formula, **kwargs):
        def _get_symbol_symbol_key(formula):
            assert formula.is_symbol(types.BOOL)
            symbol_str = formula.serialize()
            symbol_str = symbol_str.replace("\"", "")
            is_next = symbol_str.endswith("_next")
            if is_next:
                symbol_str = symbol_str[0:len(symbol_str)-len("_next")]
            return (symbol_str, is_next)

        if formula.is_symbol(types.BOOL):
            (key, is_next) = _get_symbol_symbol_key(formula)

            if key in self.symb_map:
                res = self.symb_map[key]
            else:
                if not self.short_names:
                    res = "\"%s\"" % key
                else:
                    self.counter = self.counter + 1
                    res = "var_%d" % self.counter
                self.symb_map[key] = res

            # add next to the variable
            if is_next:
                res = "next(%s)" % res
        else:
            assert False

        return res

    def walk_bool_constant(self, formula, **kwargs):
        if formula == TRUE():
            res = "TRUE"
        elif formula == FALSE():
            res = "FALSE"
        else:
            res = formula.serialize()

        return res
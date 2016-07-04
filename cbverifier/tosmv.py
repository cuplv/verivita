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


class SmvTranslator:
    def __init__(self, env,
                 state_vars, input_vars,
                 init, trans,
                 invarspec):
        self.state_vars = state_vars
        self.input_vars = input_vars
        self.init = init
        self.trans = trans
        self.invarspec = invarspec

        self.translator = None
        self.env = env

    def to_smv(self, stream):
        self.translator = SmvFormulaTranslator(self.env, stream)
        stream.write("MODULE main\n")
        self.print_vars(stream, "VAR", self.state_vars)
        self.print_vars(stream, "IVAR", self.input_vars)

        stream.write("INVARSPEC\n")
        self.print_formula(stream, self.invarspec)
        stream.write(";\nINIT\n")
        self.print_formula(stream, self.init)
        stream.write(";\nTRANS\n")
        self.print_formula(stream, self.trans)


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

    def print_formula(self, stream, formula):
        stream.write(self.translator.translate(formula))

class SmvFormulaTranslator(DagWalker):
    def __init__(self, env, stream, short_names=True):
        DagWalker.__init__(self, env, None)

        self.short_names = short_names
        self.symb_map = {}
        self.counter = 0

        self.mgr = self.env.formula_manager
        self.stream = stream
        self.write = self.stream.write

    def translate(self, formula):
        (f, s) = self.walk(formula)
        return s

    # def _get_key(self, formula, **kwargs):
    #     if len(kwargs) == 0:
    #         return formula
    #     raise NotImplementedError("DagWalker should redefine '_get_key'" +
    #                               " when using keywords arguments")

    def _my_binary(self, formula, op_str, **kwargs):
        res = "("
        list_args = kwargs['args']
        for (f, s) in list_args[:-1]:
            assert type(s) == type("")
            res = "%s%s %s " % (res,s,op_str)
        (f,s) = kwargs['args'][-1]
        res = res + s + ")"
        return res

    def walk_or(self, formula, **kwargs):
        res = self._my_binary(formula, "|", **kwargs)
        return (formula, res)

    def walk_and(self, formula, **kwargs):
        res = self._my_binary(formula, "&", **kwargs)
        return (formula, res)

    def walk_implies(self, formula, **kwargs):
        res = self._my_binary(formula, "->", **kwargs)
        return (formula, res)

    def walk_iff(self, formula, **kwargs):
        res = self._my_binary(formula, "<->", **kwargs)
        return (formula, res)

    def walk_not(self, formula, **kwargs):
        (l, s) = kwargs['args'][0]
        res = "(! %s)" % s
        return (formula, res)

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
                    res = "var_%d" % self.counter
                    self.counter = self.counter + 1
                self.symb_map[key] = res

            # add next to the variable
            if is_next:
                res = "next(%s)" % res
        else:
            assert False

        return (formula, res)

    def walk_bool_constant(self, formula, **kwargs):
        res = formula.serialize()
        return (formula, res)

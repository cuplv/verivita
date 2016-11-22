from cbverifier.encoding.encoder import TransitionSystem

import logging
from pysmt.logics import QF_BOOL
from pysmt.shortcuts import Solver
from pysmt.shortcuts import is_sat, is_valid
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or, Implies, Iff, ExactlyOne


class BMC:
    """
    Implementation of Bounded Model Checking
    """

    def __init__(self, helper, ts, error):
        self.helper = helper
        self.ts = ts
        self.error = error

    def find_bug(self, k):
        """Explore the system up to k steps.

        Returns None if no bugs where found up to k or a
        counterexample otherwise.
        """

        all_vars = set(self.ts.state_vars)
        all_vars.update(self.ts.input_vars)

        solver = Solver(name='z3', logic=QF_BOOL)
        encoding = self.encode_up_to_k(solver, all_vars, k)
        res = self.solve(solver, k)

        return res


    def encode_up_to_k(self, solver, all_vars, k):
        # Get the BMC encoding up to k
        error_condition = []
        for i in range(k + 1):
            # encode the i-th BMC step
            logging.debug("Encoding %d..." % i)

            if (i == 0):
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts.init, i)
            else:
                f_at_i = self.helper.get_formula_at_i(all_vars,
                                                      self.ts.trans, i-1)
            solver.add_assertion(f_at_i)


            error_condition.append(self.helper.get_formula_at_i(all_vars,
                                                                self.error,
                                                                i))
        # error condition in at least one of the (k-1)-th states
        logging.debug("Error condition %s" % error_condition)
        solver.add_assertion(Or(error_condition))


    def solve(self, solver, k):
        logging.debug("Finding bug up to %d steps..." % k)
        res = solver.solve()
        if (solver.solve()):
            logging.debug("Found bug...")

            model = solver.get_model()
            trace = self._build_trace(model, k)
            return trace
        else:
            # No bugs found
            logging.debug("No bugs found up to %d steps" % k)
            return None

    def _build_trace(self, model, steps):
        """Extract the trace from the satisfying assignment."""

        vars_to_use = [self.ts.state_vars, self.ts.input_vars]
        cex = []
        for i in range(steps + 1):
            cex_i = {}

            # skip the input variables in the last step
            if (i >= steps):
                vars_to_use = [self.ts.state_vars]

            for vs in vars_to_use:
                for var in vs:
                    var_i = self.helper.get_var_at_time(var, i)
                    cex_i[var] = model.get_value(var_i, True)
            cex.append(cex_i)
        return cex

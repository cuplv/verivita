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
        self.all_vars = set(self.ts.state_vars)
        self.all_vars.update(self.ts.input_vars)
        self.error = error

    def find_bug(self, k, incremental=False):
        """Explore the system up to k steps.

        Returns None if no bugs where found up to k or a
        counterexample otherwise.
        """

        if (not incremental):
            return self.find_bug_non_inc(k, None)
        else:
            return self.find_bug_inc(k, None)

    def _get_solver(self):
        solver = Solver(name='z3', logic=QF_BOOL)
        return solver

    def find_bug_non_inc(self, k, trace_enc=None):
        solver = self._get_solver()
        self.encode_up_to_k(solver, self.all_vars, k, trace_enc)
        logging.info("Finding bugs UP TO step %d..." % k)
        res = self.solve(solver, k)
        return res

    def encode_up_to_k(self, solver, all_vars, k, trace_enc=None):
        # Get the BMC encoding up to k
        error_condition = []
        for i in range(k + 1):
            # encode the i-th BMC step
            logging.debug("Encoding %d..." % i)

            f_at_i = self.get_ts_enc_at_i(i)
            solver.add_assertion(f_at_i)

            if (trace_enc is not None):
                tenc_at_i = self.get_trace_enc_at_i(i, trace_enc)
                solver.add_assertion(tenc_at_i)

            error_condition.append(self.helper.get_formula_at_i(self.all_vars,
                                                                self.error,
                                                                i))
        # error condition in at least one of the (k-1)-th states
        logging.debug("Error condition %s" % error_condition)
        solver.add_assertion(Or(error_condition))


    def find_bug_inc(self, k, trace_enc=None):
        solver = self._get_solver()

        res = None
        for i in range(k + 1):
            logging.info("Finding bugs at step %d..." % i)

            f_at_i = self.get_ts_enc_at_i(i)
            solver.add_assertion(f_at_i)

            if (trace_enc is not None):
                tenc_at_i = self.get_trace_enc_at_i(i, trace_enc)
                solver.add_assertion(tenc_at_i)

            solver.push()

            error_at_i = self.helper.get_formula_at_i(self.all_vars,
                                                      self.error,
                                                      i)
            solver.add_assertion(error_at_i)

            res = self.solve(solver, i)
            if res is not None:
                return res

            solver.pop()

        return res

    def simulate(self, trace_enc):
        """Simulate the trace
        """

        logging.info("Simulating a trace with %d messages" % len(trace_enc))

        solver = self._get_solver()

        sim_trace = None
        k = len(trace_enc)
        for i in range(k + 1):
            logging.info("Simulating step %d/%d" % (i, k))
            f_at_i = self.get_ts_enc_at_i(i)
            solver.add_assertion(f_at_i)

            tenc_at_i = self.get_trace_enc_at_i(i, trace_enc)
            solver.add_assertion(tenc_at_i)

            solver_res = solver.solve()
            if not solver_res:
                return (i, None, sim_trace)
            elif (i == k):
                assert solver_res
            logging.debug("Simulation encoding is satisfiable at step %d..." % (i+1))

            # TODO
            # assert the last step of the model in the encoding
            # just read the last step
            model = solver.get_model()
            sim_trace = self._build_trace(model, i)

        assert sim_trace is not None
        return (i+1, sim_trace, None)


    def get_ts_enc_at_i(self, i):
        if (i == 0):
            f_at_i = self.helper.get_formula_at_i(self.all_vars,
                                                  self.ts.init, i)
        else:
            f_at_i = self.helper.get_formula_at_i(self.all_vars,
                                                  self.ts.trans, i-1)
        return f_at_i

    def get_trace_enc_at_i(self, i, trace_enc, all_vars=None):
        if all_vars is None:
            all_vars = self.all_vars

        tenc = TRUE()
        if (i > 0):
            (state, next_state) = trace_enc[i-1]

            tenc_prev = self.helper.get_formula_at_i(all_vars,
                                                     state,
                                                     i-1)
            tenc_next = self.helper.get_formula_at_i(all_vars,
                                                     next_state,
                                                     i)
            tenc = And([tenc, tenc_prev, tenc_next])

        return tenc

    def solve(self, solver, k, build_trace=True):
        if (solver.solve()):
            logging.debug("The encoding is satisfiable...")
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
            if (i not in self.helper.time_memo):
                self.helper.get_formula_at_i(self.all_vars, TRUE(), i)

            cex_i = {}

            # skip the input variables in the last step
            if (i >= steps):
                vars_to_use = [self.ts.state_vars]

            for vs in vars_to_use:
                for var in vs:
                    assert var is not None
                    var_i = self.helper.get_var_at_time(var, i)
                    assert var_i is not None
                    cex_i[var] = model.get_py_value(var_i, True)
            cex.append(cex_i)
        return cex

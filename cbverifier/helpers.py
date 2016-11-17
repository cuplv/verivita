"""Helper functions, to understand where to put them.

TODO: memoization needs to be aware of the prefix
"""

from pysmt import shortcuts
from pysmt.shortcuts import Symbol, substitute

from pysmt.exceptions import UndefinedSymbolError

class Helper:
    def __init__(self,env):
        self.env = env
        self.time_memo = {}

    @staticmethod
    def get_next_var(var, mgr):
        """Given a variable returns the correspondent variable with the next suffix.
        It is used when describing transition relations (over var and var_next)
        """
        return Helper.get_new_var(var, mgr, None, "", "_next")

    @staticmethod
    def get_next_variables(vars, mgr):
        """As get_next_var for a set of variables.
        Returns a set (so no order is kept)
        """
        return Helper.get_new_variables(vars, mgr, None, "", "_next")

    @staticmethod
    def get_new_var(var, mgr, old2new_map, prefix, suffix):
        """Returns a variable named as
        <prefix>_var_<suffix> of the same type of var.

        If the variable does not exists it is created from scratch
        (so, do NOT expect a fresh variable here)
        """
        assert var.is_symbol()
        base = "%s%s%s" % (prefix, var.symbol_name(), suffix)
        try:
            new_symbol = mgr.get_symbol(base)
        except UndefinedSymbolError as e:
            new_symbol = Symbol(base, var.symbol_type())
            assert new_symbol != None
        if None != old2new_map:
            old2new_map[var] = new_symbol
        return new_symbol

    @staticmethod
    def get_new_variables(vars, mgr, old2new_map, prefix, suffix):
        """As get_new_var for a list of variables"""
        next_var_list = []
        for v in vars:
            assert v.is_symbol()
            next_symbol = Helper.get_new_var(v, mgr, old2new_map, prefix, suffix)
            next_var_list.append(next_symbol)
        return frozenset(next_var_list)

    def get_formula_at_i(self, vars, formula, i, prefix = "bmc_"):
        """Change formula replacing every variable var in vars with a variable
        named <prefix>_var_i and every variable var_next with a
        variable named <prefix>_var_j, where j is i+1.

        Example for i = 0, prefix = bmc_

        Input: (v & v_next) | p
        Output: (bmc_v_0 & bmc_v_1) | bmc_p_0
        """
        if i in self.time_memo:
            time_i_map = self.time_memo[i]
        else:
            time_i_map = {}

            Helper.get_new_variables(vars,
                                     self.env.formula_manager,
                                     time_i_map,
                                     prefix,
                                     "_%d" % i)

            app_map = {}
            Helper.get_new_variables(vars,
                                     self.env.formula_manager,
                                     app_map,
                                     prefix,
                                     "_%d" % (i+1))
            for k,v in app_map.iteritems():
                next_var = Helper.get_next_var(k, self.env.formula_manager)
                time_i_map[next_var] = v
            app_map = None

            self.time_memo[i] = time_i_map

        f_at_i = substitute(formula, time_i_map)
        return f_at_i


    def get_next_formula(self, vars, formula):
        """Given a formula returns the same formula where all the variables
        in vars are renamed to var_next"""
        next_map = {}
        Helper.get_new_variables(vars, self.env.formula_manager, next_map, "", "_next")

        next_formula = substitute(formula, next_map)
        return next_formula


    def get_var_at_time(self, var, time):
        """Returns the variable at time "time" or None if the var was
        not created"""
        assert var.is_symbol()
        if time in self.time_memo:
            if var in self.time_memo[time]:
                return self.time_memo[time][var]

        return None

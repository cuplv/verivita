""" Encode a counter with Boolean variables.

PySMT does not include a module to handle finite enumeratives.

We need counters to have a logarithmic encoding for the states of the
automata (other options are to use theories or better encoding with
sorting networks or ADDs).

"""


import math
from pysmt.typing import BOOL
import pysmt.shortcuts
from pysmt.shortcuts import Solver
from pysmt.shortcuts import Symbol, TRUE, FALSE
from pysmt.shortcuts import Not, And, Or


class CounterEnc():
    """ Class used to encode program counters with Boolean variables.

    """
    def __init__(self, pysmt_env, use_bdds = False):
        """
        pysmt_env: environment used to create the bdd package
        """
        self.use_bdds = use_bdds
        if (use_bdds):
            self.bdd_solver = Solver(env=pysmt_env, logic=pysmt.logics.BOOL,
                                     name='bdd')
            self.bdd_converter = self.bdd_solver.converter
        else:
            self.bdd_solver = None
            self.bdd_converter = None

        self.vars2bound = {}

    @staticmethod
    def _get_bitsize(max_values):
        if max_values == 0:
            return 1
        else:
            bitsize = int(math.floor(math.log(max_values,2)) + 1)
            return bitsize

    def _get_bitvar(self, var_name, bit_index):
        assert var_name  in self.vars2bound
        max_size = self.vars2bound[var_name]
        bitsize = CounterEnc._get_bitsize(max_size)
        assert bit_index < bitsize

        bit_var_name = "_bit_%s_%d" % (var_name, bit_index)
        return Symbol(bit_var_name, BOOL)


    def add_var(self, var_name, upper_bound):
        assert var_name not in self.vars2bound
        self.vars2bound[var_name] = upper_bound


    def eq_val(self, var_name, value, unsafe=False):
        """ Given a variable and a natural number value, produce the
        encoding for variable = value

        When unsafe is True, it allows to encode a number that is
        greater than the maximum value of the counter.
        This is needed to encode the bitmask (but it is bad for a
        standard usage)
        """

        def eq_val_rec(value, bit_list):
            """Get the boolean encoding for value and saves it in bit_list.

            For example, if value is 10 and bit_list = []
            bit_list at the end of the function will be [1,0,1,0]
            NOTE THE ORDER OF BITS: from the lower one to the higher one
            """
            if (value == 0):
                return bit_list
            else:
                remainder = value % 2
                div = value // 2

                if (remainder == 1): bit_list.append(True)
                else: bit_list.append(False)
                return eq_val_rec(div, bit_list)

        assert var_name in self.vars2bound
        max_size = self.vars2bound[var_name]
        assert unsafe or max_size >= value
        bitsize = CounterEnc._get_bitsize(max_size)

        bit_list = eq_val_rec(value, [])
        assert(bit_list is not None)

        assert(bitsize >= len(bit_list)) # otherwise we do not have enough bits to represent it

        bit_val_list = []
        for i in range(bitsize):
            """ var_name_bit_i = val """
            bit_at_time = self._get_bitvar(var_name, i)
            if (i < len(bit_list)):
                if bit_list[i]: bit_val_list.append(bit_at_time)
                else: bit_val_list.append(Not(bit_at_time))
            else: bit_val_list.append(Not(bit_at_time))
        bit_val = And(bit_val_list)
        assert(bit_val != None)

        return bit_val


    def get_mask(self, var_name):
        """ Returns the bitmask needed to ignore the additional unused
        bits used to encode the counter var_name.
        """

        # minimum number of bits to represent max_value
        assert var_name in self.vars2bound
        max_value = self.vars2bound[var_name]
        bitsize = CounterEnc._get_bitsize(max_value)

        # construct the bitmask: we do NOT want all the models
        i = max_value + 1
        mask = FALSE()
        max_value_with_bit = int(math.pow(2,bitsize)) - 1

        # print "Maximum value %d" % max_value
        # print "Number of bits %d" % bitsize
        # print "max_repr_value %d" % max_value_with_bit

        while i <= max_value_with_bit:
            single_val = self.eq_val(var_name, i, True)
            mask = Or(mask, single_val)
            i = i + 1
        assert(mask != None)
        mask = Not(mask)

        # TODO: get a compact representation using BDDs
        if (self.use_bdds):
            bdd_mask = self.bdd_converter.convert(mask)
            mask = self.bdd_converter.back(bdd_mask)

        return mask

    def get_counter_var(self, var_name):
        counter_vars = set()

        assert var_name in self.vars2bound
        max_value = self.vars2bound[var_name]
        bitsize = CounterEnc._get_bitsize(max_value)

        for i in range(bitsize):
            bitvar = self._get_bitvar(var_name, i)
            counter_vars.add(bitvar)

        return counter_vars

    # def encode_fc(self, append_to, counter_name, max_value, time_frame):
    #     bitsize = VarsDecl.get_bit_sizes(max_value)

    #     for i in range(bitsize):
    #         bi = self.vars_decl.get_bit_at_time(counter_name, i, time_frame)
    #         bi_next = self.vars_decl.get_bit_at_time(counter_name, i, time_frame + 1)
    #         append_to.append(Iff(bi, bi_next))
    #     return


    # def encode_sum(self, counter_name, max_value, time_frame):
    #     bitsize = VarsDecl.get_bit_sizes(max_value)

    #     adder_list = []
    #     carry = TRUE()
    #     assert(bitsize > 0)
    #     for i in range(bitsize):
    #         bi = self.vars_decl.get_bit_at_time(counter_name, i, time_frame)
    #         bi_next = self.vars_decl.get_bit_at_time(counter_name, i, time_frame + 1)

    #         current = Iff(bi_next, Xor(bi, carry))
    #         adder_list.append(current)
    #         carry = And(bi, carry)

    #     return And(adder_list)

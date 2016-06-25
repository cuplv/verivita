""" Data structure to represent a specification (a single rule, not
the whole specification)

NOTE: the spec also contains the associated results (weight, soundness..)

Implements the code that serialize the spec and enumerates the set of
specifications for a given alphabet.
"""

import logging
from scipy.stats.mstats import gmean
from numpy import float128
import numpy

from ctrace import CTraceSerializer

try:
    import simplejson as json
    from simplejson import JSONEncoder, JSONDecoder
except ImportError:
    import json
    from json import JSONEncoder, JSONDecoder

from fractions import Fraction

class SpecType:
    """Defines the possible types of a specifications.
    """
    Enable, Disable, Allow, Disallow = range(4)

    @staticmethod
    def negate(spec_type):
        if SpecType.Enable == spec_type: return SpecType.Disable
        elif SpecType.Disable == spec_type: return SpecType.Enable
        elif SpecType.Allow == spec_type: return SpecType.Disallow
        elif SpecType.Disallow == spec_type: return SpecType.Allow
        else:
            assert(False)

    @staticmethod
    def spec_from_str(typeStr):
        assert (typeStr == "enable" or typeStr == "disable" or
                typeStr == "allow" or typeStr == "disallow")

        if typeStr == "enable": return SpecType.Enable
        if typeStr == "disable": return SpecType.Disable
        if typeStr == "allow": return SpecType.Allow
        if typeStr == "disallow": return SpecType.Disallow

        assert False

    @staticmethod
    def get_desc(spec_type):
        if SpecType.Enable == spec_type: return "enable"
        elif SpecType.Disable == spec_type: return "disable"
        elif SpecType.Allow == spec_type: return "allow"
        elif SpecType.Disallow == spec_type: return "disallow"
        else:
            assert(False)

class Spec:
    def __init__(self, specType, src, dst):
        self.specType = specType

        # src symbol
        self.src = src
        # Callback symbol
        self.cb = None
        # dst symbol
        self.dst = dst

        # List of arguments for the src message
        self.src_args = []
        # List of arguments for the dst message
        self.dst_args = []
        # Callback parameters
        self.cb_args = []

    def get_print_desc(self):
        spec_desc = SpecType.get_desc(self.specType)
        desc = "Rule (%s[%s], %s[%s], %s[%s])" \
               % (rule.src, ",".join(rule.src_args),
                  rule.cb, ",".join(rule.cb_args),
                  rule.dst, ",".join(rule.dst_args))
        return desc

    def __eq__(self, other):
        return (self.specType == other.specType and
                self.src == other.src and
                self.dst == other.dst and
                self.cb == other.cb and
                self.src_args == other.src_args and
                self.dst_args == other.dst_args and
                self.cb_args == other.cb_args)

    def __hash__(self):
        return id(self)

    @staticmethod
    def get_specs_symbols(spec_list):
        """Returns all the symbols (src, dst, cb)
        contained in the rules of the spec.
        """
        symbols = set([])
        for r in spec_list:
            symbols.add(r.src)
            symbols.add(r.dst)
            if (r.cb != None): symbols.add(r.cb)
        return symbols

class SpecJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Spec):
            res = {"type" : obj.specType,
                   "src" : obj.src,
                   "dst" : obj.dst,
                   "cb" : obj.cb,
                   "src_args" : obj.src_args,
                   "dst_args" : obj.dst_args,
                   "cb_args" : obj.cb_args}
            return res
        elif isinstance(obj, Fraction):
            res = {"num" : str(obj.numerator),
                   "den" :str(obj.denominator)}
            return res
        else:
            return json.JSONEncoder.default(self, obj)


class SpecSerializer:
    @staticmethod
    def write_specs(spec_list, outfile):
        json.dump({"specs" : spec_list},
                  outfile,cls=SpecJSONEncoder, allow_nan=True)

    @staticmethod
    def read_specs(infile):
        def read_frac(d):
            if ('num' not in d):
                raise Exception(str(d) + " is not a fraction")
            if ('den' not in d):
                raise Exception(str(d) + " is not a fraction")
            num = int(d.pop('num'))
            den = int(d.pop('den'))
            return Fraction(num,den)

        def read_spec(d):
            """Read a single spec"""
            assert 'type' in d and 'match' in d and 'change' in d

            specType = SpecType.spec_from_str(d['type'])

            spec = Spec(specType, "","")
            
            # match
            match_json = d['match']

            assert (len(match_json.keys()) <= 2) 
            # at least an event or a callin
            assert ('event' in match_json or 'callin' in match_json)
            # there is a callback only when there is an event (callback -> event)
            assert ((not 'callback' in match_json) or ('event' in match_json))

            
            if 'event' in match_json:
                message_data = match_json["event"]
            elif 'callin' in match_json:
                message_data = match_json["callin"]

            spec.src = CTraceSerializer.get_message_symbol(message_data["signature"],
                                                           message_data["concreteArgsVariables"])
            spec.src_args = list(message_data["concreteArgsVariables"])

            if 'callback' in match_json:
                cb_data = match_json['callback']
                spec.cb = CTraceSerializer.get_message_symbol(cb_data["signature"],
                                                              cb_data["concreteArgsVariables"])
                spec.cb_args = list(cb_data["concreteArgsVariables"])
            
            # change
            change_json = d["change"]
            assert (len(change_json.keys()) == 1)
            # no callbacks in change
            assert ('event' in change_json or 'callin' in change_json)

            if 'event' in change_json:
                message_data = change_json["event"]
            elif 'callin' in change_json:
                message_data = change_json["callin"]

            spec.dst = CTraceSerializer.get_message_symbol(message_data["signature"],
                                                           message_data["concreteArgsVariables"])
            spec.dst_args = list(message_data["concreteArgsVariables"])

            return spec

        # Read the specification file
        with infile as data_file:
            data = json.load(data_file)
            
#        assert 'specs' in data
        specs = []
        for elem in data:
            specs.append(read_spec(elem))

        return specs

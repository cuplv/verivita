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
               % (self.src, ",".join(self.src_args),
                  self.cb, ",".join(self.cb_args),
                  self.dst, ",".join(self.dst_args))
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

class Binding:
    def __init__(self, event, callback):
        self.event = event
        self.cb = callback

        self.event_args = []
        self.cb_args = []
        
class SpecSerializer:
    "Read a list of specs and bindings" 

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

        def read_msg(message_data):
            assert ("signature" in message_data and 
                    "concreteArgsVariables" in message_data)

            signature = CTraceSerializer.get_message_symbol(message_data["signature"],
                                                            message_data["concreteArgsVariables"])
            args = list(message_data["concreteArgsVariables"])

            return (signature, args)
            
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
            
        
        def read_spec(d):
            """Read a single spec"""
            assert 'type' in d and 'match' in d and 'change' in d

            specType = SpecType.spec_from_str(d['type'])

            spec = Spec(specType, "","")
            
            # match
            match_json = d['match']

            assert (len(match_json.keys()) == 1) 
            # at least an event or a callin
            assert ('event' in match_json or 'callin' in match_json)
            assert ('callback' not in match_json)
            # there is a callback only when there is an event (callback -> event)
            
            if 'event' in match_json:
                message_data = match_json["event"]
            elif 'callin' in match_json:
                message_data = match_json["callin"]

            (spec.src, spec.src_args) = read_msg(message_data)
            
            # change
            change_json = d["change"]
            assert (len(change_json.keys()) == 1)
            # no callbacks in change
            assert ('event' in change_json or 'callin' in change_json)

            if 'event' in change_json:
                message_data = change_json["event"]
            elif 'callin' in change_json:
                message_data = change_json["callin"]
            (spec.dst, spec.dst_args) = read_msg(message_data)

            assert spec != None
            return spec

        def read_binding(d):
            assert "event" in d and "callback" in d
            assert len(d) == 2 # exactly one event and one callback

            binding = Binding("", "")

            (binding.event, binding.event_args) = read_msg(d["event"])
            (binding.cb, binding.cb_args) = read_msg(d["callback"])

            return binding
        
        # Read the specification file
        with infile as data_file:
            data = json.load(data_file)
            
        assert "specs" in data
        assert "bindings" in data
        specs = []
        for elem in data["specs"]:            
            specs.append(read_spec(elem))
        bindings = []
        for elem in data["bindings"]:
            bindings.append(read_binding(elem))        

        return {'specs' : specs, 'bindings' : bindings}



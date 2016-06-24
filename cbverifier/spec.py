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

try:
    import simplejson as json
    from simplejson import JSONEncoder, JSONDecoder    
except ImportError:
    import json
    from json import JSONEncoder, JSONDecoder
    
from fractions import Fraction

class LetterType:
    """Define the type of a letter in the trace.
    """
    Event, Callin = range(2)


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
    def get_desc(spec_type):
        if SpecType.Enable == spec_type: return "enable"
        elif SpecType.Disable == spec_type: return "disable"
        elif SpecType.Allow == spec_type: return "allow"
        elif SpecType.Disallow == spec_type: return "disallow"
        else:
            assert(False)    


def weight_in_range(weight):
    return weight == Fraction(-1,1) or (weight >= Fraction(0,1) and weight <= Fraction(1,1))
            
class SpecStatus: NotDone,Done,Timeout = [0,1,-1]
class Spec:    
    def __init__(self, specType, src, dst):
        self.specType = specType
        self.src = src
        self.dst = dst

        # List of arguments for the src message
        # Arguments is just a list of strings
        self.src_args = []
        # List of arguments for the dst message 
        self.dst_args = []

        # Callback symbol
        self.cb = None
        # Callback parameters
        self.cb_args = []
        
        # Learning stuff of the spec
        self.weight = Fraction(-1,1)
        self.status = SpecStatus.NotDone
        self.succintness = []
        
    def get_print_desc(self):
        spec_desc = SpecType.get_desc(self.specType)
        desc = "%s\t%s\t%s\t%s" % (self.src, spec_desc, self.dst, float(self.weight))
        return desc

    def __eq__(self, other):        
        return (self.specType == other.specType and
                self.src == other.src and
                self.dst == other.dst and
                self.cb == other.cb and
                self.src_args == other.src_args and
                self.dst_args == other.dst_args and
                self.cb_args == other.cb_args and
                self.weight == other.weight and
                self.status == other.status and
                set(self.succintness) == set(other.succintness))

    def __hash__(self):
        return id(self)

    @staticmethod
    def get_specs_symbols(spec_list):
        """Returns all the symbols (both src and dst)
        contained in the rules of the spec.
        """
        symbols = set([])
        for r in spec_list:
            symbols.add(r.src)
            symbols.add(r.dst)
        return symbols

    def update_succintness(spec, weight, ratio):
        found = False
        for i in range(len(spec.succintness)):
            (w,r) = spec.succintness[i]            
            if w == weight:
                spec.succintness[i] = (w, ratio)
                found = True
        if not found:
            spec.succintness.append((weight, ratio))
                    
    
    
    @staticmethod
    def merge_specs(spec_list):
        spec_weight = {}
        # map from weight to sum
        soundness_app = {}
        # map from weight to sum
        gv_succ_map = {}
        
        # map from to a rule to sum
        succintness_app = {}
        for spec in spec_list:
            (_, _, specs, soundness, gv_succ) = spec

            for (w, val) in soundness:
                if w not in soundness_app: soundness_app[w] = 0
                soundness_app[w] = soundness_app[w] + val
            for (w, val) in gv_succ:
                if w not in gv_succ_map:
                    gv_succ_map[w] = 0
                else: gv_succ_map[w] = gv_succ_map[w] + val
                
            for rule in specs:
                key = (rule.src, rule.specType, rule.dst)
                
                if not key in spec_weight:
                    spec_weight[key] = rule.weight
                else:
                    spec_weight[key] = spec_weight[key] + rule.weight

                if key not in succintness_app:
                    succintness_app[key] = {}
                
                for (w, val) in rule.succintness:
                    if w not in succintness_app[key]:
                        succintness_app[key][w] = 0
                    succintness_app[key][w] = succintness_app[key][w] + val

        # we count as 0 the succintness of the rules not present in a spec
        total_rules = len(spec_list)
        merged_rules = []
        for key, succ_map in succintness_app.iteritems():
            (src, specType, dst) = key
            rule = Spec(specType, src, dst)
            rule.status = SpecStatus.Done
            for w,v in succ_map.iteritems():
                rule.succintness.append((w, Fraction(v, total_rules)))
            assert key in spec_weight
            rule.weight = spec_weight[key] / total_rules                
            merged_rules.append(rule)

        merged_soundness = []        
        for w,v in soundness_app.iteritems():
            merged_soundness.append((w, Fraction(v, len(spec_list))))
        merged_gv_succ = []
        for w,v in gv_succ_map.iteritems():
            # arithmetic mean among samples
            merged_gv_succ.append((w, Fraction(v, len(spec_list))))

        res_spec = ("", Fraction(0,1), merged_rules, merged_soundness, merged_gv_succ)
        return res_spec

    @staticmethod
    def get_gv_succ(spec_list):    
        weight_map = {}        
        for s in spec_list:
            for (w,v) in s.succintness:
                if w not in weight_map:
                    weight_map[w] = [v]
                else:
                    weight_map[w].append(v)

        gv_succ = []
        for weight, val_list in weight_map.iteritems():
            samples = [float128(suc_val) for suc_val in val_list]
            geo_mean = gmean(samples, axis=0)
            if geo_mean is numpy.ma.masked:
                gv_succ.append((weight, Fraction(2,0)))
            else:
                gv_succ.append((weight, Fraction.from_float(float(geo_mean))))
            
        return gv_succ

class SpecStat():
    """Contains the statistics copmuted for a specification.
    """
    def __init__(self, weight, trace_name, removed_rules, sound):
        """
        trace_name: name of the trace (string)
        removed_rules: list of indexes of the removed rules (the index correspond to the position of the rule in the specs)
        sound: true if the rule is sound for the trace
        """
        self.weight = weight
        self.trace_name = trace_name
        self.removed_rules = removed_rules
        self.sound = sound
    
    
class SpecIterator():
    """ Generate the possible set of specifications for a list of events

    If we have n distinct events and callback, then the number of all
    possible specifications is the following:
    TOT_SPEC(n) = 2 * (n-1)           + # number of i -> +- e
                  n-1                 + # number of e -> - e 
                  2 * (n-1)(n-2)   2    # number of e_j -> +/- e_k
    """
    def __init__(self, trace):
        start_evt = trace.get_init_evt()
        set_evt = set(trace.alphabet)
        set_evt.remove(start_evt)
        evt_list = list(set_evt)
        evt_list.sort()
        self.events = [start_evt] + evt_list

        self.trace = trace
        
        # Int => Bool => SpecType
        self.spec_type_map = {
            0 : {LetterType.Event : SpecType.Disable, LetterType.Callin : SpecType.Disallow},
            1 : {LetterType.Event : SpecType.Enable, LetterType.Callin : SpecType.Allow}
        }
        
        # state of the iterator
        self.src_evt_index = 0
        self.dst_evt_index = 1 # start event can never be on the rhs
        # Plus = Enable | Allow (this choice depends on dst symbol)
        # Minus = Disable | Disallow
        self.next_spec = 0

    def get_estimate(self):
        """Returns the number of possible specifications.
        """
        n = len(self.events)
        n_m_1 = (n - 1)
        tot = 2 * n_m_1 + n_m_1 + 2 * (n_m_1) * (n - 2)
        return tot
            
    def _is_start_event(self, evt):
        evt == self.events[0]    
        
    def __iter__(self):
        return self

    def next(self):
        """Returns a Spec or raise an exception.
        spec_type: type of specification (enable, disalbe, allow, disallow)
        src: action that enables/disables/allow/disallow
        dst: action that is enabled/disabled/allowed/disallowed

        """
        if (self.next_spec == 2 or
            (1 == self.next_spec and
             self.src_evt_index == self.dst_evt_index)):
            # visited all spec type, pick next element
            logging.debug("Visited all spec for %s %s",
                         self.src_evt_index, self.dst_evt_index)

            self.dst_evt_index = self.dst_evt_index + 1
            self.next_spec = 1
            
            if (self.dst_evt_index >= len(self.events)):
                self.dst_evt_index = self.dst_evt_index + 1

                # visited all dst elements, take the next dst event
                self.src_evt_index = self.src_evt_index + 1
                self.dst_evt_index = 1 # never care about the initial symbol again

                if (self.src_evt_index >= (len(self.events))):
                    # src is the last element, nothing to do
                    raise StopIteration()
        else:
            logging.debug("Inc current spec type (%d) for %s %s" %
                          (self.next_spec, self.src_evt_index, self.dst_evt_index))

            self.next_spec = self.next_spec + 1
           
        assert(self.dst_evt_index < len(self.events))
        assert(self.src_evt_index < len(self.events))
        dst_evt = self.events[self.dst_evt_index]

        assert(self.next_spec > 0 and self.next_spec <= 2)
        spec_map = self.spec_type_map[self.next_spec - 1]
        
        spec_type = spec_map[self.trace.get_type(dst_evt)]
        
        return Spec(spec_type,
                    self.events[self.src_evt_index],
                    dst_evt)

class SpecJSONEncoder(JSONEncoder):
    def default(self, obj):        
        if isinstance(obj, Spec):
            res = {"type" : obj.specType,
                   "src" : obj.src,
                   "dst" : obj.dst,
                   "cb" : obj.cb,
                   "src_args" : obj.src_args,
                   "dst_args" : obj.dst_args,
                   "cb_args" : obj.cb_args,
                   "weight" : self.default(obj.weight),
                   "status" : obj.status,
                   "succintness" : obj.succintness}            
            return res
        elif isinstance(obj, SpecStat):
            res = {"trace_name" : obj.trace_name,
                   "removed_rules" : obj.removed_rules,
                   "sound" : obj.sound,
                   "weight" : obj.weight}
            return res            
        elif isinstance(obj, Fraction):
            res = {"num" : str(obj.numerator),
                   "den" :str(obj.denominator)}
            return res
        else:
            return json.JSONEncoder.default(self, obj)

        
class SpecSerializer:
    @staticmethod
    def write_specs(src_trace, tot_traces, spec_list, outfile, soundness=None, stats_list=None, gv_succ=None):
        if soundness == None: soundness = []
        if gv_succ == None: gv_succ = []
        
        # Relax the assertion:
        # the hmm spec mining assign weights that may not be in the [0,1] range
        # for rule in spec_list: assert(weight_in_range(rule.weight))
        json.dump({"src_trace" : src_trace,
                   "total" : tot_traces,
                   "specs" : spec_list,
                   "soundness" : soundness,
                   "stats" : stats_list,
                   "gv_succ" : gv_succ},
                  outfile,cls=SpecJSONEncoder,allow_nan=True)

    @staticmethod
    def read_specs(infile, soundness=False, stats_list=False, gv_succ=False):
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

            assert 'type' in d and 'src' in d and 'dst' in d and 'weight' in d            
            specType = d.pop('type')
            src = d.pop('src')
            dst = d.pop('dst')
            weight = read_frac(d.pop('weight'))
            res = Spec(specType, src,dst)
            res.weight = weight

            # read the cb 
            if 'cb' in d: res.cb = d['cb']
            # read the arguments
            args_to_read = [('src_args', res.src_args),
                            ('dst_args', res.dst_args),
                            ('cb_args', res.cb_args)]
            for (label, field) in args_to_read:
                if label in d:
                    for l in d[label]: field.append(l)
                    
            # relax assertion:
            # the hmm spec mining assign weights that may not be in the [0,1] range
            # assert(weight_in_range(res.weight))            
            if "status" in d:
                res.status = d["status"]

            # Reads the succintness value of the specification
            if "succintness" in d:
                res.succintness = []
                for l in d['succintness']:
                    assert(len(l) == 2)
                    res.succintness.append((read_frac(l[0]),
                                            read_frac(l[1])))
            else:
                res.succintness = []

            return res

        assert (not stats_list) or soundness
        
        # Read the specification file
        with infile as data_file:
            data = json.load(data_file)

        src_trace = data['src_trace']
        try:
          total = read_frac(data['total'])
        except:
          total = Fraction(0, 1)

        specs = []
        for d in data['specs']:
            specs.append(read_spec(d))

        # Read soundness
        if "soundness" in data:
            res_sound = []
            for l in data['soundness']:
                assert(len(l) == 2)
                res_sound.append((read_frac(l[0]),
                                  read_frac(l[1])))
        else:
            res_sound = []

        # Read spec stats
        spec_stats = []
        if "stats" in data and None != data["stats"]:
            for stat_map in data["stats"]:
                assert("trace_name" in stat_map)
                assert("removed_rules" in stat_map)
                assert("sound" in stat_map)
                if stat_map["weight"] == None:
                    w = None
                else:
                    w = read_frac(stat_map["weight"])
                
                s = SpecStat(w,
                             stat_map["trace_name"],
                             stat_map["removed_rules"],
                             stat_map["sound"])
                spec_stats.append(s)

        # read the global value  of succintness
        if "gv_succ" in data:
            res_succ = []
            for l in data['gv_succ']:
                assert(len(l) == 2)
                res_succ.append((read_frac(l[0]),
                                 read_frac(l[1])))
        else:
            res_succ = []
            
        res = (src_trace, total, specs)
        if soundness:
            res = res + (res_sound,)
            if stats_list:
                res = res + (spec_stats,)
                if gv_succ:
                    res = res + (res_succ,)
        return res

""" Concrete trace data structure and parsing.
"""

import json # for reading the traces from file
import re

from counting.trace import LetterType, TraceSerializer

class CCallback:
    """ Represent a concrete callback (cb)
    """
    def __init__(self, symbol):
        # object involved in the cb
        self.symbol = symbol
        self.args = []
        self.cb_types = []
        
        # list of callins
        self.ci = []

class CCallin:
    """ Concrete callin.
    """
    def __init__(self, symbol, ci_type):
        # object
        assert symbol != None        
        self.symbol = symbol
        
        # list of all the object arguments
        self.args = []

        # type
        self.ci_type = None
        
class CEvent:
    """ Represent a concrete event.
    """
    def __init__(self, symbol):
        # name of the event
        self.symbol = symbol

        # arguments of the event
        self.args = []
        
        # list of callbacks
        self.cb = []
    
class ConcreteTrace:
    
    def __init__(self):
        self.events = []

class CTraceSerializer:
    
    @staticmethod
    def read_trace(input_file):
        """ Read a trace from a json file."""
        with input_file as data_file:    
            data = json.load(data_file)

        TraceSerializer.check_keys(data, ["events"])

        ctrace = ConcreteTrace()
        for event_json in data["events"]:
            TraceSerializer.check_keys(event_json, ["initial"])
            # skip the initial event
            if (event_json["initial"] == "true"): continue

            event = CTraceSerializer.read_event(event_json)
            ctrace.events.append(event)
        
        return ctrace


    @staticmethod
    def read_event(data):
        """Read a single event."""
        evt_field = ["callbackObjects", "eventIdentifier"]
        TraceSerializer.check_keys(data, evt_field)

        # read the event
        event_symbol = TraceSerializer._tr_get_event_key(data["eventIdentifier"])
        event = CEvent(event_symbol)

        if "concreteArgs" in data:
            event.args = data["concreteArgs"]
        else:
            event.args = []
            
        # read the list of callbacks
        for cb_json in data["callbackObjects"]:
            if cb_json != "null":
                cb = CTraceSerializer.read_cb(cb_json)
                event.cb.append(cb)
        
        return event

    @staticmethod
    def read_cb(cb_json):
        """Read a single callback."""
        TraceSerializer.check_keys(cb_json, ["id", "cbObjects", "callinList"])

        cb = CCallback(cb_json["id"])

        # Read the cb objects
        for obj_str in cb_json["cbObjects"]:
            match = re.search('([a-zA-Z\. \(\)]+)@([0-9]+)', obj_str)
            assert match
            obj_type = match.group(1)
            obj = match.group(2)
            cb.args.append(obj)
            cb.cb_types.append(obj_type)

        # read the list of callins
        for ci_json in cb_json["callinList"]:
            ci = CTraceSerializer.read_ci(ci_json)
            cb.ci.append(ci)
                                   
        return cb

    @staticmethod
    def read_ci(ci_json):
        ci_fields = ["booleanArgs",
                     "concreteArgs",
                     "name",
                     "signature",
                     "type"]
        TraceSerializer.check_keys(ci_json, ci_fields)


        symbol = TraceSerializer._tr_get_callin_key(ci_json)
        ci_type = ci_json["type"]
        ci = CCallin(symbol, ci_type)

        for obj in ci_json["concreteArgs"]:
            ci.args.append(obj)        
        
        return ci

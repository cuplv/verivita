""" Concrete trace data structure and parsing.
"""

import json # for reading the traces from file
import re

from counting.trace import LetterType, TraceSerializer

class CCallback:
    """ Represent a concrete callback (cb)
    """
    def __init__(self, obj, obj_type):
        # object involved in the cb
        self.obj = obj
        self.obj_type = obj_type

class CCallin:
    """ Concrete callin.
    """
    def __init__(self, symbol, receiver, ci_type):
        # object 
        self.symbol = None
        # Receiver object
        self.receiver = None        
        # list of all the object arguments
        self.obj_args = []
        # type
        self.ci_type = None
        
class CEvent:
    """ Represent a concrete event.
    """
    def __init__(self, symbol):
        # name of the event
        self.symbol = symbol
        # list of callbacks
        self.cb = []
        # list of callins
        self.ci = []
    
class ConcreteTrace:
    
    def __init__(self):
        self.events = []
        self.objects = set()

class CTraceSerializer:
    
    @staticmethod
    def read_trace(input_file):
        """ Read a trace from a json file."""
        with input_file as data_file:    
            data = json.load(data_file)

        TraceSerializer.check_keys(data, ["events"])

        for event_json in data["events"]:
            TraceSerializer.check_keys(event_json, ["initial"])
            # skip the initial event
            if (event_json["initial"] == "true"): continue

            event = CTraceSerializer.read_event(event_json)
            


    @staticmethod
    def read_event(data):
        """Read a single event."""
        evt_field = ["callbackObjects", "callinList",
                     "eventIdentifier"]
        TraceSerializer.check_keys(data, evt_field)

        # read the event
        event_symbol = TraceSerializer._tr_get_event_key(data["eventIdentifier"])
        event = CEvent(event_symbol)

        # read the list of callbacks
        for cb_json in data["callbackObjects"]:
            if cb_json != "null":
                cb = CTraceSerializer.read_cb(cb_json)
                event.cb.append(cb)

        # read the list of callins
        for ci_json in data["callinList"]:
            ci = CTraceSerializer.read_ci(ci_json)            
            event.ci.append(cb)
        
        return event

    @staticmethod
    def read_cb(cb_json):
        """Read a single callback."""
        match = re.search('([a-zA-Z\. \(\)]+)@([0-9]+)', cb_json)
        assert match

        obj_type = match.group(1)
        obj = match.group(2)

        cb = CCallback(obj, obj_type)
        
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
        # TODO
        receiver = None
        ci = CCallin(symbol, receiver, ci_type)

        for obj in ci_json["concreteArgs"]:
            ci.obj_args.append(obj)        
        
        return ci

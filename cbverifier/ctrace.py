""" Concrete trace data structure and parsing.
"""

import json # for reading the traces from file
import re

class CCallback:
    """ Represent a concrete callback (cb)
    """
    def __init__(self, symbol):
        # object involved in the cb
        self.symbol = symbol
        self.args = []
        
        # list of callins
        self.ci = []

class CCallin:
    """ Concrete callin.
    """
    def __init__(self, symbol):
        # object
        assert symbol != None        
        self.symbol = symbol
        
        # list of all the object arguments
        self.args = []
        
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
    def check_keys(data, keys):    
        for key in keys:
            if (key not in data):
                raise Exception("%s key is not in the input json file\n%s" % (str(key), data))
    
    @staticmethod
    def read_trace(input_file):
        """ Read a trace from a json file."""
        with input_file as data_file:    
            data = json.load(data_file)

        CTraceSerializer.check_keys(data, ["events"])

        ctrace = ConcreteTrace()
        for event_json in data["events"]:
            CTraceSerializer.check_keys(event_json, ["initial"])
            # skip the initial event
            if (event_json["initial"] == "true"):
                event = CEvent("initial")
            else:
                event = CTraceSerializer.read_event(event_json)
            ctrace.events.append(event)
        
        return ctrace

    @staticmethod
    def get_message_symbol(signature, args):
        bool_args = []
        for arg_str in args:
            if (arg_str == "true" or arg_str == "false"):
                bool_args.append(arg_str)
        if len(bool_args) > 0:
            signature = signature + "_" + "_".join(bool_args)
        return signature
    
    @staticmethod
    def read_event(data):
        """Read a single event."""
        evt_field = ["callbackObjects", "signature"]
        CTraceSerializer.check_keys(data, evt_field)

        # read the event
        event_symbol = data["signature"]
        symbol = CTraceSerializer.get_message_symbol(data["signature"],
                                                     data["concreteArgs"])
        event = CEvent(symbol)

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
        CTraceSerializer.check_keys(cb_json, ["signature", "concreteArgs", "callinList"])

        symbol = CTraceSerializer.get_message_symbol(cb_json["signature"],
                                                     cb_json["concreteArgs"])
        cb = CCallback(symbol)
        cb.args = list(cb_json["concreteArgs"])

            # OLD MATCH ON OBJECTS
            # match = re.search('([a-zA-Z\. \(\)]+)@([0-9]+)', obj_str)
            # assert match
            # obj_type = match.group(1)
            # obj = match.group(2)
            # cb.args.append(obj)

        # read the list of callins
        for ci_json in cb_json["callinList"]:
            ci = CTraceSerializer.read_ci(ci_json)
            cb.ci.append(ci)
                                   
        return cb

    @staticmethod
    def read_ci(ci_json):
        ci_fields = ["signature", "concreteArgs"]
        CTraceSerializer.check_keys(ci_json, ci_fields)

        symbol = CTraceSerializer.get_message_symbol(ci_json["signature"],
                                                     ci_json["concreteArgs"])
        ci = CCallin(symbol)
        ci.args = list(ci_json["concreteArgs"])

        return ci

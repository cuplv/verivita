""" Concrete trace data structure and parsing.
"""

from counting import LetterType

class CCallback:
    """ Represent a concrete callback (cb)
    """
    def __init__(self):
        # list of objects involved in the cb
        self.objects = []

class CCallin:
    """ Concrete callin.
    """
    def __init__(self):
        # object 
        self.symbol = None
        # Receiver object
        self.receiver = None        
        # list of all the object arguments
        self.obj_args = []
        # type
        self.type = None
        
class CEvent:
    """ Represent a concrete event.
    """
    def __init__(self):
        # name of the event
        self.symbol = None
        # list of callbacks
        self.cb = []
        # list of callins
        self.ci = []
    
class ConcreteTrace:
    
    def __init__(self):
        self.events = []
        self.objects = set()

    

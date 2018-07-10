# Miscellaneous utility functions
#
import logging

def is_debug():
    """ Return true if the logging level is debug """
    return (logging.getLogger().getEffectiveLevel() == logging.DEBUG)

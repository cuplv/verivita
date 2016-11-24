""" Test the specification package

"""

import logging
import unittest

from ply.lex import LexToken
import ply.yacc as yacc


try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cbverifier.specs.spec import Spec


class TestSpecs(unittest.TestCase):

    def test_spec_creation(self):
        spec_list = Spec.get_specs_from_string("SPEC [CI] [l] void method_name() |- TRUE; " +
                                               "SPEC [CI] [l] void method_name() |- TRUE;" +
                                               "SPEC [CI] [b] void android.widget.Button.setOnClickListener(l) |+ [CB] [l] void onClick(b);" +
                                               "SPEC TRUE[*]; [CI] [b] void android.widget.Button.setOnClickListener(l) |+ [CB] [l] void onClick(b)")
        self.assertTrue(len(spec_list) == 4)

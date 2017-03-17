""" Implementation of a bi-directional map.

The implementation is dumb now, it uses two maps to store both directions.
It is not used in performance critical code, so it is not an issue for now.


"""

class BiMap:
    def __init__(self):
        self.a2b = {}
        self.b2a = {}

    def add(self,a,b):
        self.a2b[a] = b
        self.b2a[b] = a

    def lookup_a(self,a):
        return self.a2b[a]

    def lookup_b(self,b):
        return self.b2a[b]

    def iteritems_a_b(self):
        return self.a2b.iteritems()

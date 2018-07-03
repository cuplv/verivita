"""
Computes a set of properties of the model for a
specific trace.
"""

from cbverifier.specs.spec_ast import *
from cbverifier.encoding.grounding import TraceMap
from cbverifier.specs.spec_parser import spec_parser
import string

class AttachRelation:
    """ Computes the attachment relation between objects """
    def __init__(self, trace_map, root_components):
        """ List of concrete object values of root components
        used to start the reachability analysis.

        They should be Activity objects.
        """

        attach_methods = {'android.app.Activity' : ['L = [CI] [EXIT] [${CONTAINER}] android.view.View android.app.Activity.findViewById(# : int)']}

        rc = ObjBinRelComputation(trace_map,
                                  "CONTAINER",
                                  "L",
                                  attach_methods)
        # Represent the containment relation
        # as a -> [b,c] if a contains b and c
        # (or b/c is attached to a).
        self._is_contained = rc.compute_relation(root_components)


    """
    Returns the list of components attached to obj
    """
    def get_attached(self, obj):
        if obj in self._is_contained:
            return self._is_contained[obj]
        else:
            return []

    def is_attached(self, obj_a, obj_b):
        if obj_a in self._is_contained:
            return obj_b in self._is_contained[obj_a]
        else:
            return []


class ObjBinRelComputation:
    """ Generic class used to compute binary relations of
    objects in a trace
    """

    def __init__(self, trace_map,
                 src_placeholder,
                 dst_var_name,
                 relation_map):
        """
        relation_map is a map that organizes the list of methods
        that can relate one object to another one.

        The method are organized by class of the src object.
        Each method uses the variable dst_var_name to refer to the object
        that is related src_placeholder as the placeholder to substitute the
        src object id.
        """
        self.trace_map = trace_map
        self.src_placeholder = src_placeholder
        self.dst_var_name = dst_var_name
        self.relation_map = relation_map


    def compute_relation(self, root_objects):
        relation = {}
        stack = list(root_objects)
        while (0 < len(stack)):
            obj_val = stack.pop()
            if obj_val not in relation:
                # get all the objects could be related to object
                related_objects = self._get_related_objs(obj_val)
                related_obj_set = set()
                for dst_obj in related_objects:
                    related_obj_set.add(dst_obj)
                    stack.append(dst_obj)
                relation[obj_val] = related_obj_set
        return relation


    def _get_related_objs(self, obj):
        """
        Get the list of objects that can be used to attach something
        to obj.
        """
        dst_var_ast = new_id(self.dst_var_name)
        if (obj.type in self.relation_map):
            generic_method_list = self.relation_map[obj.type]
            for m_template in generic_method_list:
                # replace the placeholder in m
                subs = {self.src_placeholder : obj.get_value()}
                m_replaced_str = string.Template(m_template).safe_substitute(subs)

                # parse m_replaced
                m_ast = spec_parser.parse_call(m_replaced_str)
                if (m_ast is None):
                    raise Exception("Error parsing %s" % m_replaced_str)
                related_objs = self.trace_map.find_all_vars(m_ast, dst_var_ast)
                return related_objs
        else:
            return []

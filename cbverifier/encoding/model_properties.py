"""
Computes a set of properties of the model for a
specific trace.
"""

from cbverifier.specs.spec_ast import *
from cbverifier.encoding.grounding import TraceMap
from cbverifier.specs.spec_parser import spec_parser
import string

class BinRelation:
    """ Generic class used to compute binary relations of
    objects in a trace
    """

    def __init__(self, trace_map,
                 src_placeholder,
                 dst_var_name,
                 relation_map_forward,
                 relation_map_backward,
                 root_objects):
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
        self.relation_map_forward = relation_map_forward
        self.relation_map_backward = relation_map_backward
        self.root_objects = root_objects

        self.relation = {}
        self._compute_relation(self.root_objects)

    def _compute_relation(self, root_objects):
        self.relation = {}
        stack = list(root_objects)
        while (0 < len(stack)):
            obj_val = stack.pop()

            # compute the forward relation
            related_objects = self._get_related_objs(obj_val,
                                                     self.relation_map_forward,
                                                     True)
            if not obj_val in self.relation:
                ro = set()
                self.relation[obj_val] = ro
            else:
                ro = self.relation[obj_val]
            for dst_obj in related_objects:
                ro.add(dst_obj)
                stack.append(dst_obj)

            # compute the backward relation
            related_objects = self._get_related_objs(obj_val,
                                                     self.relation_map_backward,
                                                     False)
            for dst_obj in related_objects:
                if dst_obj not in self.relation:
                    self.relation[dst_obj] = set()
                self.relation[dst_obj].add(obj_val)

    def _get_related_objs(self, obj, relation_map, forward=True):
        """
        Get the list of objects that can be used to attach something
        to obj.
        """
        if (obj.type in relation_map):
            generic_method_list = relation_map[obj.type]
            for m_template in generic_method_list:
                if (forward):
                    var_to_search_for = new_id(self.dst_var_name)
                    subs = {self.src_placeholder : obj.get_value()}
                else:
                    var_to_search_for = new_id(self.src_placeholder)
                    subs = {self.dst_var_name : obj.get_value()}

                m_replaced_str = string.Template(m_template).safe_substitute(subs)

                # parse m_replaced
                m_ast = spec_parser.parse_call(m_replaced_str)
                if (m_ast is None):
                    raise Exception("Error parsing %s" % m_replaced_str)
                related_objs = self.trace_map.find_all_vars(m_ast,
                                                            var_to_search_for)
                return related_objs
        else:
            return []


    """
    Returns the list of components attached to obj
    """
    def get_related(self, obj):
        if obj in self.relation:
            return self.relation[obj]
        else:
            return []

    def is_related(self, obj_a, obj_b):
        if obj_a in self.relation:
            return obj_b in self.relation[obj_a]
        else:
            return []


class AttachRelation(BinRelation):

    attach_methods_fwd = {'android.app.Activity' : ['L = [CI] [EXIT] [${CONTAINER}] android.view.View android.app.Activity.findViewById(# : int)']}
    attach_methods_bwd = {'android.app.Fragment' : ['[CB] [ENTRY] [${L}] void android.app.Fragment.onAttach(CONTAINER : android.app.Activity)']}

    """ Computes the attachment relation between objects """
    def __init__(self, trace_map, root_components):
        """ List of concrete object values of root components
        used to start the reachability analysis.

        They should be Activity objects.
        """

        BinRelation.__init__(self, trace_map,
                             "CONTAINER",
                             "L",
                             AttachRelation.attach_methods_fwd,
                             AttachRelation.attach_methods_bwd,
                             root_components)


class RegistrationRelation(BinRelation):
    register_methods_fwd = {'android.view.View' : ['[CI] [ENTRY] [${CONTAINER}] void android.view.View.setOnClickListener(L : android.view.View$OnClickListener)']}
    register_methods_bwd = {}

    def __init__(self, trace_map, root_components):
        BinRelation.__init__(self, trace_map,
                             "CONTAINER",
                             "L",
                             RegistrationRelation.register_methods_fwd,
                             RegistrationRelation.register_methods_bwd,
                             root_components)

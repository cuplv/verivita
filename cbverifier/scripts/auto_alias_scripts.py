from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
import argparse

aliasList = {
    "android.app.Fragment.onCreate": [""]
}

def cycle_lines(in_file, out_file):
    with open(in_file, 'r') as f:
        for line in f:
            if line is not None and len(line) > 2 and line[0] != '/':

                line2 = line.strip()
                if line2[-1] == ";":
                    trimedLine = line2[:-1]
                else:
                    trimedLine = line2
                parsedspec = Spec.get_spec_from_string(trimedLine)
                assert(len(parsedspec) == 1)
                spec = parsedspec[0].ast

                spec2 = add_alias(spec, "foo", ["bar","baz"])
                print ""
                pretty_print(spec2)

def add_alias(spec, name, substitutions):
    node_regexp = get_regexp_node(spec)
    atom = get_spec_rhs(spec)
    aliases = get_spec_aliases(spec)


    newaliases = add_alias_to_chain(aliases,name,substitutions)
    if is_spec_enable(spec):
        return new_enable_spec(node_regexp,atom, newaliases)
    elif is_spec_disable(spec):
        return new_disable_spec(node_regexp,atom,newaliases)
    else:
        raise Exception()

def add_alias_to_chain(aliases, name, substitutions):
    node_type = get_node_type(aliases)
    if(node_type == NIL):
        id_substitutions = []
        for substitution in substitutions:
            id_substitutions.append(new_id(substitution))
        return new_alias((new_id(name),id_substitutions),new_nil())
    new = get_alias_new(aliases)
    old = get_alias_old(aliases)
    tail = get_alias_tail(aliases)
    return new_alias(old,new,add_alias_to_chain(tail))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print human readable data from protobuf trace')
    parser.add_argument('--input', type=str,
                        help="input file",required=True)
    parser.add_argument('--output', type=str,
                        help="input file",required=True)
    args = parser.parse_args()

    cycle_lines(args.input, args.output)
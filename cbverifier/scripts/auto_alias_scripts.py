from cbverifier.specs.spec import Spec
from cbverifier.specs.spec_ast import *
import argparse

#Note: DO NOT USE THIS SCRIPT FOR ANYTHING WHICH IS NEGATED!!!
#aliases of negation must be moved inside the clause and conjuncted
# eg: a;.*;!b |-c ALIAS b=b,t results in two rules a;.*;!t |-c and a;.*;!b|-c
# meaning that we effectively have a;.*;TRUE|-c
# instead a;.*;(!t & !b) |-c is needed

if(True):
    combinations = [

        ({"onStart","onResume", "onPause","onSaveInstanceState","onDestroy","onDetach",
          "onCreateView","onViewCreated","onDestroyView", "<init>","onStop","onCreate","onAttach", "onActivityCreated", "isDetached", "isResumed"},
            {"android.support.v4.app.Fragment", "android.support.v4.app.ListFragment","android.app.ListFragment",
               "android.support.v4.app.DialogFragment","android.preference.PreferenceFragment",
             "android.app.DialogFragment",
             "android.webkit.WebViewFragment",
             "android.support.v7.preference.PreferenceFragmentCompat"
             # "android.support.v14.preference.EditTextPreferenceDialogFragment",
             # "android.support.v14.preference.ListPreferenceDialogFragment",
             # "android.support.v14.preference.MultiSelectListPreferenceDialogFragment",
             # "android.support.v14.preference.PreferenceDialogFragment",
             # "android.support.v17.leanback.app.BrandedFragment",
             # "android.support.v17.leanback.app.GuidedStepFragment",
             # "android.support.v17.leanback.app.HeadersFragment",
             # "android.support.v17.preference.LeanbackPreferenceDialogFragment",
             # "android.support.v17.preference.LeanbackSettingsFragment",
             # "android.support.v17.leanback.app.OnboardingFragment",
             # "android.support.v17.leanback.app.PlaybackFragment",
             # "android.support.v17.leanback.app.RowsFragment",
             # "android.support.v17.leanback.app.SearchFragment",
             # "android.support.v17.preference.BaseLeanbackPreferenceFragment",
             # "android.support.v17.leanback.app.BrowseFragment",
             # "android.support.v17.leanback.app.DetailsFragment",
             # "android.support.v17.leanback.app.ErrorFragment",
             # "android.support.v17.preference.LeanbackListPreferenceDialogFragment",
             # "android.support.v17.preference.LeanbackPreferenceFragment",
             # "android.support.v17.leanback.app.PlaybackOverlayFragment",
             # "android.support.v17.leanback.app.VerticalGridFragment",
             # "android.support.v17.leanback.app.VideoFragment"
             })]
    base = "android.app.Fragment"

if(False):
    combinations = [
        ({"onCreate","onResume", "onPause","onStop","onStart","onDestroy","<init>","onRestart"},
         {
          "android.accounts.AccountAuthenticatorActivity",
          "android.support.v7.app.ActionBarActivity",
          "android.app.ActivityGroup",
          "android.app.AliasActivity",
          "android.support.v7.app.AppCompatActivity",
          "android.app.ExpandableListActivity",
          "android.support.v4.app.FragmentActivity",
          "android.app.LauncherActivity",
          "android.app.ListActivity",
          "android.preference.PreferenceActivity",
          "android.app.TabActivity"})
    ]
    base = "android.app.Activity"

aliasMap = {}



for combination in combinations:
    for method in combination[0]:
        subslist = []
        basemethod = base + "." + method
        for object in combination[1]:
            subslist.append(object + "." + method)
        aliasMap[basemethod] = subslist


print ""

def get_aliases_for_spec(spec):
    node_regexp = get_regexp_node(spec)
    mr1 = getMethodRefs(node_regexp)
    atom = get_spec_rhs(spec)
    mr1 = mr1.union(getMethodRefs(atom))

    aliases = []
    for mr in mr1:
        split = mr.split(" ")
        if(len(split) == 2):
            mrp = split[1]
        else:
            mrp = mr
        a = aliasMap
        if mrp in aliasMap:
            mr_ = aliasMap[mrp]
            mr_.append(mrp)
            aliases.append((mrp,mr_))

    return aliases

def getMethodRefs(node):
    if(node[0] == ID):
        assert(isinstance(node[1],basestring))
        return {node[1]}
    else:
        out = set()
        for i in xrange(2,len(node)):
            out = out.union(getMethodRefs(node[i]))
        return out



def cycle_lines(in_file, out_file):
    with open(in_file, 'r') as f:
        for line in f:
            if line is not None and len(line) > 2 and line[0] != '/':

                line2 = line.strip()
                if line2[-1] == ";":
                    trimedLine = line2[:-1]
                else:
                    trimedLine = line2
                parsedspec = Spec.get_specs_from_string(trimedLine)
                assert(len(parsedspec) == 1)
                spec = parsedspec[0].ast
                aliasList = get_aliases_for_spec(spec)
                assert(len(aliasList) > 0)
                for alias in aliasList:
                    spec = add_alias(spec, alias[0],alias[1])
                pretty_print(spec)
                print ";"
            else:
                print line

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
    return new_alias((old,new),add_alias_to_chain(tail,name,substitutions))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print human readable data from protobuf trace')
    parser.add_argument('--input', type=str,
                        help="input file",required=True)
    parser.add_argument('--output', type=str,
                        help="input file",required=False)
    args = parser.parse_args()

    cycle_lines(args.input, args.output)
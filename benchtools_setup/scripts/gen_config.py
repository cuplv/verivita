import argparse
import os

subexpressions = [
    "cbverifier/android_specs/subexpr/android.app.AlertDialog/dialog.spec",
    "cbverifier/android_specs/subexpr/android.app.Activity/activity_callbacks.spec",
    "cbverifier/android_specs/subexpr/android.app.Fragment/fragment_callbacks.spec"
]
enable_disable_rules = {
    "lifestate" : [
        "cbverifier/android_specs/enabledisable/android.view.View/view_REGEX.spec",
        "cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec",
        "cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment.spec",
        "cbverifier/android_specs/enabledisable/android.view.View/onClick_listener_setenabled.spec",
        "cbverifier/android_specs/enabledisable/android.os.AsyncTask/AsyncTask.spec",
        "cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifestate.spec",
        "cbverifier/android_specs/enabledisable/android.app.AlertDialog/DialogInterfaces_OnClickListener.spec"
    ],
    "lifecycle" : [
        "cbverifier/android_specs/enabledisable/android.app.Activity/activity_lifecycle.spec",
        "cbverifier/android_specs/enabledisable/android.app.Fragment/Fragment_lifecycle.spec"
    ],
    "just_disallow" : [

    ]
}
allow_disallow_rules = {
    "AlertDialog.dismiss": ("Dialog.dismiss.txt",[
        "cbverifier/android_specs/allowdisallow/android.app.AlertDialog/dismiss.spec"
    ]),
    "AlertDialog.show" : ("Dialog.show.txt",[
        "cbverifier/android_specs/allowdisallow/android.app.AlertDialog/show.spec"
    ]),
    "AsyncTask.execute": ("AsyncTask_all.execute.txt",[
        "cbverifier/android_specs/allowdisallow/android.os.AsyncTask/execute.spec"
    ]),
    "Fragment.getResources": ("Fragment_all.getResources.txt",[
        "cbverifier/android_specs/allowdisallow/fragment/fragment_getResources.spec",
        "cbverifier/android_specs/allowdisallow/android.support.v4.app.Fragment/fragment_getResources.spec"
    ]),
    "Fragment.getString": ("Fragment_all.getString.txt",[
        "cbverifier/android_specs/allowdisallow/fragment/fragment_getString.spec",
        "cbverifier/android_specs/allowdisallow/android.support.v4.app.Fragment/fragment_getString.spec"
    ]),
    "Fragment.setArguments" : ("Fragment.setArguments.txt",[
        "cbverifier/android_specs/allowdisallow/fragment/fragment_setArguments.spec"
    ]),
    "Fragment.startActivity" : ("Fragment_all.startActivity.txt",[
        "cbverifier/android_specs/allowdisallow/fragment/fragment_startActivity.spec",
        "cbverifier/android_specs/allowdisallow/android.support.v4.app.Fragment/fragment_startActivity.spec"
    ])

}

environment = "[environment]\n" \
    "db_uri = db\n" \
    "delay_notifications = true\n" \
    "create_db = true\n" \
    "scheduler=make\n" \
    "dump_scheduler_script = output_scheduler_local.txt\n" \
    "num_cores = 1\n"


params = "executable =./scripts/verify.sh\n" \
    "basedir=/\n" \
    "time_limit=600\n" \
    "mem_limit=4000000\n" \
    "email=\n"\
    "disabled=false"


instance_pref = "instances_file=./instances/"

tarball_pref = "tarball=./results/"

parameters_pref = "parameters=/home/s/Documents/source/callback-verification;"

group_pref = "[group_"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate run groups automatically for benchtools')
    parser.add_argument('--print_paths', type=str,
                    help="lifestate: ls, lifecycle: lc",required=False)
    parser.add_argument('--disallow', type = str,
                        help = "disallow to print", required=False)
    args = parser.parse_args()

    #scriptdir = os.path.dirname(__file__)
    scriptdir=os.path.dirname(os.path.abspath(__file__))

    basedir = "/".join(scriptdir.split("/")[:-2])

    if args.print_paths is None:
        print environment
        for ruleset in enable_disable_rules:
            for disallow in allow_disallow_rules:
                print ""
                print group_pref + ruleset + "_" + disallow + "]"
                print params
                specfiles = enable_disable_rules[ruleset] + allow_disallow_rules[disallow][1] + subexpressions
                specfiles_absolute = [basedir + "/" + f for f in specfiles]
                for specfile in specfiles_absolute:
                    if not os.path.isfile(specfile):
                        raise Exception("specfile: " + specfile + " does not exist")
                print parameters_pref + ":".join(specfiles_absolute)
                print tarball_pref + disallow + "_" + ruleset  + ".tar.bz2"
                print instance_pref + allow_disallow_rules[disallow][0]

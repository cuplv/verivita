#!/usr/bin/env bash

#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python $DIR/callin_callbacks.py --trace $1 --disallow /Users/s/Documents/source/callback-verification/cbverifier/android_specs/allowdisallow/android.app.AlertDialog/dismiss.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Activity/activity_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.AlertDialog/dialog.spec
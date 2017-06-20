#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

python $DIR/callin_callbacks.py --trace $1 --disallow /Users/s/Documents/source/callback-verification/cbverifier/android_specs/allowdisallow/fragment/fragment_getString.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/subexpr/android.app.Fragment/fragment_callbacks.spec:/Users/s/Documents/source/callback-verification/cbverifier/android_specs/allowdisallow/android.support.v4.app.Fragment/fragment_getString.spec
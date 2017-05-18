This is a directory of apps which are malformed in some way or another which we are excluding from our experiments.

- app.Watson exclusion: This is a user library which uses the android.support package, we could specify it as framework code, however there are not good ways to version it like the real framework code so it can cause problems for the experiments.
    - exclusion file: watson.txt

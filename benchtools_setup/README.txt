# Dependencies

- The script uses the benchtools tools (in benchtools.tar.bz2).
Benchtools have been developed by Alberto Griggio in fbk (https://es-static.fbk.eu/people/griggio/).
They *CANNOT* be redistributed or reused for other projects.

- NuXmv: https://es-static.fbk.eu/tools/nuxmv/

# Environment variables to set!

- Path to nuXmv
```export NUXMV_PATH="<path-to-nuxmv-executable>"```


# Simulation

- Configuration:
  - In the file 'config_simulation': change "basedir" to the path to the folder that contains traces
  - In the file 'config_simulation': change "parameters" to contains the path to the verifier and the paths to the specifications.
    Look at the example for the format.
  - In the file 'trace_to_simulate.txt': you must fill the list (one name per line) of names of the traces in the trace_to_simulate.txt file
    The name of the trace must be relative to the path basedir specified in the config_simulation (change it on your system)


- run the simulation
python ${BENCHTOOLS_PATH}/exec/run_group.py config_simulation

- run things in background
bash ~/Tools/benchtools/exec/schedule_at_group.sh config_simulation

- collect the results
python ${BENCHTOOLS_PATH}/analyze/extract_log.py -p -f filters/simulate.py -o simulate_res.txt ./results_simulation/simulation.tar.bz2 

- Results: the results are in the file simulate_res.txt
The file list each trace and, for each trace, it show if the simulation succeeded or if it was blocked and its runtime.


# Performance
- Configuration:
  - In the file 'config_verification': change "basedir" to the path to the folder that contains traces
  - In the file 'config_verification': change "parameters" to contains the path to the verifier and the paths to the specifications.
    Look at the example for the format.
  - In the file 'trace_to_verify.txt': you must fill the list (one name per line) of names of the traces in the trace_to_simulate.txt file
    The name of the trace must be relative to the path basedir specified in the config_simulation (change it on your system)


- run the verification
python ${BENCHTOOLS_PATH}/exec/run_group.py ./config_verification 

- collect the results
python ${BENCHTOOLS_PATH}/analyze/extract_log.py -p -f filters/ic3_filter.py -o verify_res.txt ./results/verification.tar.bz2 



# DEBUG THE OUTPUT
The detailed results are (compressed) in the `results_simulation` folder and in the results folder.

The archive contains, for each trace and each script configuration, three different files (*.stder,  
*.stdout, *.stats) that contains respectively the output of the standard error, of the standard output and some statistics (e.g. run time).



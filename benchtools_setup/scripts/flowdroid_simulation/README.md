# Experiments using the "FlowDroid-like" framework model

The folder contains the script used to run the validation and verification using the FlowDroid model and to collect and plot the results.

# Validation

## Run validation

```
cd <verivita-repo>/benchtools_setup/results_tables/popl/flowdroid/simulation
python <benchtools_path>/exec/run_group.py config_simulation_s
```

`<benchtools_path>` is the path to the benchtools tool

`<verivita-repo>` path to the Verivita repository


## Collect results and generates plots

- Collect the log of the results:

```
cd <verivita-repo>/benchtools_setup/results_tables/popl/flowdroid/simulation
tar xjf simulation_flowdroid.tar.bz2
python <benchtools_path>/analyze/extract_log.py -p -f <verivita-repo>/benchtools_setup/filters/simulate_flowdroid.py -o simulation_flowdroid.log simulation_flowdroid
```

- Create the plots.

The script generates the plot in the same folder and prints the name of the generated plots.
```
cd <verivita-repo>/benchtools_setup/results_tables/popl/flowdroid/simulation/
python <verivita-repo>/benchtools_setup/scripts/flowdroid_simulation/gen_flowdroid_validation_plot.py -f simulation_flowdroid.log
```




# Run verification




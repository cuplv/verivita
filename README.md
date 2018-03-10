# Verivita (may be referred to as "callback-verification" in certain files)
Verivita is a verification technique for checking the event driven programming protocol of an Android application.  The event driven programming protocol  defines the possible interactions between an android application and the android framework via callbacks and library method invocations called callins. This is done by recording a trace of the application and then automatically searching for nearby executions that could fail.

# High Level Process For Use

- Create trace of Android application (See TraceRunner submodule)
- Check trace with verivita using a relevant set of lifestate rules
- Output is either a rearranged trace showing a possible failure or a proof that it cannot be rearranged


# External Dependencies
- PySMT
  - Install PySMT (e.g. pip install pysmt)
  - Install z3 and the CUDD support (pysmt-install --z3 --bdd, then pysmt-install --env, and use the output to extend the PYTHONPATH)
- TraceRunner
- Google protobuf 3.0

*WARNING* we require protobuf version 3.0


# Installation

1. You need to install PySMT with z3 (follow the instruction at https://github.com/pysmt/pysmt)

2. Compile the protobuffer interface (from the root directory of the project). You need the TraceRunner repository for this.
```
protoc -I=<TraceRunner-repo>/TraceRunnerRuntimeInstrumentation/tracerunnerinstrumentation/src/main/proto/edu/colorado/plv/tracerunner_runtime_instrumentation --python_out=./cbverifier/traces <TraceRunner-repo>/TraceRunnerRuntimeInstrumentation/tracerunnerinstrumentation/src/main/proto/edu/colorado/plv/tracerunner_runtime_instrumentation/tracemsg.proto
```

3. add the cbverifier path to the PYTHONPATH environment variable



# Usage

## Verify a trace (with BMC)
```python cbverifier/driver.py -t <trace-file> -s <spec-files> -k <bmc-bound>```

Example:
```
python cbverifier/driver.py -f json -t cbverifier/test/examples/trace1.json -s cbverifier/test/examples/spec1.spec -k 2
```

`<spec-files>` is a colon separated list of paths to specification files.

Note: the `-f json` flag can be used if the trace is in json format. For binary format traces (the default generated by trace runner) no flags are needed.

Note: the verifier tool has different parameters, like the `-k` bound. Use `-h` to get an help screen that explain them.


## Verify a trace (with IC3)
```python cbverifier/driver.py -t <trace-file> -s <spec-files> -m ic3 --ic3_frames 10 -n <PATH-TO-NUXMV>```

The verifier uses the tool nuXmv to verify if the trace can reach a violation (note that this cannot be proved by BMC)

In this case the user must specify the path to the nuXmv tool (`-n` followed by the absolute path to nuXmv). The (binary, static version of the) tool can be downloaded here: https://es-static.fbk.eu/tools/nuxmv/

The other parameter that must be specified is `--ic3_frames` that determines the number of frames explored by the IC3 algorithm.

The result of the verification process for now is "The trace is SAFE", "The system can reach an error state" or "The result is still unknown (e.g try to increment the number of frames).".


## Check the input files (traces and specs) and print them as output
```python cbverifier/driver.py -m check-files -t <trace-file> -s <spec-files>```


## Print the list of grounded specifications
```python cbverifier/driver.py -m show-ground-specs -t <trace-file> -s <spec-files>```

## Simulate a trace

The following command simulate the trace and applies the constraints
described by the set of specifications. This step can be used to
validate a set of specifications againts a concrete trace of execution.
```
python driver.py  -t <trace-file> -s <spec-files> -m simulate
```

The command allows to simulate a trace specified by an arbitrary order
of top-level callbacks with the paramter `-w`.

For example, consider the trace:

```
TRACE:
[0] [CB] void com.ianhanniballake.contractiontimer.ContractionTimerApplication.<init>() (612b562) 
  [1] [CI] void android.app.Application.<init>() (612b562) 
[4] [CB] void com.ianhanniballake.contractiontimer.ContractionTimerApplication.attachBaseContext(android.content.Context) (612b562,6a2a16b) 
  [5] [CI] void android.content.ContextWrapper.attachBaseContext(android.content.Context) (612b562,6a2a16b) 
[8] [CB] java.lang.String com.ianhanniballake.contractiontimer.ContractionTimerApplication.getPackageName() (612b562) 
  [9] [CI] java.lang.String android.content.ContextWrapper.getPackageName() (612b562) 
[12] [CB] java.lang.ClassLoader com.ianhanniballake.contractiontimer.ContractionTimerApplication.getClassLoader() (612b562) 
  [13] [CI] java.lang.ClassLoader android.content.ContextWrapper.getClassLoader() (612b562) 
[16] [CB] com.ianhanniballake.contractiontimer.provider.ContractionProvider.<clinit> (NULL) 
  [17] [CI] void android.content.UriMatcher.<init>(int) (f426055,-1) 
  [19] [CI] void android.content.UriMatcher.addURI(java.lang.String,java.lang.String,int) (f426055,com.ianhanniballake.contractiontimer,contractions,1) 
  [21] [CI] void android.content.UriMatcher.addURI(java.lang.String,java.lang.String,int) (f426055,com.ianhanniballake.contractiontimer,contractions/#,2) 
[24] [CB] void com.ianhanniballake.contractiontimer.provider.ContractionProvider.<init>() (ca6f21a) 
```

With the command:
```
python driver.py  -t <trace-file> -s <spec-files> -m simulate -w 8:0
```
we test if the trace
```
[8] [CB] java.lang.String com.ianhanniballake.contractiontimer.ContractionTimerApplication.getPackageName() (612b562) 
  [9] [CI] java.lang.String
  android.content.ContextWrapper.getPackageName() (612b562) 
[0] [CB] void com.ianhanniballake.contractiontimer.ContractionTimerApplication.<init>() (612b562) 
  [1] [CI] void android.app.Application.<init>() (612b562) 
```
can be simulated according to the set of specifications.


## Run unit tests:
```nosetests```


## Specification language
The specification language is described in the file SPEC_LANGUAGE.md

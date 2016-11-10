# callback-verification
Dynamic verification using callbacks.


# External Dependencies
- PySMT
- TraceRunner
- Google protobuf 3.0

*WARNING* we require version 3.0


Compile the python package for protobuffer
```
protoc -I=../TraceRunner/TraceRunnerRuntimeInstrumentation/tracerunnerinstrumentation/src/main/proto/edu/colorado/plv/tracerunner_runtime_instrumentation --python_out=./cbverifier/traces ../TraceRunner/TraceRunnerRuntimeInstrumentation/tracerunnerinstrumentation/src/main/proto/edu/colorado/plv/tracerunner_runtime_instrumentation/tracemsg.proto

```


# Usage

Dynamic verification:
```python driver.py -t <trace-file> -s <spec-file> -k <bmc-bound>```

Check if the input files are well formed:
```python driver.py -m check-files -t <trace-file> -s <spec-file>```

To have bash generate the list of spec files automatically from a directory:
```for f in `find $(pwd) -name "*.spec"`; do echo -e "$f:\c"; done```

Run unit tests:
```cd cbverifier; nosetests```

To Run
======
compile protocol buffers

```
protoc -I=<path to trace-serializer dir>/src/main/protobuf/ --python_out=. <path to trace-serializer dir>/src/main/protobuf/QueryTrace.proto
```

Notes
=====

Verification assumes that all holes that are relevant to verification are filled.
Any unfilled holes for callbacks or callins will be dropped from the trace.
Any unfilled parameters will be replaced with an unused object.
TODO: figure out something better as this may negatively affect verification
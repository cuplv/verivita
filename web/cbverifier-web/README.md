To Run
======
compile protocol buffers

```
protoc -I=<path to trace-serializer dir>/src/main/protobuf/ --python_out=. <path to trace-serializer dir>/src/main/protobuf/QueryTrace.proto
```

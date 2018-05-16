Verivita Web Interface
======================

A web site for verifying android applications with the Verivita system.


Setup
-----
Install elm (Note this is only required for development not deployment)
```
brew install elm
```

or

```
npm install elm
```

Install JEP

JEP is a python interface for java and is used to invoke Verivita.

```
pip install jep
```

Include jep.so in the library path for java

* In MacOS this is the environment variable DYLD_LIBRARY_PATH, location is likely ```/usr/local/lib/python2.7/site-packages/jep/jep.so```

* In Linux this is the environment variable LD_LIBRARY_PATH



Running
-------

```
sbt run
```

Mock Objects for Web Development
--------------------------------

set environment variable.
```
export VERIVITA_MOCK=true
```

This switches the implementation of TraceManager to an instance of
"FakeManager" so verivita isn't required for development tasks.


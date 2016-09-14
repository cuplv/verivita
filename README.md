# callback-verification
Dynamic verification using callbacks.


# External Dependencies
- PySMT

# Usage

Dynamic verification:
```python driver.py -t <trace-file> -s <spec-file> -k <bmc-bound>```

Check if the input files are well formed:
```python driver.py -m check-files -t <trace-file> -s <spec-file>```

To have bash generate the list of spec files automatically from a directory:
```for f in `find $(pwd) -name "*.spec"`; do echo -e "$f:\c"; done```

Run unit tests:
```cd cbverifier; nosetests```

# Branches:
- tests: used to develop integration tests for verification.

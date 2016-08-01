# callback-verification
Dynamic verification using callbacks.


# External Dependencies
- PySMT

# Usage

Dynamic verification:
```python driver.py -t <trace-file> -s <spec-file> -k <bmc-bound>```

Check if the input files are well formed:
```python driver.py -m check-files -t <trace-file> -s <spec-file>```

Run unit tests:
```cd cbverifier; nosetests```

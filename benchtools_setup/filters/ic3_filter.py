import re

def do_filter(iterable):
    result = "?"
    time = '?'
    started = False
    extra = []
    steps = '?'

    to = False

    p = None
    for line in iterable:
        line = line.strip()
        if not line: continue

        if line.startswith('real ') and not to:
            try: time = float(line.split()[1])
            except: pass

        if line.startswith('The trace is SAFE'):
            result = 'Safe'

        if line.startswith('The system can reach an error state'):
            result = 'Unsafe'


        # no bug found - unknown result
        if line.startswith("KeyboardInterrupt"):
            to = True
            time = "Timeout"
            result = "Timeout"
        if line.startswith("Exception: An error happened reading the trace"):
            result = "ReadError"
        if line.startswith("MemoryError"):
            result = "MemoryError"


    return 'result %s time %s steps %s %s' % (result, time, steps, " ".join(extra))





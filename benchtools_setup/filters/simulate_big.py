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

        elif line.startswith('real ') and not to:
            try: 
                time = float(line.split()[1])
                if time != "?" and time > 3600: #line.startswith("KeyboardInterrupt"):
                    to = True
                    time = "Timeout"
                    result = "?"

            except: pass

        elif line.startswith('The trace can be simulated in'):
            result = 'Ok'
            app = re.match("The trace can be simulated (\d+) steps", line)

            if (app):
                steps = app.groups(1)
            else:
                app = re.match("The trace can be simulated in (\d+) steps", line)
                if(app):
                    steps = app.groups(1)

        elif line.startswith('The trace cannot be simulated'):
            result = 'Block'

            app = re.match("The trace cannot be simulated \(it gets stuck at the (\d+) transition\)", line)

            if (app):
                steps = app.group(1)
        elif line.startswith("Exception: An error happened reading the trace"):
            result = "ReadError"
        elif line.startswith("MemoryError"):
            result = "MemoryError"
        elif line.startswith("z3types.Z3Exception: out of memory"):
            result = "MemoryError"
        elif line.startswith("cbverifier.traces.ctrace.MalformedTraceException"):
            result = "ReadError"
        elif line.startswith("Exception MemoryError: MemoryError()"):
            result = "MemoryError"
        elif line.startswith("KeyError: ('"):
            result = "KeyError"



        # no bug found - unknown result
    return 'result %s time %s steps %s %s' % (result, time, steps, " ".join(extra))

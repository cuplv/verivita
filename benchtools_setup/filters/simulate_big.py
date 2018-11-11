import re

def do_filter(iterable):
    result = "?"
    time = '?'
    started = False
    extra = []
    steps = '?'
    total_steps = '?'

    to = False

    simulate_steps_re = re.compile("INFO:root:Simulating step (\d+)/(\d+)")

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

        elif line.startswith('The trace cannot be simulated'):
            result = 'Block'

        elif line.startswith('INFO:root:Simulating'):
            match_step_line = simulate_steps_re.match(line)
            if match_step_line:
                steps = match_step_line.group(1)

                if (type(steps) == type((),)):
                    steps = steps[0]

                total_steps = match_step_line.group(2)
                if (type(total_steps) == type((),)):
                    total_steps = total_steps[0]
        elif line.startswith("The trace can be simulated in 0 steps"):
            steps = 0
            total_steps = 0

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


    return 'result %s time %s steps %s totalsteps %s %s' % (result, time, steps, total_steps, " ".join(extra))

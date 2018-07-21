import re

def do_filter(iterable):
    result = "?"
    time = '?'
    started = False
    extra = []
    steps = '?'
    total_steps = '?'

    failure_reason = '?'

    to = False

    can_simulate_re = re.compile("The trace can be simulated (\d+) steps")
    can_simulate_re_2 = re.compile("The trace can be simulated in (\d+) steps")
    cannot_simulate_re = re.compile("The trace cannot be simulated \(it gets stuck at the (\d+)-th transition\)")
    simulate_steps_re = re.compile("INFO:root:Simulating step (\d+)/(\d+)")
    failure_re = re.compile("Failure: (\w+)")

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
            # app = can_simulate_re.match(line)
            # if (app):
            #     steps = app.groups(1)
            # else:
            #     app = can_simulate_re_2.match(line)
            #     if(app):
            #         steps = app.groups(1)

        elif line.startswith('The trace cannot be simulated'):
            result = 'Block'
            # app = cannot_simulate_re.match(line)
            # if (app):
            #     steps = app.group(1)

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

        elif line.startswith("Failure:"):
            match_failure_re = failure_re.match(line)
            if match_failure_re:
                failure_reason = match_failure_re.group(1)
                if (type(failure_reason) == type((),)):
                    failure_reason = failure_reason[0]

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


    return 'result %s time %s steps %s totalsteps %s failure_reason %s %s' % (result, time, steps, total_steps, failure_reason, " ".join(extra))

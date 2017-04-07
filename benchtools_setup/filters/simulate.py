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

        if line.startswith('The trace can be simulated in'):
            result = 'Ok'
            app = re.match("The trace can be simulated (\d+) steps", line)

            if (app):
                steps = app.groups(1)
            else:
                app = re.match("The trace can be simulated in (\d+) steps", line)
		if(app):
                    steps = app.groups(1)

        if line.startswith('The trace cannot be simulated (it gets stuck after'):
            result = 'Block'

            app = re.match("The trace cannot be simulated \(it gets stuck after (\d+) transition\)", line)

            if (app):
                steps = app.group(1)


        # no bug found - unknown result
        if line.startswith("KeyboardInterrupt"):
            to = True
            time = "Timeout"
            result = "?"

    return 'result %s time %s steps %s %s' % (result, time, steps, " ".join(extra))

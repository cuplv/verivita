import optparse


def slice_single_object(trace, object):
    pass

def main(input_args = None):
    p = optparse.OptionParser()
    p.add_option('-t', '--trace', help="trace file")
    p.add_option('-m', '--mode', type='choice',
                 choices=['print', 'single'],
                 help=("print: print entire trace\n"+
                       "single: slice against single object"))
    p.add_option('-o', '--object')

    opts, args = p.parse_args(input_args)

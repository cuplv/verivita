#~/.pyenv/versions/2.7.14/bin/ipython
#import ipy_utils as t
from IPython.core.debugger import Pdb
small_exp_traces = "/Users/s/Documents/data/pldi_2017_submission_data/apps_man_corp/"

#debug method
def dm(*args):
    pdb = Pdb()
    pdb.runcall(*args)
    
    

#~/.pyenv/versions/2.7.14/bin/ipython
#import ipy_utils as t
from IPython.core.debugger import Pdb

#debug method
def dm(*args):
    pdb = Pdb()
    pdb.runcall(*args)
    
    

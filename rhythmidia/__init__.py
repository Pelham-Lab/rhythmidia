"""Race tube image analysis and period elucidation in Python."""

# Add imports here
#import importlib
disp = True
try:
    import pyautogui
except KeyError:
    disp = False
if disp:
    #importlib.import_module(.rhythmidia)
    #importlib.import_module(rhythmidia_gui)
    from .rhythmidia import *
    from .rhythmidia_gui import *


#from ._version import __version__

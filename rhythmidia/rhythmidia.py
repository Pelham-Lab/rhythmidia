import sys
disp = True
try:
    import pyautogui
except KeyError:
    disp = False
from rhythmidia.rhythmidia_gui import openAndRun
from argparse import ArgumentParser

def run():
    openAndRun()


if __name__ == "__main__":
    if disp:
        run()
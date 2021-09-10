
from colored import stylize
import colored as c

def positive(string):
    return stylize(string, c.fg("green"))
    
def negative(string):
    return stylize(string, c.fg("red"))
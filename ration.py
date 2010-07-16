#!/usr/bin/env python

import re
import subprocess

def get_screen_resolution():
    p = subprocess.Popen(['xwininfo', '-root'], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    
    match = re.search(r'Width: ([0-9]+)\s+Height: ([0-9]+)', output)
    
    width = int(match.group(1))
    height = int(match.group(2))
    
    return width, height
    
def 
    
print get_screen_resolution()

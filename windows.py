#!/usr/bin/env python

import re
import subprocess

def get_screen_resolution():
    """
    Fetch the current screen resolution using xwininfo.
    
    TODO: Handle multiple monitors / desktops.
    """
    p = subprocess.Popen(['xwininfo', '-root'], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    
    match = re.search(r'Width: ([0-9]+)\s+Height: ([0-9]+)', output)
    
    width = int(match.group(1))
    height = int(match.group(2))
    
    return width, height

def select_window():
    """
    Use xwininfo to allow the user to select a window and then fetches its window id.
    """
    p = subprocess.Popen(['xwininfo'], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    
    # e.g. "Window id: 0x4400088"
    match = re.search(r'Window id: (0x[0-9a-f]+)', output)
    
    return match.group(1)

def resize_window(window_id, x, y, width, height):
    """
    Use wmctrl to resize a window.
    """
    size = '0,%i,%i,%i,%i' % (x, y, width, height)
    print ' '.join(['wmctrl', '-i', '-r', window_id, '-e', size])
    p = subprocess.Popen(['wmctrl', '-i', '-r', window_id, '-e', size], stdout=subprocess.PIPE)
    output = p.communicate()[0]

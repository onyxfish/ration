#!/usr/bin/env python

import sys

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

import ration

GUI_GLADE_FILE = 'gui/ration.glade'

class RationApp:
    """
    TODO
    """

    def __init__(self):
        self.window = gtk.Window()
        self.canvas = gtk.DrawingArea()
        self.window.add(self.canvas)
        
        self.window.connect('destroy', gtk.main_quit)
        self.window.connect('destroy-event', gtk.main_quit)
        self.canvas.connect('configure-event', self.canvas_configure)
        self.canvas.connect('expose-event', self.canvas_expose)
        
        width, height = ration.get_screen_resolution()
        width, height = width * 0.2, height * 0.2
        
        self.window.set_size_request(width, height)
        self.window.show_all()
    
    def canvas_configure(self, widget, event):
        print 'configure'
        x, y, width, height = widget.get_allocation()
        
        self.buffer_pixmap = gtk.gdk.Pixmap(widget.window, width, height)
        self.buffer_pixmap.draw_rectangle(widget.get_style().white_gc, True, 0, 0, width, height)
        
        return True
    
    def canvas_expose(self, widget, event):
        print 'expose'
        x , y, width, height = event.area
        
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL], self.buffer_pixmap, x, y, x, y, width, height)
        widget.window.draw_line(widget.get_style().fg_gc[gtk.STATE_NORMAL], 0, 0, 100, 50)

        return False

if __name__ == '__main__':
    app = RationApp()
    gtk.main()


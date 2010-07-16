#!/usr/bin/env python

import sys

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade

GUI_GLADE_FILE = 'gui/ration.glade'

class RationApp:
	"""
	TODO
	"""

	def __init__(self):
	    self.builder = gtk.Builder()
	    self.builder.add_from_file(GUI_GLADE_FILE)
	    
	    self.window = self.builder.get_object('ration_window')
	    self.window.connect('destroy', gtk.main_quit)
	    self.window.set_default_size(100, 75)
	    self.window.show()
	    
	    signal_handlers = { 
	        'on_ration_window_destroy_event' : gtk.main_quit,
	    }
	    
	    self.builder.connect_signals(signal_handlers)


if __name__ == '__main__':
	app = RationApp()
	print 'running'
	gtk.main()



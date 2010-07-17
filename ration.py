#!/usr/bin/env python

import atexit
import math
import sys

import pygtk
pygtk.require('2.0')
import gtk
import gtk.glade
import keybinder

import windows

HOTKEY = '<Alt>R'
CANVAS_SCALE = 0.2
BOXES_PER_SIDE = 8

class RationApp:
    """
    An application to quickly resize windows to fill discrete portions of the
    screen in GTK-based Linux distributions.
    """
    mouse_down = None
    canvas_width = 0
    canvas_height = 0

    def __init__(self):
        """
        Setup the window and canvas.
        """
        self.window = gtk.Window()
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        
        self.canvas = gtk.DrawingArea()
        self.canvas.set_events(
            gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.POINTER_MOTION_HINT_MASK | 
            gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
        self.window.add(self.canvas)
        
        self.window.connect('destroy', gtk.main_quit)
        self.window.connect('destroy-event', gtk.main_quit)
        self.canvas.connect('configure-event', self.canvas_configure)
        self.canvas.connect('expose-event', self.canvas_expose)
        self.canvas.connect('motion-notify-event', self.canvas_motion)
        self.canvas.connect('button-press-event', self.canvas_button_press)
        self.canvas.connect('button-release-event', self.canvas_button_release)
        
        width, height = windows.get_screen_resolution()
        width, height = width * CANVAS_SCALE, height * CANVAS_SCALE
        
        self.setup_status_icon()
        
        self.window.set_size_request(int(width), int(height))
        self.window.show_all()
        
        self.bind_hotkey()
        
    def setup_status_icon(self):
        """
        Setup the status icon that functions as a main menu.
        """
        self.menu = gtk.Menu()
        quit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quit_item.connect('activate', self.menu_quit)
        self.menu.append(quit_item)
        self.menu.show_all()

        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_stock(gtk.STOCK_FIND)
        self.status_icon.set_tooltip('Ration')
        self.status_icon.set_visible(True)

        self.status_icon.connect('activate', self.status_activate)
        self.status_icon.connect('popup-menu', self.status_popup_menu)
    
    def status_activate(self, status_icon):
        """
        Toggle the visiblity of the app window.
        """
        self.hotkey()
        
    def status_popup_menu(self, status_icon, button, time):
        """
        Show the application menu.
        """
        self.menu.popup(None, None, None, button, time)
    
    def menu_quit(self, menu_item):
        """
        Exit the application from menu.
        """
        gtk.main_quit()
    
    def canvas_configure(self, widget, event):
        """
        Configure the rendering back-buffer.
        """
        x, y, self.canvas_width, self.canvas_height = widget.get_allocation()
        
        self.buffer_pixmap = gtk.gdk.Pixmap(widget.window, self.canvas_width, self.canvas_height)
        self.clear_buffer()
        
        return True
    
    def canvas_expose(self, widget, event):
        """
        Render the back-buffer to the canvas.
        """
        x, y, width, height = event.area
        
        widget.window.draw_drawable(
            self.window.get_style().fg_gc[gtk.STATE_NORMAL], 
            self.buffer_pixmap, 
            x, y, x, y, width, height)

        return False
    
    def canvas_motion(self, widget, event):
        """
        Redraw the canvas with the latest selection.
        """
        if self.mouse_down:
            self.draw_selection(event)
        
        return True
    
    def canvas_button_press(self, widget, event):
        """
        Record mouse coordinates for drawing the selection box.
        """
        self.mouse_down = (event.x, event.y)
        
        return True
    
    def canvas_button_release(self, widget, event):
        """
        Redraw the canvas with the latest selection.
        """
        self.clear_buffer()
        self.blit_buffer()
        
        self.mouse_down = None
        
        return True
    
    def clear_buffer(self):
        """
        Clear the back-buffer.
        """
        self.buffer_pixmap.draw_rectangle(self.window.get_style().white_gc, True, 0, 0, self.canvas_width, self.canvas_height)
        
        for i in range(0, BOXES_PER_SIDE):
            x = (self.canvas_width / BOXES_PER_SIDE) * i
            self.buffer_pixmap.draw_line(self.window.get_style().black_gc, x, 0, x, self.canvas_height)
        
        for j in range(0, BOXES_PER_SIDE):
            y = (self.canvas_height / BOXES_PER_SIDE) * j
            self.buffer_pixmap.draw_line(self.window.get_style().black_gc, 0, y, self.canvas_width, y)
    
    def draw_selection(self, event):
        """
        Draw the current selection box onto the back-buffer.
        """
        x = self.mouse_down[0]
        y = self.mouse_down[1]
        width = event.x - x
        height = event.y - y
        
        if width < 0:
            width = -width
            x -= width
            
        if height < 0:
            height = -height
            y -= height
        
        self.clear_buffer()
        
        first_x_box = int(math.floor(x / (self.canvas_width / BOXES_PER_SIDE)))
        last_x_box = int(math.floor((x + width) / (self.canvas_width / BOXES_PER_SIDE)))
        first_y_box = int(math.floor(y / (self.canvas_height / BOXES_PER_SIDE)))
        last_y_box = int(math.floor((y + height) / (self.canvas_height / BOXES_PER_SIDE)))
        
        for i in range(first_x_box, last_x_box + 1):
            for j in range(first_y_box, last_y_box + 1):
                x1 = (self.canvas_width / BOXES_PER_SIDE) * i
                x2 = (self.canvas_width / BOXES_PER_SIDE) * (i + 1)
                y1 = (self.canvas_height / BOXES_PER_SIDE) * j
                y2 = (self.canvas_height / BOXES_PER_SIDE) * (j + 1)

                self.buffer_pixmap.draw_rectangle(self.window.get_style().black_gc, True, int(x1), int(y1), int(x2 - x1), int(y2 - y1))
        
        self.buffer_pixmap.draw_rectangle(
            self.window.get_style().fg_gc[gtk.STATE_NORMAL], 
            False, 
            int(x), int(y), int(width), int(height))
        self.blit_buffer()
        
    def blit_buffer(self):
        """
        Copy the back-buffer to the visible canvas.
        """
        self.canvas.window.draw_drawable(
            self.window.get_style().fg_gc[gtk.STATE_NORMAL], 
            self.buffer_pixmap, 
            0, 0, 0, 0, self.canvas_width, self.canvas_height)
        
    def hotkey(self):
        if self.window.get_visible():
            self.window.hide()
        else:
            self.window.show()
        
    def bind_hotkey(self):
        keybinder.bind(HOTKEY, self.hotkey)
    
    def unbind_hotkey(self):
        keybinder.unbind(HOTKEY)
        
if __name__ == '__main__':
    app = RationApp()
    atexit.register(app.unbind_hotkey)
    gtk.main()


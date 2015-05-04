#!/usr/bin/env python

import ConfigParser
import os

import atexit
import math
import sys

import pygtk
pygtk.require('2.0')
import gtk
import keybinder

import windows

screen_resolution = windows.get_screen_resolution()
CONFIG = {
        'hotkey': '<Ctrl><Alt>D',
        'exit_hotkey': 'Escape',
        'hide_after_arrangement': True,
        'canvas_scale': 0.2,
        'columns': 8,
        'rows': 8,
        'usable_screen_width': screen_resolution[0],
        'usable_screen_height': screen_resolution[1],
        'left_screen_margin': 0,
        'top_screen_margin': 0,
        'right_padding': 0,
        'bottom_padding': 0
}

CONFIG_FILE = os.path.expanduser('~/.ration')

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
        Read Config
        """
        if os.path.isfile(CONFIG_FILE):
            cfg = ConfigParser.ConfigParser()

            with open(CONFIG_FILE) as f:
                cfg.readfp(f)

            for option in CONFIG:
                try:
                    CONFIG[option] = cfg.getint('Config', option)
                except:
                    try:
                        CONFIG[option] = cfg.getfloat('Config', option)
                    except:
                        try:
                            CONFIG[option] = cfg.get('Config', option)
                        except:
                            pass

        """
        Setup the window and canvas.
        """
        self.window = gtk.Window()
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)

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

        width = math.floor(CONFIG['usable_screen_width'] * CONFIG['canvas_scale'] / CONFIG['columns']) * CONFIG['columns'] + 1
        height = math.floor(CONFIG['usable_screen_height'] * CONFIG['canvas_scale'] / CONFIG['rows']) * CONFIG['rows'] + 1

        self.setup_status_icon()

        self.window.set_size_request(int(width), int(height))
        self.window.show_all()

        self.bind_hotkeys()

    def go(self):
        """
        Launch the program main loop.
        """
        atexit.register(self.unbind_hotkeys)
        gtk.main()

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
        self.status_icon.set_from_stock(gtk.STOCK_ZOOM_FIT)
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
            self.update(event)

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
        self.update(event, selection=False)

        self.mouse_down = None

        window_id, window_name = windows.select_window()

        resize_occurred = False
        if window_id != hex(self.window.window.xid)[:-1] and \
            'Edge Panel' not in window_name and \
            'x-nautilus-desktop' != window_name:
            # If all boxes selected then maximize instead of resizing
            if self.selected_boxes == [0, 0, CONFIG['columns'], CONFIG['rows']]:
                windows.maximize_window(window_id)
            else:
                windows.resize_window(window_id, *self.new_window_size)
            resize_occurred = True

        self.clear_buffer()
        self.draw_grid()
        self.blit_buffer()

        if resize_occurred and CONFIG['hide_after_arrangement']:
            self.hide()

        return True

    def update(self, event, selection=True):
        """
        Updates selection coordinates and redraws the GUI.
        """
        self.compute_selection_rectangle(event)
        self.compute_selected_boxes()
        self.compute_new_window_size()
        self.clear_buffer()
        self.draw_selected_boxes()
        self.draw_grid()
#        if selection: self.draw_selection()
        self.blit_buffer()

    def compute_selection_rectangle(self, event):
        """
        Compute the shape of the selection, taking into account negative selection coordinates.

        (i.e. lower-right to upper-left)
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

        self.selection = (int(x), int(y), int(x + width), int(y + height))

    def compute_selected_boxes(self):
        """
        Use mouse coordinates to determine which boxes have been selected.
        """
        self.selected_boxes = (min(int(math.floor(self.selection[0] / (self.canvas_width / CONFIG['columns']))), CONFIG['columns']),
                               min(int(math.floor(self.selection[1] / (self.canvas_height / CONFIG['rows']))), CONFIG['rows']),
                               min(int(math.floor(self.selection[2] / (self.canvas_width / CONFIG['columns'])) + 1), CONFIG['columns']),
                               min(int(math.floor(self.selection[3] / (self.canvas_height / CONFIG['rows'])) + 1), CONFIG['rows']))

        self.selected_boxes = [max(0, x) for x in self.selected_boxes]

    def compute_new_window_size(self):
        """
        Translate the selection size to the actual screen size a window should be resized too.
        """
        self.new_window_size = (self.selected_boxes[0] * CONFIG['usable_screen_width'] / CONFIG['columns']
                                    + CONFIG['left_screen_margin'],
                                self.selected_boxes[1] * CONFIG['usable_screen_height'] / CONFIG['rows']
                                    + CONFIG['top_screen_margin'],
                                (self.selected_boxes[2] - self.selected_boxes[0]) * CONFIG['usable_screen_width'] / CONFIG['columns']
                                    - CONFIG['right_padding'],
                                (self.selected_boxes[3] - self.selected_boxes[1]) * CONFIG['usable_screen_height'] / CONFIG['rows']
                                    - CONFIG['bottom_padding'])

    def clear_buffer(self):
        """
        Clear the back-buffer.
        """
        self.buffer_pixmap.draw_rectangle(self.window.get_style().white_gc, True, 0, 0, self.canvas_width, self.canvas_height)
        self.draw_grid()

    def draw_grid(self):
        """
        Draw the selection grid onto the back-buffer.
        """
        for i in range(0, CONFIG['columns'] + 1):
            x = (self.canvas_width / CONFIG['columns']) * i
            self.buffer_pixmap.draw_line(self.window.get_style().black_gc, x, 0, x, self.canvas_height)

        for j in range(0, CONFIG['rows'] + 1):
            y = (self.canvas_height / CONFIG['rows']) * j
            self.buffer_pixmap.draw_line(self.window.get_style().black_gc, 0, y, self.canvas_width, y)

    def draw_selection(self):
        """
        Draw the current selection box onto the back-buffer.
        """
        style = self.window.get_style()

        self.buffer_pixmap.draw_rectangle(
            style.fg_gc[gtk.STATE_NORMAL],
            False,
            self.selection[0],
            self.selection[1],
            self.selection[2] - self.selection[0],
            self.selection[3] - self.selection[1])

    def draw_selected_boxes(self):
        """
        Draw the selected boxes in a different color.
        """
        x1 = self.selected_boxes[0] * self.canvas_width / CONFIG['columns']
        y1 = self.selected_boxes[1] * self.canvas_height / CONFIG['rows']
        x2 = self.selected_boxes[2] * self.canvas_width / CONFIG['columns']
        y2 = self.selected_boxes[3] * self.canvas_height / CONFIG['rows']

        color = self.window.get_colormap().alloc_color("#999999", False, True)

        gc = self.window.window.new_gc()
        gc.foreground = color

        self.buffer_pixmap.draw_rectangle(gc, True, int(x1), int(y1), int(x2 - x1), int(y2 - y1))

    def blit_buffer(self):
        """
        Copy the back-buffer to the visible canvas.
        """
        self.canvas.window.draw_drawable(
            self.window.get_style().fg_gc[gtk.STATE_NORMAL],
            self.buffer_pixmap,
            0, 0, 0, 0, self.canvas_width, self.canvas_height)

    def hide(self):
        self.window.hide()
        keybinder.unbind('Escape')

    def show(self):
        self.window.show()
        keybinder.bind('Escape', self.hide)

    def hotkey(self):
        """
        Toggle the visibility of the window.
        """
        if self.window.get_visible():
            self.hide()
        else:
            self.show()

    def bind_hotkeys(self):
        """
        Bind the toggle and hide hotkeys.
        """
        keybinder.bind(CONFIG['hotkey'], self.hotkey)
        keybinder.bind(CONFIG['exit_hotkey'], self.hide)

    def unbind_hotkeys(self):
        """
        Unbind the toggle and hide hotkeys.
        """
        keybinder.unbind(CONFIG['hotkey'])
        keybinder.unbind('Escape')

if __name__ == '__main__':
    app = RationApp()
    app.go()


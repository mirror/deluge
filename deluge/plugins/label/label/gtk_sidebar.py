#
# gtk_sidebar.py
#
# Copyright (C) 2008 Martijn Voncken <mvoncken@gmail.com>
# Copyright (C) 2007 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA    02110-1301, USA.
#


import gtk
import gtk.glade

import deluge.component as component
import deluge.common
from deluge.log import LOG as log
from deluge.ui.client import aclient

STATE_PIX = {
    "Downloading":"downloading",
    "Seeding":"seeding",
    "Paused":"inactive",
    "Checking":"checking",
    "Queued":"queued",
    "Error":"alert"
    }


class LabelSideBar(component.Component):
    def __init__(self):
        component.Component.__init__(self, "LabelSideBar", interval=2000)
        self.window = component.get("MainWindow")
        glade = self.window.main_glade
        self.label_view = glade.get_widget("label_view")
        self.hpaned = glade.get_widget("hpaned")
        self.scrolled = glade.get_widget("scrolledwindow_sidebar")
        self.is_visible = True
        self.filters = {}

        # Create the liststore
        #cat,value,count , pixmap.
        self.liststore = gtk.ListStore(str, str, int, gtk.gdk.Pixbuf)
        self.filters[("state", "All")] = self.liststore.append(["state","All",0,gtk.gdk.pixbuf_new_from_file(
               deluge.common.get_pixmap("dht16.png"))])


        # Create the column
        column = gtk.TreeViewColumn(_("Filters"))
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        render = gtk.CellRendererPixbuf()
        column.pack_start(render, expand=False)
        column.add_attribute(render, 'pixbuf', 3)
        render = gtk.CellRendererText()
        column.pack_start(render, expand=True)
        column.set_cell_data_func(render, self.render_cell_data,None)

        self.label_view.append_column(column)

        self.label_view.set_model(self.liststore)

        self.label_view.get_selection().connect("changed",
                                    self.on_selection_changed)

        # Select the 'All' label on init
        self.label_view.get_selection().select_iter(
            self.liststore.get_iter_first())

        #init.....
        self._start()


    def cb_update_filter_items(self, filter_items):
        for cat,filters in filter_items.iteritems():
            for value, count in filters:
                self.update_row(cat, value , count)

    def update_row(self, cat, value , count ):
        if (cat, value) in self.filters:
            row = self.filters[(cat, value)]
            self.liststore.set_value(row, 2, count)
        else:
            pix = self.get_pixmap(cat, value)
            row = self.liststore.append([cat, value, count , pix])
            self.filters[(cat, value)] = row

    def render_cell_data(self, column, cell, model, row, data):
        "cell renderer"
        value = model.get_value(row, 1)
        count = model.get_value(row, 2)
        txt = "%s (%s)"  % (value, count)
        cell.set_property('text', txt)

    def get_pixmap(self, cat, value):
        if cat == "state":
            pix = STATE_PIX.get(value, "dht")
            return gtk.gdk.pixbuf_new_from_file(deluge.common.get_pixmap("%s16.png" % pix))
        return None


    def visible(self, visible):
        if visible:
            self.scrolled.show()
        else:
            self.scrolled.hide()
            self.hpaned.set_position(-1)

        self.is_visible = visible

    def on_selection_changed(self, selection):
        try:
            (model, row) = self.label_view.get_selection().get_selected()

            cat    = model.get_value(row, 0)
            value = model.get_value(row, 1)

            #gtk-ui has it's own filtering logic on status-fields.
            #not using the label-backend for filtering. (for now)
            #just a few simple hacks to translate label-filters to gtk-filters.
            if cat == "tracker":
                cat = "tracker_host"

            filter = (cat, value)
            if value == "All":
                filter = (None, None)
            elif (cat == "label" and value == "No Label"):
                 filter = ("label","")

            component.get("TorrentView").set_filter(*filter)

        except Exception, e:
            log.debug(e)
            # paths is likely None .. so lets return None
            return None

    def update(self):
        aclient.label_filter_items(self.cb_update_filter_items)



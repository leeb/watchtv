# main.py
#
# Copyright 2024 Lee Briggs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import os
import logging
import gi
#import ffmpeg

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
gi.require_version("GstPlay", "1.0")
gi.require_version("GstPbutils", "1.0")
gi.require_version('Soup', '3.0')

from gi.repository import Gtk, Gio, Adw, Gst, Gdk, GObject
from .window import ApplicationWindow
from .settings import Settings
from .tvhapi import TvhApi

logger = logging.getLogger(__name__)


class Application(Adw.Application):
    """The main application singleton class."""
    __gsignals__ = {
        'channels-loaded': (GObject.SIGNAL_RUN_FIRST, None, ()),   # new channel list
    }
    application_version = GObject.Property(type=str, default="")

    def __init__(self):
        super().__init__(application_id="dev.leeb.WatchTV",
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        css_file = Gio.File.new_for_uri(
            "resource:///dev/leeb/WatchTV/window.css")
        css_provider = Gtk.CssProvider()
        css_provider.load_from_file(css_file)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), 
                                                  css_provider, 
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        win = self.props.active_window
        if not win:
            win = ApplicationWindow(application=self)
        win.present()

        settings = Settings.instance()
        settings.connect('tvhserver-changed', self.on_tvhserver_changed)
        self.on_tvhserver_changed(settings)


    def play_channel_number(self, channel_number):
        if channel_number in self.channels:
            channel = self.channels[channel_number]            
            logger.info(f"Channel: {channel.uuid} {channel.name}")
            uri = self._api.play(channel_number)
            return uri
        

    def channel_number_to_index(self, channel_number, offset=0):
        keys = sorted(list(self.channels))
        try:
            index = keys.index(channel_number)
            index += offset
            if index < 0 or index > len(keys):
                index = None
        except:
            index = None
        return index

    def channel_index_to_number(self, index):
        """Find a relative channel numbers"""
        keys = sorted(list(self.channels))
        if index < 0 or index > len(keys):
            return None
        return keys[index]        

    def on_tvhserver_changed(self, settings):
        self._api = TvhApi(settings.host, 
                           settings.username, 
                           settings.password)
        self.channeltags = {}
        self.channels = {}

        for tag in self._api.get_channeltags():
            self.channeltags[tag.uuid] = tag
        for channel in self._api.get_channels():
            if channel.number:
                self.channels[(channel.number)] = channel

        def dialog_result(dialog, result, data):
            try:
                index = dialog.choose_finish(result)
                if index == 0:
                    self.props.active_window.activate_action('win.preferences')
            except:
                pass

        if len(self.channeltags) == 0 and len(self.channels) == 0:
            dialog = Gtk.AlertDialog(message="No response from server, check configuration?")
            dialog.set_buttons(['Yes', 'No'])
            dialog.choose(self.props.active_window, None, dialog_result, None)

        self.emit('channels-loaded')

    def on_about_action(self, widget, _):
        about = Adw.AboutWindow(transient_for=self.props.active_window,
                                application_name='Watch TV',
                                application_icon='dev.leeb.WatchTV',
                                developer_name='Lee Briggs',
                                version=self.get_property('application-version'),
                                developers=['Lee Briggs'],
                                copyright="© 2024 Lee Briggs")
        about.set_license_type(Gtk.License.GPL_3_0)
        # about.set_comments("hello")   # appears as "Details"
#                                version=self.get_property('application-version'),

        about.add_legal_section("This software uses libraries from the FFmpeg project under the LGPLv2.1",
                                None,
                                Gtk.License.LGPL_2_1,
                                "This is some custom text")

        about.add_legal_section("GTK4 Paintable Sink",
                                None,
                                Gtk.License.MPL_2_0,
                                None)

        about.add_legal_section("Television Logo",
                                None,
                                Gtk.License.CUSTOM,
                                "Wikimedia Commons CC-BY-SA 3.0\nhttps://commons.wikimedia.org/wiki/File:Blank_television_set.svg")

        about.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""

    # debug, info, warning, error, critical
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=LOGLEVEL)

    Gst.init(None)
    logger.info(f"Gst version: {Gst.version()}")    # 1.24.7

    for f in os.listdir('/app/lib'):
        print(f"/app/lib/{f}")
    print("--------------")

    for f in os.listdir('/app'):
        print(f"/app/{f}")
    print("--------------")
    for f in os.listdir('/app/bin'):
        print(f"/app/bin/{f}")
    print("--------------")
    for f in os.listdir('/app/share'):
        print(f"/app/share/{f}")
    print("--------------")



    reg = Gst.Registry.get()
    for x in reg.get_plugin_list():
        print (x.get_name(), x.get_filename())

    avdec_h264 = Gst.ElementFactory.make('avdec_h264', 'decoder')
    logger.info(f"decoder: {avdec_h264} {type(avdec_h264)}")

    openh264 = Gst.ElementFactory.make('openh264dec', 'decoder')
    logger.info(f"decoder: {openh264} {type(openh264)}")



    # list all decoders
    #factories = Gst.ElementFactory.list_get_elements( \
    #    Gst.ELEMENT_FACTORY_TYPE_DECODER | Gst.ELEMENT_FACTORY_TYPE_MEDIA_VIDEO, 
    #    Gst.Rank.MARGINAL)

    #for factory in factories:
    #    print(factory.get_element_type())





    app = Application()
    app.set_property('application-version', version)
    return app.run(sys.argv)

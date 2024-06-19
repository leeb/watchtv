# preferences.py
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

from gi.repository import Gtk, Adw, Gio
import logging
from .settings import Settings
from .tvhapi import TvhApi

logger = logging.getLogger(__name__)


_server_description = """Credentials for TVHeadend Server.
These details will only be saved after a successful connection test.

The host should be the IP address or hostname of the TVH Server.
Note: port is fixed to the default of 9981.
"""



class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.window = window

        self.add(self.create_server_page())
        self.add(self.create_client_page())

        def on_close(window):
            logger.info(f"preferences close request {window}")

        self.connect('close-request', on_close)

    def create_client_page(self):
        page = Adw.PreferencesPage(title="Client")
        page.set_icon_name("applications-system-symbolic")

        group = Adw.PreferencesGroup(title="Interface")
        group.set_description("To-do...")

        page.add(group)
        return page

    def create_server_page(self):
        page = Adw.PreferencesPage(title="Server")
        page.set_icon_name("network-server-symbolic")

        group = Adw.PreferencesGroup(title="TVHeadend Server")
        self.get_application()

        group.set_description(_server_description)
        page.add(group)

        settings = Settings.instance()

        def host_changed(row):
            settings.host = row.get_text()

        def username_changed(row):
            settings.username = row.get_text()

        def password_changed(row):
            settings.password = row.get_text()
        
        row_host = Adw.EntryRow(title="Host")
        row_host.set_text(settings.host)
        group.add(row_host)
        row_host.connect('changed', host_changed)
        #Settings.instance().bind('host', row_host, 'text', Gio.SettingsBindFlags.DEFAULT)
        
        row_username = Adw.EntryRow(title="Username")
        row_username.set_text(settings.username)
        group.add(row_username)
        row_username.connect('changed', username_changed)
        #Settings.instance().bind('username', row_username, 'text', Gio.SettingsBindFlags.DEFAULT)

        row_password = Adw.PasswordEntryRow(title="Password")
        row_password.set_text(settings.password)
        group.add(row_password)
        row_password.connect('changed', password_changed)
        #Settings.instance().bind('password', row_password, 'text', Gio.SettingsBindFlags.DEFAULT)

        footer_group = Adw.PreferencesGroup()
        page.add(footer_group)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # box.set_hexpand(True)
        # box.set_hexpand_set(True)
        # box.add_css_class("debug-box")
        box.set_halign(Gtk.Align.CENTER)
        box.set_spacing(10)
        footer_group.add(box)

        def on_test_configuration(button):    
            button_labels = ["Cancel", "Save"]

            def dialog_result(dialog, result, data):
                try:
                    index = dialog.choose_finish(result)
                    if index == 1:
                        Settings.instance().tvhserver_apply()
                except:
                    pass

            # a cheeky way to reset things for testing...
            if settings.host == "reset" and settings.username == "reset" and settings.password == "reset":
                settings.tvhserver_reset()
                self.close()                
                return
            
            api = TvhApi(settings.host, settings.username, settings.password)
            serverinfo = api.serverinfo()

            if serverinfo is None:
                # failure conditions
                if api.connected == False:
                    dialog = Gtk.AlertDialog(message="Host not found")
                    dialog.show(self)
                
                else:
                    if api.status == 403:
                        dialog = Gtk.AlertDialog(message="Error: 403 Forbidden.\nCheck user credentials and server permissions.")
                    else:
                        dialog = Gtk.AlertDialog(message=f"Error: {api.status}\nCould not communicate with the server")
                    dialog.show(self)

            else:
                if 'api_version' in serverinfo and serverinfo['api_version'] >= 19:
                    dialog = Gtk.AlertDialog(message="Connection successful")
                    dialog.set_buttons(button_labels)
                    dialog.choose(self, None, dialog_result, None)
                else:
                    dialog = Gtk.AlertDialog(message="Connected to server, but API is not compatible")
                    dialog.show(self)

        server_connect_button = Gtk.Button(label="Test Configuration")
        server_connect_button.connect("clicked", on_test_configuration)
        box.append(server_connect_button)

        return page




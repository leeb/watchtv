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
from .settings import Settings
from .tvhapi import TvhApi


class PreferencesWindow(Adw.PreferencesWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #self.window = window

        self.add(self.create_server_page())
        page2 = Adw.PreferencesPage(title="Client")
        self.add(page2)
        #page.add(self.create_server_page())

        def on_close(window):
            print(f"preferences close request {window}")

        self.connect('close-request', on_close)


    def create_server_page(self):
        page = Adw.PreferencesPage(title="Server")

        group = Adw.PreferencesGroup(title="TVHeadend Server")
        page.add(group)

        settings = Settings.instance()

        def host_changed(row):
            print(f"host changed {row}")
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

        def on_server_connect(button):
            if Settings.instance().tvhserver_has_changed():
                print("Server settings have changed")
                
                if self.test_server_connection():
                    print("server details good")
                    # emit a reload event
                    Settings.instance().tvhserver_apply()

                else:
                    print("server details bad")


        server_connect_button = Gtk.Button(label="Connect")
        server_connect_button.connect("clicked", on_server_connect)
        box.append(server_connect_button)

        return page


    def test_server_connection(self) -> bool:
        settings = Settings.instance()
        api = TvhApi(settings.host, settings.username, settings.password)
        print(f"  calling server info")
        serverinfo = api.serverinfo()
        print(f"  raw response: {serverinfo}")

        try:
            if serverinfo['api_version'] >= 19:
                return True
        except:
            pass
        return False








# settings.py
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

from gi.repository import GObject, Gio
from typing import Self


class Settings(Gio.Settings):
    _instance = None

    __gsignals__ = {
        'tvhserver-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    #def __new__(cls, *args, **kwargs):
    #    if not cls._instance:
    #        cls._instance = super(Settings, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def instance(cls) -> Self:
        """Return an active instance of Settings."""
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    def __init__(self):        
        super().__init__(schema_id='dev.leeb.WatchTV')
        self._host = None
        self._username = None
        self._password = None

    #def set_tvhserver(self, host: str, username: str, password: str):
    #    self._host = host
    #    self._username = username
    #    self._password = password
        #self.set_string('host', host)
        #self.set_string('username', username)
        #self.set_string('password', password)

    #def get_tvhserver(self) -> (str, str, str):
    #    if self._username is None:
    #        self._username = self.get_string('username')
    #    if self._password is None:
    #        self._password = self.get_string('password')
    #    return (self._host, self._username, self._password)

    def tvhserver_apply(self):
        """Copy the volatile server details into Gio.Settings (dconf)"""
        self.set_string('host', self._host)
        self.set_string('username', self._username)
        self.set_string('password', self._password)
        self.emit('tvhserver-changed')

    def tvhserver_reset(self):
        self.reset('host')
        self.reset('username')
        self.reset('password')
        self._host = None
        self._username = None
        self._password = None

    def tvhserver_has_changed(self):
        if self._host != self.get_string('host'):
            return True
        if self._username != self.get_string('username'):
            return True
        if self._password != self.get_string('password'):
            return True
        
    @property
    def host(self) -> str:
        if self._host is None:
            self._host = self.get_string('host')
        return self._host
    
    @host.setter
    def host(self, hostname: str):
        self._host = hostname
        #self.set_string('host', host)

    @property
    def username(self) -> str:
        if self._username is None:
            self._username = self.get_string('username')
        return self._username
    
    @username.setter
    def username(self, username: str):
        self._username = username
        #self.set_string('username', username)

    @property
    def password(self) -> str:
        if self._password is None:
            self._password = self.get_string('password')
        return self._password
    
    @password.setter
    def password(self, password: str):
        self._password = password
        #self.set_string('password', password)

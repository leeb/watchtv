# tvhapi.py
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

from gi.repository import Gio, Soup
import logging
import json
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class ChannelTag():
    def __init__(self, data={}):
        self.uuid = data.get('uuid')
        self.name = data.get('name', '')
        self.private = data.get('private', False)
        self.internal = data.get('internal', False)

    def __str__(self):
        return f"ChannelTag {self.uuid} {self.name}"


class Channel():
    def __init__(self, data={}):        
        self.uuid = data.get('uuid')
        self.name = data.get('name', '')
        self.number = data.get('number', 0)
        self.enabled = data.get('enabled', False)
        self.tags = data.get('tags', [])
        self.services = data.get('services', [])
        #self.epgauto = data.get('epgauto', False)
        #self.autoname = data.get('autoname', True)

    def __str__(self):
        return f"Channel {self.uuid} {self.number:3d} {self.name}"


class TvhApi():
    def __init__(self, host, username, password):
        self._host = host
        self._username = username
        self._password = password
        self.connected = None
        self.status = None

    def __request(self, url, **kwargs):
        def on_auth(msg, auth, retrying):
            if auth.get_scheme_name() == 'Digest':
                auth.authenticate(self._username, self._password)

        session = Soup.Session()
        session.set_property('accept-language-auto', True)
        session.set_property('user-agent', 'WatchTV')
        params = ""
        if kwargs:
            params = f"?{urlencode(kwargs)}"
        uri = f"http://{self._host}:9981/{url}{params}"
        message = Soup.Message.new('GET', uri)
        message.connect('authenticate', on_auth)
        #logger.debug(f"Soup request {uri}")
        
        #WARNING:watchtv.tvhapi:Soup exception: <class 'gi.repository.GLib.GError'> g-io-error-quark: Could not connect to 192.168.21.121: No route to host (37)

        try:
            bytes = session.send_and_read(message)
            self.connected = True
        except Exception as e:
            self.connected = False
            logger.info(f"Soup exception: {e}")

        self.status = message.get_status()
        if self.status == 200 and bytes:
            return bytes.get_data().decode("utf-8")
        else:
            logger.info(f"Server status: {message.get_status()}")

        return None
    
    def json_request(self, url, **kwargs):
        r = self.__request(f"api/{url}", **kwargs)
        if r is None:
            return None
        return json.loads(r, strict=False)

    def serverinfo(self):
        return self.json_request('serverinfo')

    def play(self, channel_number):
        r = self.__request(f"play/ticket/stream/channelnumber/{channel_number}")
        url = None
        logger.debug(r)
        for line in r.splitlines():
            if line[0] == '#':
                continue
            url = line
        return url

    def get_channeltags(self):
        data = self.json_request('channeltag/grid')
        r = []
        if data:
            for entry in data.get('entries', []):
                r.append(ChannelTag(entry))
        return r
        
    def get_channels(self):
        data = self.json_request('channel/grid', limit=1000)
        r = []
        if data:
            for entry in data.get('entries', []):
                r.append(Channel(entry))
        return r

    def ping(self):
        pass

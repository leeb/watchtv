# window.py
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

from gi.repository import Adw, Gtk, Gst, Gdk, Gio, GLib, GObject
import math
import logging
from .channels import ChannelController
from .preferences import PreferencesWindow
from .videosize import VideoSize
from .gstflags import GstPlayFlags

logger = logging.getLogger(__name__)


@Gtk.Template(resource_path='/dev/leeb/WatchTV/window.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ApplicationWindow'

    header_bar: Gtk.HeaderBar = Gtk.Template.Child()
    channel_listbox: Gtk.ListBox = Gtk.Template.Child()
    video_picture: Gtk.Picture = Gtk.Template.Child()
    split_view: Adw.OverlaySplitView = Gtk.Template.Child()

    fullscreen_button: Gtk.Button = Gtk.Template.Child()
    sidebar_button: Gtk.ToggleButton = Gtk.Template.Child()
    vidctrl_button: Gtk.Button = Gtk.Template.Child()

    channel_label: Gtk.Label = Gtk.Template.Child()
    alert_label: Gtk.Label = Gtk.Template.Child()
    setting_label: Gtk.Label = Gtk.Template.Child()

    channel_number = GObject.Property(type=int, default=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
        self.set_title("Watch TV")
        self.playbin_state = None
        self.set_default_size(1024, 622)
        self.video_size = VideoSize()

        self.init_playbin()
        self.init_events()
        self.init_channel_control()
        self.init_volume_control()
        self.create_actions()

        self.get_application().connect('channels-loaded', self.on_channels_loaded)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.get_application().set_accels_for_action(f"win.{name}", shortcuts)

    def create_actions(self):
        def on_show_subtitles(action, value):
            action.set_state(value)
            self.set_show_subtitles(value.get_boolean())
            if value.get_boolean():
                self.set_alert_label("Subtitles On")
            else:
                self.set_alert_label("Subtitles Off")

        def on_fullscreen(action, _):
            if self.is_fullscreen():
                self.unfullscreen()
                self.header_bar.show()
            else:
                self.header_bar.hide()
                self.fullscreen()

        def on_video_size_half(action, value):
            self.video_size.set_scale(0.5)

        def on_video_size_original(action, value):
            self.video_size.set_scale(1)

        def on_video_size_double(action, value):
            self.video_size.set_scale(2)

        def on_video_control(action, _):
            if self.playbin_state == Gst.State.PLAYING:
                self.playbin.set_state(Gst.State.READY)
                self.set_alert_label("STOP")
            elif self.playbin_state == Gst.State.READY:
                self.playbin.set_state(Gst.State.PLAYING)
                self.set_alert_label("PLAY")

        def on_channels(action, _):
            self.split_view.set_show_sidebar(not self.split_view.get_show_sidebar())

        def on_preferences(action, _):
            dialog = PreferencesWindow()
            dialog.set_modal(True)
            dialog.set_transient_for(self)
            dialog.present()

        subtitles_action = Gio.SimpleAction.new_stateful('toggle-subtitles', None, GLib.Variant.new_boolean(False))
        subtitles_action.connect("change-state", on_show_subtitles)
        self.add_action(subtitles_action)
        self.get_application().set_accels_for_action("win.toggle-subtitles", ['s'])

        self.create_action('toggle-fullscreen', on_fullscreen, 'f')
        self.create_action('video-size-half', on_video_size_half, ['<Alt>0'])
        self.create_action('video-size-original', on_video_size_original, ['<Alt>1'])
        self.create_action('video-size-double', on_video_size_double, ['<Alt>2'])
        self.create_action('video-control', on_video_control)
        self.create_action('toggle-channels', on_channels, 'c')
        self.create_action('preferences', on_preferences)

    def init_events(self):
        def on_fullscreened(appwindow, fullscreened):
            if self.is_fullscreen():
                self.fullscreen_button.set_icon_name("view-restore-symbolic")
            else:
                self.fullscreen_button.set_icon_name("view-fullscreen-symbolic")

        def on_video_size(video_size, width, height):
            header_height = self.get_height() - self.video_picture.get_height()
            logger.info(f"on_resize {video_size} {width} {height} {header_height}")
            self.set_default_size(width, height + header_height)
            #self.content.set_size_request(width, height)

        def on_channel_number(appwindow, param):
            uri = self.get_application().play_channel_number(self.get_property('channel-number'))
            if uri is not None:
                self.play_stream(uri)

        def on_sidebar_show(split_view, property):
            logger.info(f"sidebar show {split_view} : {property}")
            if self.sidebar_button.get_active() != split_view.get_show_sidebar():
                self.sidebar_button.set_active(split_view.get_show_sidebar())

        def on_gesture_release(gesture, n, x, y):
            def single_click():
                self.split_view.set_show_sidebar(True)
                self._gesture_click_timeout = None
                return False
            w = self.get_property('default-width')
            if n == 1:
                if x < (w / 3): # only use single clicks in the left third fo the screen
                    self._gesture_click_timeout = GLib.timeout_add(500, single_click)
            if n == 2:
                if getattr(self, "_gesture_click_timeout", None):
                    GLib.source_remove(self._gesture_click_timeout)
                    self._gesture_click_timeout = None
                self.activate_action('win.toggle-fullscreen')

        self.connect('notify::fullscreened', on_fullscreened)
        self.video_size.connect('resize', on_video_size)
        self.connect('notify::channel-number', on_channel_number)
        self.split_view.connect('notify::show-sidebar', on_sidebar_show)

        gesture = Gtk.GestureClick()
        gesture.set_button(1)
        gesture.connect('released', on_gesture_release)
        self.video_picture.add_controller(gesture)

    def init_channel_control(self):
        def change_channel(channel_number, offset=0):
            index = self.get_application().channel_number_to_index(channel_number)
            if index is not None:
                row = self.channel_listbox.get_row_at_index(index + offset)
                if row:
                    row.activate()
                    logger.info(f"row: {row}")

        def on_preview(channel_controller, channel_number):
            self.channel_label.set_label(f"{channel_number}")

        def on_show(channel_controller):
            self.channel_label.show()

        def on_hide(channel_controller):
            self.channel_label.hide()

        def on_select(channel_controller, channel_number):
            change_channel(channel_number)

        def on_key_pressed(event_controller, keyval, keycode, modifier):
            logger.debug(f"key pressed {event_controller} {keyval} {keycode} {modifier}")

            if not modifier:
                if keyval == Gdk.KEY_Return or keyval == Gdk.KEY_KP_Enter:
                    self.channel_controller.select()

                if keyval >= Gdk.KEY_0 and keyval <= Gdk.KEY_9:
                    self.channel_controller.enter_number(keyval - Gdk.KEY_0)

                if keyval >= Gdk.KEY_KP_0 and keyval <= Gdk.KEY_KP_9:
                    self.channel_controller.enter_number(keyval - Gdk.KEY_KP_0)

        def on_channel_up(action, _):
            change_channel(self.get_property('channel-number'), 1)

        def on_channel_down(action, _):
            change_channel(self.get_property('channel-number'), -1)

        def on_channelrow_activated(listbox, row):
            logger.info(f"row activated {listbox} {row} {row.channel.number}")
            self.set_alert_label(row.channel.name)
            self.set_property('channel-number', row.channel.number)

        self.channel_listbox.connect('row-activated', on_channelrow_activated)

        self.channel_controller = ChannelController()
        self.channel_controller.connect("preview", on_preview)
        self.channel_controller.connect("show", on_show)
        self.channel_controller.connect("hide", on_hide)
        self.channel_controller.connect("select", on_select)

        event_controller = Gtk.EventControllerKey()
        event_controller.connect("key-pressed", on_key_pressed)
        self.add_controller(event_controller)

        self.create_action('channel-up', on_channel_up, ['Page_Up'])
        self.create_action('channel-down', on_channel_down, ['Page_Down'])

    def init_volume_control(self):
        def on_dec_volume(*_):
            vol = math.cbrt(self.playbin.get_property('volume'))
            volp = max(0, vol - 0.02)
            self.playbin.set_property('volume', volp**3)
            self.set_setting_label(f"Volume: {round(volp * 100)}%")

        def on_inc_volume(*_):
            vol = math.cbrt(self.playbin.get_property('volume'))
            vol = min(1.5, vol + 0.02)
            self.playbin.set_property('volume', vol**3)
            self.set_setting_label(f"Volume: {round(vol * 100)}%")

        def on_scroll(controller, dx, dy):
            if dy > 0.5:
                on_dec_volume()
            elif dy < -0.5:
                on_inc_volume()

        def on_toggle_mute(action, value):
            if self.playbin.get_property('mute'):
                self.playbin.set_property('mute', False)
            else:
                self.playbin.set_property('mute', True)

        scroll_controller = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll_controller.connect("scroll", on_scroll)
        self.add_controller(scroll_controller)

        # use a stateful action so that a tick is shown on the menu
        mute_action = Gio.SimpleAction.new_stateful('mute', None, GLib.Variant.new_boolean(False))
        mute_action.connect("change-state", on_toggle_mute)
        self.add_action(mute_action)
        self.get_application().set_accels_for_action("win.mute", ['m'])

        self.create_action('decrease-volume', on_dec_volume, ['j'])
        self.create_action('increase-volume', on_inc_volume, ['k'])

        def on_mute_changed(playbin, param):
            if self._mute != self.playbin.get_property('mute'):
                self._mute = self.playbin.get_property('mute')
                if self._mute:
                    mute_action.set_state(GLib.Variant.new_boolean(True))
                    self.set_setting_label("Mute: On")
                else:
                    mute_action.set_state(GLib.Variant.new_boolean(False))
                    self.set_setting_label("Mute: Off")

        # mute seems to notify whenever the volume is changed, 
        # so also use a shadow value to test against
        self._mute = self.playbin.get_property('mute')
        self.playbin.connect('notify::mute', on_mute_changed)

    def set_setting_label(self, label, seconds=4):
        def label_timeout():
            self.setting_label.set_visible(False)
            self._setting_label_timeout = None
            return False

        # remove a timer if one already exists
        if getattr(self, "_setting_label_timeout", None):
            GLib.source_remove(self._setting_label_timeout)

        self.setting_label.set_label(label)        
        self.setting_label.set_visible(True)
        self._setting_label_timeout = GLib.timeout_add_seconds(4, label_timeout)

    def set_alert_label(self, label, seconds=4):
        def label_timeout():
            self.alert_label.set_visible(False)
            self._alert_label_timeout = None
            return False

        # remove a timer if one already exists
        if getattr(self, "_alert_label_timeout", None):
            GLib.source_remove(self._alert_label_timeout)

        self.alert_label.set_label(label)        
        self.alert_label.set_visible(True)
        self._alert_label_timeout = GLib.timeout_add_seconds(4, label_timeout)

    def on_channels_loaded(self, app):
        self.channel_listbox.remove_all()

        for key in sorted(app.channels.keys()):
            channel = app.channels[key]

            name_label = Gtk.Label(label=channel.name)
            number_label = Gtk.Label(label=channel.number, width_chars=8)

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.append(number_label)
            box.append(name_label)

            row = Gtk.ListBoxRow(child=box)
            row.channel = channel
            self.channel_listbox.append(row)

    def init_playbin(self):
        video_sink = Gst.ElementFactory.make("gtk4paintablesink", "sink")
        self.video_picture.set_size_request(512, 288)
        self.video_picture.set_paintable(video_sink.props.paintable)

        self.playbin = Gst.ElementFactory.make("playbin3")
        self.playbin.set_property("video-sink", video_sink) # video_bin

        # set player defaults
        self.set_show_subtitles(False)
        self.playbin.set_property('mute', False)

        # this function is called when the pipeline changes states.
        def on_state_changed(bus, msg):
            if msg.src != self.playbin:
                return
            old_state, new_state, pending_state = msg.parse_state_changed()
            self.playbin_state = new_state

            logger.info("State changed from {0} to {1}".format(
                Gst.Element.state_get_name(old_state), 
                Gst.Element.state_get_name(new_state)))

            if new_state == Gst.State.READY:
                self.vidctrl_button.set_icon_name("media-playback-start-symbolic")
                self.vidctrl_button.set_visible(True)

            elif new_state == Gst.State.PAUSED:
                self.vidctrl_button.set_icon_name("media-playback-start-symbolic")
                self.vidctrl_button.set_visible(True)

            elif new_state == Gst.State.PLAYING:
                self.vidctrl_button.set_icon_name("media-playback-stop-symbolic")
                self.vidctrl_button.set_visible(True)
                self.query_video_resolution()
            
            else:
                self.vidctrl_button.set_visible(False)

            #if old_state == Gst.State.READY and new_state == Gst.State.PAUSED:
                #pass

        # obtain the bus to monitor for state changes
        bus = self.playbin.get_bus()
        bus.add_signal_watch()

        bus.connect("message::state-changed", on_state_changed)

    def set_show_subtitles(self, show):
        logger.info(f"set show subtitles {show}")
        flags = self.playbin.get_property("flags")
        if show:
            flags |= GstPlayFlags.TEXT
        else:
            flags &= ~GstPlayFlags.TEXT

        self.playbin.set_property("flags", flags)

    def query_video_resolution(self):
        video_sink = self.playbin.get_property('video-sink')
        if video_sink:
            sink_pad = video_sink.get_static_pad("sink")
            if sink_pad:
                caps = sink_pad.get_current_caps()
                if caps:
                    structure = caps.get_structure(0)
                    #logger.info(structure.to_string())

                    if structure.has_field("width") and structure.has_field("height") and \
                                                        structure.has_field("pixel-aspect-ratio"):
                        width = structure.get_int("width")[1]
                        height = structure.get_int("height")[1]
                        result, par_num, par_den = structure.get_fraction("pixel-aspect-ratio")

                        #logger.info(f"Pixel aspect ratio: {par}")
                        logger.info(f"Queried Video resolution: {width}x{height}")
                        logger.info(f"Pixel aspect ratio: {par_num}/{par_den}")

                        self.video_size.set_video(width, height, par_num, par_den)

    def play_stream(self, uri):
        logger.info(f"play stream {uri}")
        self.playbin.set_state(Gst.State.READY)
        self.playbin.set_property('uri', uri)
        self.playbin.set_state(Gst.State.PLAYING)

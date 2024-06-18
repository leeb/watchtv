from gi.repository import GObject, GLib

class ChannelController(GObject.GObject):
    """Manage direct entry of channel numbers using the keyboard"""
    COUNTDOWN_TIME = 16
    SELECT_TIME = 12

    __gsignals__ = {
        'preview': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'select': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
        'show': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'hide': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }
    
    def __init__(self):
        super().__init__()
        self._entry = 0
        self._counter = 0
        
    def _interval(self):
        if self._counter:
            if self._counter == self.SELECT_TIME:
                self.emit("select", self._entry)
            self._counter -= 1
            return True
        else:
            self.emit('hide')
            self._entry = 0     # reset channel number
            return False
    
    def select(self):
        if self._counter >= self.SELECT_TIME:
            self._counter = self.SELECT_TIME - 1
            self.emit("select", self._entry)

    def enter_number(self, num):
        if self._counter == 0:
            GLib.timeout_add(250, self._interval)
            self.emit('show')
        self._counter = self.COUNTDOWN_TIME

        entry = (self._entry % 100) * 10;
        self._entry = entry + num
        self.emit('preview', self._entry)



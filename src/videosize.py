from gi.repository import GObject


class VideoSize(GObject.GObject):
    __gsignals__ = {
        'resize': (GObject.SIGNAL_RUN_FIRST, None, (int, int)),
    }

    def __init__(self):
        super().__init__()
        self.width = 704
        self.height = 576
        self.aspect_num = 16
        self.aspect_denom = 11
        self.screen_width = 1920
        self.screen_height = 1080
        self.scale = 1

    def _refresh(self):
        self.screen_height = self.height * self.scale
        self.screen_width = ((self.width * self.aspect_num) / self.aspect_denom) * self.scale

    def set_scale(self, scale):
        self.scale = scale
        self._refresh()
        self.emit('resize', self.screen_width, self.screen_height)

    def set_video(self, width=None, height=None, aspect_num=None, aspect_denom=None):
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        if aspect_num is not None:
            self.aspect_num = aspect_num
        if aspect_denom is not None:
            self.aspect_denom = aspect_denom
        self._refresh()

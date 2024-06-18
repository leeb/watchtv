# default = 0x0717 default
class GstPlayFlags:
    VIDEO               = 0x0001
    AUDIO               = 0x0002
    TEXT                = 0x0004
    VIS                 = 0x0008    # Render visualisation when no video is present
    SOFT_VOLUME         = 0x0010    # Use software volume
    NATIVE_AUDIO        = 0x0020    # Only use native audio formats
    NATIVE_VIDEO        = 0x0040    # Only use native video formats
    DOWNLOAD            = 0x0080    # Attempt progressive download buffering
    BUFFERING           = 0x0100    # Buffer demuxed/parsed data
    DEINTERLACE         = 0x0200    # Deinterlace video if necessary
    SOFT_COLORBALANCE   = 0x0400    # Use software color balance
    FORCE_FILTERS       = 0x0800    # Force audio/video filter(s) to be applied
    FORCE_SW_DECODERS   = 0x1000    # Force only software-based decoders (no effect for playbin3)

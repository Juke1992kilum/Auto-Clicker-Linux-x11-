import ctypes

x11 = ctypes.cdll.LoadLibrary("libX11.so.6")
xtst = ctypes.cdll.LoadLibrary("libXtst.so.6")

x11.XOpenDisplay.restype = ctypes.c_void_p


class FastClickerCore:
    def __init__(self):
        self.display = x11.XOpenDisplay(None)

        if not self.display:
            raise RuntimeError("Could not open X11 display.")

    def click(self):
        xtst.XTestFakeButtonEvent(self.display, 1, True, 0)
        xtst.XTestFakeButtonEvent(self.display, 1, False, 0)
        x11.XFlush(self.display)
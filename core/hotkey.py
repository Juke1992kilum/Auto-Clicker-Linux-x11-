from Xlib import X, XK, display


class GlobalHotkey:
    def __init__(self, hotkey_name, callback):
        self.hotkey_name = hotkey_name
        self.callback = callback
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        d = display.Display()
        root = d.screen().root

        keysym = XK.string_to_keysym(self.hotkey_name)
        keycode = d.keysym_to_keycode(keysym)

        modifiers = (
            0,
            X.LockMask,
            X.Mod2Mask,
            X.LockMask | X.Mod2Mask,
        )

        for mod in modifiers:
            try:
                root.grab_key(
                    keycode,
                    mod,
                    True,
                    X.GrabModeAsync,
                    X.GrabModeAsync,
                )
            except Exception:
                pass

        d.flush()

        while self.running:
            event = d.next_event()
            if event.type == X.KeyPress:
                self.callback()
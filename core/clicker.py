import time
import threading
from .x11_click import FastClickerCore


class ClickController:
    def __init__(self):
        self.core = FastClickerCore()
        self.running = False
        self.interval = 0.1
        self.thread = None

    def _worker(self):
        click = self.core.click
        next_time = time.perf_counter()

        while self.running:
            now = time.perf_counter()

            if now >= next_time:
                click()
                next_time += self.interval
            else:
                time.sleep(min(next_time - now, 0.01))

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="ClickThread"
        )
        self.thread.start()

    def stop(self):
        if not self.running:
            return

        self.running = False

        # ✅ safer shutdown (prevents ghost thread execution)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)

        self.thread = None
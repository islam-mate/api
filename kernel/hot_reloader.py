import threading
import time
import os


class HotReloader:
    def __init__(self):
        self.config_path = "config.yaml"
        self.last_modified = None
        self._thread = None
        self._running = False

    def start(self):
        self.last_modified = os.path.getmtime(self.config_path)
        self._running = True
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()
        print("Hot reloader started - watching config.yaml")

    def stop(self):
        self._running = False
        print("Hot reloader stopped")

    def _watch(self):
        while self._running:
            try:
                modified = os.path.getmtime(self.config_path)
                if modified != self.last_modified:
                    self.last_modified = modified
                    print("config.yaml changed - reloading modules...")
            except FileNotFoundError:
                pass
            time.sleep(2)

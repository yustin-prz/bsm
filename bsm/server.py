import os
import sys
import subprocess

from PyQt6.QtCore import QThread, pyqtSignal


# ── Server reader thread ───────────────────────────────────────────────────────
class ServerThread(QThread):
    output_received = pyqtSignal(str)
    server_stopped  = pyqtSignal()

    def __init__(self, server_path):
        super().__init__()
        self.server_path = server_path
        self.process = None

    def run(self):
        try:
            self.process = subprocess.Popen(
                [self.server_path],
                cwd=os.path.dirname(self.server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            for line in self.process.stdout:
                self.output_received.emit(line.rstrip())
            self.process.wait()
        except Exception as e:
            self.output_received.emit(f"[ERROR] {e}")
        self.server_stopped.emit()

    def send_command(self, cmd):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
            except Exception:
                pass

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
            except Exception:
                self.process.terminate()

from __future__ import annotations
import multiprocessing as mp
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from PySide6.QtCore import QObject, QTimer, Signal
from .worker import worker_main


class JobController(QObject):
    event = Signal(str, object)
    finished = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = None
        self.receiver = None
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.poll)
        self.ctx = mp.get_context('spawn')
        self.stop_at = None
        self.outcome = None
        self.temp = None
        self.killer = None

    @property
    def busy(self):
        return self.process is not None

    def start(self, kind, payload):
        if self.busy:
            raise RuntimeError('Worker already running')
        self.receiver, sender = self.ctx.Pipe(duplex=False)
        self.cancel_event = self.ctx.Event()
        self.temp = tempfile.mkdtemp(prefix='LocalTranscriber-')
        self.process = self.ctx.Process(target=worker_main,
            args=(sender, self.cancel_event, kind, payload, self.temp), daemon=True)
        self.stop_at, self.outcome, self.killer = None, None, None
        try:
            self.process.start()
        except Exception:
            self.process = None
            self.receiver.close()
            shutil.rmtree(self.temp, ignore_errors=True)
            raise
        finally:
            sender.close()
        self.timer.start()

    def cancel(self):
        if self.busy and self.stop_at is None:
            self.cancel_event.set()
            self.stop_at = time.monotonic()

    def poll(self):
        if not self.busy:
            return
        try:
            for _ in range(200):
                if not self.receiver.poll():
                    break
                kind, data = self.receiver.recv()
                if kind in ('result', 'error', 'cancelled'):
                    self.outcome = (kind, data)
                else:
                    self.event.emit(kind, data)
        except (EOFError, OSError):
            pass
        if self.stop_at is not None and self.process.is_alive() and time.monotonic() - self.stop_at > 3:
            if sys.platform == 'win32':
                if self.killer is None:
                    # Kill descendants (including ffmpeg) before deleting job temp files.
                    self.killer = subprocess.Popen(['taskkill', '/PID', str(self.process.pid), '/T', '/F'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW)
                elif self.killer.poll() is not None and self.process.is_alive():
                    self.process.kill()
            else:
                try:
                    os.killpg(self.process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if not self.process.is_alive():
            # Drain the final IPC frame before declaring completion.
            try:
                while self.receiver.poll():
                    kind, data = self.receiver.recv()
                    if kind in ('result', 'error', 'cancelled'):
                        self.outcome = kind, data
                    else:
                        self.event.emit(kind, data)
            except (EOFError, OSError):
                pass
            self.timer.stop()
            self.process.join(timeout=0)
            self.process.close()
            self.process = None
            self.receiver.close()
            shutil.rmtree(self.temp, ignore_errors=True)
            if self.stop_at is not None:
                self.outcome = ('cancelled', None)
            outcome = self.outcome or ('error', {'message': 'ワーカーが予期せず終了しました。', 'code': 'WorkerExit'})
            self.finished.emit(*outcome)

"""Runs camera reads + MediaPipe/Keras inference off the Qt UI thread.

The worker is the only reader of ``engine`` while it is alive. It keeps just the latest
frame and the latest prediction (stale ones are dropped, never queued). Qt widgets are
only touched by the UI thread, which polls ``take()``.
"""
import faulthandler
import logging
import os
import threading
import time
from time import monotonic

log = logging.getLogger(__name__)

NO_FRAME_TIMEOUT = 5.0   # seconds without any frame from a still-"open" camera
STACK_DUMP_AFTER = 8     # dump all thread stacks if the loop makes no progress this long


class InferenceWorker:
    def __init__(self, engine, *, no_frame_timeout=NO_FRAME_TIMEOUT, dump_path='lifecycle.log'):
        self.engine = engine
        self.predict_enabled = True
        # DIAGNOSTIC (temporary): skip MediaPipe + Keras, keep camera capture and preview.
        self._no_inference = os.environ.get("SENYASABI_DIAG_NO_INFERENCE") == "1"
        log.warning("Inference worker diagnostic mode SENYASABI_DIAG_NO_INFERENCE=%s",
                    "ENABLED (no MediaPipe/Keras)" if self._no_inference else "disabled")
        self._timeout = no_frame_timeout
        self._dump_path = dump_path
        self._stop = threading.Event()
        self._active = threading.Event()
        self._active.set()
        self._reset = threading.Event()
        self._lock = threading.Lock()
        self._latest = self._pred = self._error = None
        self._exited = self._close_on_exit = False
        self._thread = threading.Thread(target=self._loop, name='sign-inference', daemon=True)
        self._thread.start()

    # ---- UI-thread API -------------------------------------------------
    def take(self):
        """Return (latest_result, latest_predicted_result, error); results are consumed once."""
        with self._lock:
            latest, pred, self._latest, self._pred = self._latest, self._pred, None, None
            return latest, pred, self._error

    def set_active(self, active):
        (self._active.set if active else self._active.clear)()

    def request_reset(self):
        """Sequence reset is executed by the worker so the buffer is never touched concurrently."""
        with self._lock:
            self._pred = None
        self._reset.set()

    def shutdown(self, timeout=1.5):
        """Stop the loop. True: worker is gone and the caller may close the engine.
        False: worker is stuck in a native call and will close the engine itself when it exits."""
        self._stop.set()
        self._active.set()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout)
        with self._lock:
            if self._exited:
                return True
            self._close_on_exit = True
        log.warning('Inference worker did not stop within %.1fs; it will close the engine on exit', timeout)
        return False

    # ---- worker thread -------------------------------------------------
    def _fail(self, error):
        with self._lock:
            self._error = error

    def _loop(self):
        dump_file, last_arm = None, 0.0
        count = total = peak = 0.0
        stats_at = last_slow_log = 0.0
        frames, last_ok = 0, monotonic()
        try:
            try:
                dump_file = open(self._dump_path, 'a', encoding='utf-8')
                dump_file.write(f"\n[{time.strftime('%H:%M:%S')}] inference worker started\n")
                dump_file.flush()
            except OSError:
                dump_file = None
            while not self._stop.is_set():
                if not self._active.is_set():
                    if dump_file:
                        faulthandler.cancel_dump_traceback_later()
                        last_arm = 0.0
                    last_ok = monotonic()
                    self._active.wait(0.1)
                    continue
                if self._reset.is_set():
                    self._reset.clear()
                    self.engine.reset_sequence()
                if dump_file and monotonic() - last_arm > 1.0:
                    faulthandler.dump_traceback_later(STACK_DUMP_AFTER, file=dump_file)
                    last_arm = monotonic()
                predict = self.predict_enabled and frames % 2 == 1 and not self._no_inference
                result = self.engine.read_frame(predict=predict)
                now = monotonic()
                if result is None:
                    if not self.engine.camera_open():
                        log.warning('Camera no longer open; stopping inference')
                        self._fail('Camera disconnected. Reopen the lesson to retry.')
                        return
                    if now - last_ok > self._timeout:
                        log.warning('No camera frame for %.1fs; treating as disconnected', now - last_ok)
                        self._fail('Camera disconnected. Reopen the lesson to retry.')
                        return
                    self._stop.wait(0.02)
                    continue
                frames += 1
                last_ok = now
                with self._lock:
                    self._latest = result
                    if predict:
                        self._pred = result
                if predict:
                    ms = getattr(self.engine, 'last_inference_ms', None)
                    if isinstance(ms, (int, float)):
                        count += 1
                        total += ms
                        peak = max(peak, ms)
                        if ms > 300 and now - last_slow_log > 5:
                            last_slow_log = now
                            log.warning('Slow inference: %.0f ms', ms)
                if now - stats_at > 30:
                    if count and (peak > 200 or total / count > 100):
                        log.warning('Inference over last window: n=%d avg=%.0f ms max=%.0f ms',
                                    count, total / count, peak)
                    count = total = peak = 0.0
                    stats_at = now
                self._stop.wait(0.001)
        except Exception as error:
            log.exception('Inference worker failed')
            self._fail(error)
        finally:
            if dump_file:
                try:
                    faulthandler.cancel_dump_traceback_later()
                    dump_file.close()
                except Exception:
                    pass
            with self._lock:
                self._exited = True
                close = self._close_on_exit
            if close:
                try:
                    self.engine.close()
                except Exception:
                    log.exception('Engine close after worker exit failed')


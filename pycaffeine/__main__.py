import sys
import time
from pathlib import Path
from pycaffeine.constants import DEFAULT_SLEEP_INTERVAL, MOVE_PIXELS, SLEEP_INTERVAL_CHOICES, STATE_META
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

# PyInstaller sets sys._MEIPASS to the temp extract dir; dev uses project root
_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
_ASSETS_DIR = _BASE / "assets"


def make_tray_icon(state: str = "active") -> QIcon:
    return QIcon(str(_ASSETS_DIR / STATE_META[state]["icon"]))


class CaffeineWorker(QThread):
    started_signal = pyqtSignal()
    stopped_signal = pyqtSignal()

    def __init__(self, interval: int) -> None:
        super().__init__()
        self._running = False
        self.interval = interval

    def run(self) -> None:
        # mouseinfo (an optional pyautogui helper, unused here) calls sys.exit() at
        # import time when tkinter is broken. Block it so pyautogui catches the
        # ImportError and degrades gracefully — mouse movement only needs Xlib.
        sys.modules.setdefault("mouseinfo", None)
        try:
            import pyautogui
        except Exception as exc:
            print(f"Caffeine: cannot import pyautogui, mouse movement disabled: {exc!r}", file=sys.stderr)
            self.stopped_signal.emit()
            return

        self._running = True
        self.started_signal.emit()
        while self._running:
            pyautogui.move(MOVE_PIXELS, 0)
            self._sleep(self.interval)
            if not self._running:
                break
            pyautogui.move(-MOVE_PIXELS, 0)
            self._sleep(self.interval)
        self.stopped_signal.emit()

    def _sleep(self, seconds: int) -> None:
        """Sleep in small increments for responsive stop."""
        for _ in range(seconds * 10):
            if not self._running:
                return
            time.sleep(0.1)

    def stop(self) -> None:
        self._running = False


class CaffeineTray(QSystemTrayIcon):
    def __init__(self) -> None:
        super().__init__()
        self._worker: CaffeineWorker | None = None
        self._interval = DEFAULT_SLEEP_INTERVAL
        self._build_menu()
        self._apply_state("stopped")
        self.show()
        self._start()

    def _build_menu(self) -> None:
        menu = QMenu()
        self._status_action = menu.addAction("Stopped")
        self._status_action.setEnabled(False)
        menu.addSeparator()

        # Interval submenu
        interval_menu = menu.addMenu("Interval")
        interval_group = QActionGroup(interval_menu)
        interval_group.setExclusive(True)
        for seconds in SLEEP_INTERVAL_CHOICES:
            action = QAction(f"{seconds}s", interval_menu)
            action.setCheckable(True)
            action.setChecked(seconds == self._interval)
            action.triggered.connect(lambda checked, s=seconds: self._set_interval(s))
            interval_group.addAction(action)
            interval_menu.addAction(action)

        menu.addSeparator()
        self._start_action = menu.addAction("Start")
        self._start_action.triggered.connect(self._start)
        self._stop_action = menu.addAction("Stop")
        self._stop_action.triggered.connect(self._stop)
        self._stop_action.setEnabled(False)
        menu.addSeparator()
        menu.addAction("Quit").triggered.connect(self._quit)
        self.setContextMenu(menu)

    def _set_interval(self, seconds: int) -> None:
        self._interval = seconds
        if self._worker and self._worker.isRunning():
            self._stop()
            self._start()

    def _apply_state(self, state: str) -> None:
        meta = STATE_META[state]
        self._status_action.setText(f"{meta['label']} ({self._interval}s)")
        self.setIcon(make_tray_icon(state))
        self.setToolTip(f"Caffeine: {meta['label']} ({self._interval}s)")
        active = state == "active"
        self._start_action.setEnabled(not active)
        self._stop_action.setEnabled(active)

    def _start(self) -> None:
        self._worker = CaffeineWorker(self._interval)
        self._worker.started_signal.connect(lambda: self._apply_state("active"))
        self._worker.started_signal.connect(
            lambda: self.showMessage(
                "Caffeine",
                f"Moving mouse every {self._interval}s",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
        )
        self._worker.stopped_signal.connect(lambda: self._apply_state("stopped"))
        self._worker.start()

    def _stop(self) -> None:
        if self._worker:
            self._worker.stop()
            self._worker.wait(3000)
        self._apply_state("stopped")

    def _quit(self) -> None:
        self._stop()
        QApplication.quit()


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        print("No system tray available.", file=sys.stderr)
        sys.exit(1)
    _tray = CaffeineTray()
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()

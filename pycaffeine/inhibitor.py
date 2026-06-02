import subprocess
import sys
from pycaffeine.constants import (
    APP_NAME,
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    INHIBIT_REASON,
)


class SleepInhibitor:
    """Prevents the OS from sleeping/locking. acquire()/release() never raise."""

    def __init__(self) -> None:
        self.active = False

    @staticmethod
    def acquire() -> bool:
        """Try to inhibit system sleep. Returns True when inhibition is active.

        Subclasses must set ``self.active = True`` when acquisition succeeds and
        leave it ``False`` otherwise. Implementations must never raise.
        """
        return False

    def release(self) -> None:
        """Release the inhibition. Safe to call multiple times or when not acquired."""
        self.active = False


class NullInhibitor(SleepInhibitor):
    """Fallback when no platform implementation is available."""


class DBusInhibitor(SleepInhibitor):
    """Linux: freedesktop ScreenSaver / GNOME SessionManager inhibition via QtDBus."""

    # (service, object path, interface, inhibit method, uninhibit method, gnome-style args)
    _SERVICES = (
        (
            "org.freedesktop.ScreenSaver",
            "/org/freedesktop/ScreenSaver",
            "org.freedesktop.ScreenSaver",
            "Inhibit",
            "UnInhibit",
            False,
        ),
        (
            "org.gnome.SessionManager",
            "/org/gnome/SessionManager",
            "org.gnome.SessionManager",
            "Inhibit",
            "Uninhibit",
            True,
        ),
    )
    _GNOME_INHIBIT_IDLE_FLAG = 8

    def __init__(self) -> None:
        super().__init__()
        self._iface = None
        self._uninhibit = ""
        self._cookie = 0

    def acquire(self) -> bool:
        if self.active:
            return True
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface

            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                print(f"{APP_NAME}: D-Bus session bus not available", file=sys.stderr)
                return False

            for service, path, interface, inhibit, uninhibit, gnome_style in self._SERVICES:
                iface = QDBusInterface(service, path, interface, bus)
                if not iface.isValid():
                    continue
                if gnome_style:
                    reply = iface.call(inhibit, APP_NAME, 0, INHIBIT_REASON, self._GNOME_INHIBIT_IDLE_FLAG)
                else:
                    reply = iface.call(inhibit, APP_NAME, INHIBIT_REASON)
                args = reply.arguments()
                if args and isinstance(args[0], int):
                    self._iface = iface
                    self._uninhibit = uninhibit
                    self._cookie = args[0]
                    self.active = True
                    return True
        except Exception as exc:
            print(f"{APP_NAME}: D-Bus inhibit failed: {exc!r}", file=sys.stderr)
        return False

    def release(self) -> None:
        if self.active and self._iface is not None:
            try:
                self._iface.call(self._uninhibit, self._cookie)
            except Exception as exc:
                print(f"{APP_NAME}: D-Bus uninhibit failed: {exc!r}", file=sys.stderr)
        self._iface = None
        self._cookie = 0
        self.active = False


class WindowsInhibitor(SleepInhibitor):
    """Windows: SetThreadExecutionState keep-awake flags."""

    def acquire(self) -> bool:
        if self.active:
            return True
        try:
            import ctypes

            result = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            self.active = result != 0
        except Exception as exc:
            print(f"{APP_NAME}: SetThreadExecutionState failed: {exc!r}", file=sys.stderr)
            self.active = False
        return self.active

    def release(self) -> None:
        if self.active:
            try:
                import ctypes

                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            except Exception as exc:
                print(f"{APP_NAME}: SetThreadExecutionState reset failed: {exc!r}", file=sys.stderr)
        self.active = False


class MacInhibitor(SleepInhibitor):
    """macOS: built-in `caffeinate` child process (-d display, -i idle)."""

    def __init__(self) -> None:
        super().__init__()
        self._proc: subprocess.Popen | None = None

    def acquire(self) -> bool:
        if self.active:
            return True
        try:
            self._proc = subprocess.Popen(["caffeinate", "-di"])  # noqa: S603, S607
            self.active = True
        except Exception as exc:
            print(f"{APP_NAME}: caffeinate failed: {exc!r}", file=sys.stderr)
            self._proc = None
            self.active = False
        return self.active

    def release(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception as exc:
                print(f"{APP_NAME}: caffeinate terminate failed: {exc!r}", file=sys.stderr)
        self._proc = None
        self.active = False


def create_inhibitor() -> SleepInhibitor:
    """Create the sleep inhibitor implementation for the current platform."""
    if sys.platform.startswith("linux"):
        return DBusInhibitor()
    if sys.platform == "win32":
        return WindowsInhibitor()
    if sys.platform == "darwin":
        return MacInhibitor()
    return NullInhibitor()

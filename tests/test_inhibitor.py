import pytest
import sys
from pycaffeine.inhibitor import (
    DBusInhibitor,
    MacInhibitor,
    NullInhibitor,
    SleepInhibitor,
    WindowsInhibitor,
    create_inhibitor,
)
from unittest.mock import MagicMock, patch


@pytest.fixture()
def mock_qtdbus(monkeypatch):
    """Mock PyQt6.QtDBus so tests run without a real D-Bus session."""
    qtdbus = MagicMock()
    monkeypatch.setitem(sys.modules, "PyQt6", MagicMock())
    monkeypatch.setitem(sys.modules, "PyQt6.QtDBus", qtdbus)
    return qtdbus


class TestSleepInhibitorBase:
    def test_active_starts_false(self):
        inhibitor = SleepInhibitor()
        assert inhibitor.active is False

    def test_acquire_returns_false(self):
        inhibitor = SleepInhibitor()
        assert inhibitor.acquire() is False

    def test_release_resets_active(self):
        inhibitor = SleepInhibitor()
        inhibitor.active = True
        inhibitor.release()
        assert inhibitor.active is False

    def test_release_is_idempotent(self):
        inhibitor = SleepInhibitor()
        inhibitor.release()
        inhibitor.release()
        assert inhibitor.active is False


class TestNullInhibitor:
    def test_acquire_returns_false(self):
        inhibitor = NullInhibitor()
        assert inhibitor.acquire() is False
        assert inhibitor.active is False

    def test_release_is_noop(self):
        inhibitor = NullInhibitor()
        inhibitor.release()
        assert inhibitor.active is False


def _make_bus_and_iface(mock_qtdbus, cookie=42, valid=True, connected=True):
    """Helper: wire QDBusConnection/QDBusInterface mocks for one interface."""
    bus = MagicMock()
    bus.isConnected.return_value = connected
    mock_qtdbus.QDBusConnection.sessionBus.return_value = bus

    iface = MagicMock()
    iface.isValid.return_value = valid
    reply = MagicMock()
    reply.arguments.return_value = [cookie]
    iface.call.return_value = reply
    mock_qtdbus.QDBusInterface.return_value = iface
    return bus, iface


class TestDBusInhibitor:
    def test_acquire_via_screensaver(self, mock_qtdbus):
        _, iface = _make_bus_and_iface(mock_qtdbus, cookie=42)
        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is True
        assert inhibitor.active is True
        iface.call.assert_called_once_with("Inhibit", "pycaffeine", "Keeping system awake")

    def test_release_calls_uninhibit_with_cookie(self, mock_qtdbus):
        _, iface = _make_bus_and_iface(mock_qtdbus, cookie=42)
        inhibitor = DBusInhibitor()
        inhibitor.acquire()
        inhibitor.release()
        iface.call.assert_called_with("UnInhibit", 42)
        assert inhibitor.active is False

    def test_acquire_returns_false_without_session_bus(self, mock_qtdbus):
        _make_bus_and_iface(mock_qtdbus, connected=False)
        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is False
        assert inhibitor.active is False

    def test_acquire_falls_back_to_gnome(self, mock_qtdbus):
        bus = MagicMock()
        bus.isConnected.return_value = True
        mock_qtdbus.QDBusConnection.sessionBus.return_value = bus

        bad_iface = MagicMock()
        bad_iface.isValid.return_value = False
        good_iface = MagicMock()
        good_iface.isValid.return_value = True
        reply = MagicMock()
        reply.arguments.return_value = [99]
        good_iface.call.return_value = reply
        mock_qtdbus.QDBusInterface.side_effect = [bad_iface, good_iface]

        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is True
        # GNOME signature: Inhibit(app_id, toplevel_xid, reason, flags) with flags=8
        good_iface.call.assert_called_once_with("Inhibit", "pycaffeine", 0, "Keeping system awake", 8)
        inhibitor.release()
        good_iface.call.assert_called_with("Uninhibit", 99)

    def test_acquire_returns_false_when_no_interface_valid(self, mock_qtdbus):
        bus = MagicMock()
        bus.isConnected.return_value = True
        mock_qtdbus.QDBusConnection.sessionBus.return_value = bus
        bad_iface = MagicMock()
        bad_iface.isValid.return_value = False
        mock_qtdbus.QDBusInterface.return_value = bad_iface

        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is False

    def test_acquire_returns_false_on_non_integer_cookie(self, mock_qtdbus):
        _make_bus_and_iface(mock_qtdbus, cookie="not-a-cookie")
        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is False

    def test_acquire_handles_exception(self, mock_qtdbus):
        mock_qtdbus.QDBusConnection.sessionBus.side_effect = RuntimeError("boom")
        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is False
        assert inhibitor.active is False

    def test_release_without_acquire_is_noop(self, mock_qtdbus):
        inhibitor = DBusInhibitor()
        inhibitor.release()  # must not raise
        assert inhibitor.active is False

    def test_release_swallows_exception(self, mock_qtdbus):
        _, iface = _make_bus_and_iface(mock_qtdbus, cookie=42)
        inhibitor = DBusInhibitor()
        inhibitor.acquire()
        iface.call.side_effect = RuntimeError("dbus gone")
        inhibitor.release()  # must not raise
        assert inhibitor.active is False

    def test_double_acquire_is_idempotent(self, mock_qtdbus):
        _, iface = _make_bus_and_iface(mock_qtdbus, cookie=42)
        inhibitor = DBusInhibitor()
        assert inhibitor.acquire() is True
        assert inhibitor.acquire() is True
        # only one Inhibit call despite two acquires
        iface.call.assert_called_once_with("Inhibit", "pycaffeine", "Keeping system awake")


class TestWindowsInhibitor:
    def _patch_kernel32(self, return_value=0x80000000):
        kernel32 = MagicMock()
        kernel32.SetThreadExecutionState.return_value = return_value
        windll = MagicMock()
        windll.kernel32 = kernel32
        return patch("ctypes.windll", windll, create=True), kernel32

    def test_acquire_sets_execution_state(self):
        from pycaffeine.constants import ES_CONTINUOUS, ES_DISPLAY_REQUIRED, ES_SYSTEM_REQUIRED

        patcher, kernel32 = self._patch_kernel32()
        with patcher:
            inhibitor = WindowsInhibitor()
            assert inhibitor.acquire() is True
            assert inhibitor.active is True
        kernel32.SetThreadExecutionState.assert_called_once_with(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )

    def test_acquire_treats_zero_as_failure(self):
        patcher, _ = self._patch_kernel32(return_value=0)
        with patcher:
            inhibitor = WindowsInhibitor()
            assert inhibitor.acquire() is False
            assert inhibitor.active is False

    def test_release_resets_execution_state(self):
        from pycaffeine.constants import ES_CONTINUOUS

        patcher, kernel32 = self._patch_kernel32()
        with patcher:
            inhibitor = WindowsInhibitor()
            inhibitor.acquire()
            inhibitor.release()
        kernel32.SetThreadExecutionState.assert_called_with(ES_CONTINUOUS)
        assert inhibitor.active is False

    def test_release_without_acquire_skips_api_call(self):
        patcher, kernel32 = self._patch_kernel32()
        with patcher:
            inhibitor = WindowsInhibitor()
            inhibitor.release()
        kernel32.SetThreadExecutionState.assert_not_called()

    def test_acquire_handles_missing_windll(self):
        # On Linux ctypes has no windll attribute at all -> AttributeError -> False
        inhibitor = WindowsInhibitor()
        assert inhibitor.acquire() is False

    def test_release_swallows_exception(self):
        patcher, kernel32 = self._patch_kernel32()
        with patcher:
            inhibitor = WindowsInhibitor()
            inhibitor.acquire()
            kernel32.SetThreadExecutionState.side_effect = OSError("boom")
            inhibitor.release()  # must not raise
        assert inhibitor.active is False

    def test_double_acquire_is_idempotent(self):
        patcher, kernel32 = self._patch_kernel32()
        with patcher:
            inhibitor = WindowsInhibitor()
            assert inhibitor.acquire() is True
            assert inhibitor.acquire() is True
        kernel32.SetThreadExecutionState.assert_called_once()


class TestMacInhibitor:
    @patch("pycaffeine.inhibitor.subprocess.Popen")
    def test_acquire_spawns_caffeinate(self, mock_popen):
        inhibitor = MacInhibitor()
        assert inhibitor.acquire() is True
        assert inhibitor.active is True
        mock_popen.assert_called_once_with(["caffeinate", "-di"])

    @patch("pycaffeine.inhibitor.subprocess.Popen")
    def test_release_terminates_process(self, mock_popen):
        proc = MagicMock()
        mock_popen.return_value = proc
        inhibitor = MacInhibitor()
        inhibitor.acquire()
        inhibitor.release()
        proc.terminate.assert_called_once()
        assert inhibitor.active is False

    @patch("pycaffeine.inhibitor.subprocess.Popen", side_effect=FileNotFoundError("caffeinate"))
    def test_acquire_handles_missing_caffeinate(self, mock_popen):
        inhibitor = MacInhibitor()
        assert inhibitor.acquire() is False
        assert inhibitor.active is False

    def test_release_without_acquire_is_noop(self):
        inhibitor = MacInhibitor()
        inhibitor.release()  # must not raise
        assert inhibitor.active is False

    @patch("pycaffeine.inhibitor.subprocess.Popen")
    def test_release_swallows_terminate_exception(self, mock_popen):
        proc = MagicMock()
        proc.terminate.side_effect = OSError("already dead")
        mock_popen.return_value = proc
        inhibitor = MacInhibitor()
        inhibitor.acquire()
        inhibitor.release()  # must not raise
        assert inhibitor.active is False

    @patch("pycaffeine.inhibitor.subprocess.Popen")
    def test_double_acquire_is_idempotent(self, mock_popen):
        inhibitor = MacInhibitor()
        assert inhibitor.acquire() is True
        assert inhibitor.acquire() is True
        mock_popen.assert_called_once()

    @patch("pycaffeine.inhibitor.subprocess.Popen")
    def test_release_waits_for_process(self, mock_popen):
        proc = MagicMock()
        mock_popen.return_value = proc
        inhibitor = MacInhibitor()
        inhibitor.acquire()
        inhibitor.release()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once_with(timeout=3)


class TestFactory:
    def test_linux_returns_dbus(self):
        with patch.object(sys, "platform", "linux"):
            assert isinstance(create_inhibitor(), DBusInhibitor)

    def test_windows_returns_windows(self):
        with patch.object(sys, "platform", "win32"):
            assert isinstance(create_inhibitor(), WindowsInhibitor)

    def test_darwin_returns_mac(self):
        with patch.object(sys, "platform", "darwin"):
            assert isinstance(create_inhibitor(), MacInhibitor)

    def test_unknown_returns_null(self):
        with patch.object(sys, "platform", "freebsd14"):
            assert isinstance(create_inhibitor(), NullInhibitor)

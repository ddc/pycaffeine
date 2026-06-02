import pytest
import sys
from unittest.mock import MagicMock, patch


def _import_main():
    """Import __main__ after Qt mocks are in place."""
    from pycaffeine.__main__ import CaffeineTray, CaffeineWorker, main, make_tray_icon

    return CaffeineWorker, CaffeineTray, make_tray_icon, main


@pytest.fixture(autouse=True)
def _setup_qt(mock_qt):
    """Auto-use the shared Qt mock fixture."""


class TestMakeTrayIcon:
    def test_returns_icon(self):
        _, _, make_tray_icon, _ = _import_main()
        icon = make_tray_icon()
        assert icon is not None

    def test_active_and_stopped_use_different_icons(self, mock_qt):
        _, _, make_tray_icon, _ = _import_main()
        import sys as _sys

        mock_qicon = _sys.modules["PyQt6.QtGui"].QIcon
        mock_qicon.reset_mock()
        make_tray_icon("active")
        active_path = mock_qicon.call_args[0][0]
        make_tray_icon("stopped")
        stopped_path = mock_qicon.call_args[0][0]
        assert active_path != stopped_path
        assert active_path.endswith("pycaffeine-icon.svg")
        assert stopped_path.endswith("pycaffeine-icon-off.svg")

    def test_icon_files_exist(self):
        from pathlib import Path
        from pycaffeine.constants import STATE_META

        assets = Path(__file__).resolve().parent.parent / "assets"
        for meta in STATE_META.values():
            assert (assets / meta["icon"]).is_file()


class TestCaffeineWorker:
    def test_init_defaults(self):
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(30)
        assert worker.interval == 30
        assert worker._running is False

    def test_stop_sets_running_false(self):
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(5)
        worker._running = True
        worker.stop()
        assert worker._running is False

    @patch.dict("sys.modules", {"pyautogui": MagicMock()})
    def test_run_moves_mouse_and_stops(self):
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(1)
        worker.started_signal = MagicMock()
        worker.stopped_signal = MagicMock()

        mock_pyautogui = sys.modules["pyautogui"]
        call_count = 0

        def move_side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                worker._running = False

        mock_pyautogui.move.side_effect = move_side_effect
        worker.run()

        worker.started_signal.emit.assert_called_once()
        worker.stopped_signal.emit.assert_called_once()
        mock_pyautogui.move.assert_called()

    @patch.dict("sys.modules", {"pyautogui": MagicMock()})
    def test_run_breaks_after_sleep_when_stopped(self):
        """Cover the `break` on line 36 — stopped during first sleep."""
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(1)
        worker.started_signal = MagicMock()
        worker.stopped_signal = MagicMock()

        mock_pyautogui = sys.modules["pyautogui"]
        # Stop after first move + sleep, before second move
        mock_pyautogui.move.side_effect = lambda *a: worker.stop()
        worker.run()

        # Only one move call — the break prevented the second
        mock_pyautogui.move.assert_called_once()
        worker.stopped_signal.emit.assert_called_once()

    def test_sleep_exits_early_when_stopped(self):
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(10)
        worker._running = False
        worker._sleep(10)

    @patch.dict("sys.modules", {"pyautogui": None})
    def test_run_survives_pyautogui_import_failure(self):
        """A broken pyautogui import must not propagate out of run() —
        it would tear down Qt from the worker thread (QtDBus/GLib errors)."""
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(1)
        worker.started_signal = MagicMock()
        worker.stopped_signal = MagicMock()

        worker.run()  # must not raise

        worker.started_signal.emit.assert_not_called()
        worker.stopped_signal.emit.assert_called_once()
        assert worker._running is False

    @patch.dict("sys.modules", {"pyautogui": MagicMock()})
    def test_run_blocks_mouseinfo_import(self):
        """mouseinfo calls sys.exit() at import time when tkinter is broken —
        run() must block it so pyautogui can never raise SystemExit."""
        CaffeineWorker, _, _, _ = _import_main()
        worker = CaffeineWorker(1)
        worker.started_signal = MagicMock()
        worker.stopped_signal = MagicMock()
        sys.modules["pyautogui"].move.side_effect = lambda *a: worker.stop()

        with patch.dict("sys.modules"):
            sys.modules.pop("mouseinfo", None)
            worker.run()
            assert sys.modules["mouseinfo"] is None


class TestCaffeineTray:
    def test_init_sets_default_interval(self):
        _, CaffeineTray, _, _ = _import_main()
        from pycaffeine.constants import DEFAULT_SLEEP_INTERVAL

        tray = CaffeineTray()
        assert tray._interval == DEFAULT_SLEEP_INTERVAL

    def test_set_interval_changes_value(self):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        tray._set_interval(60)
        assert tray._interval == 60

    def test_set_interval_restarts_if_running(self):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        tray._worker = mock_worker
        tray._set_interval(15)
        assert tray._interval == 15
        mock_worker.stop.assert_called_once()

    def test_stop_without_worker(self):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        tray._worker = None
        tray._stop()

    def test_quit_calls_quit(self, mock_qt):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        tray._worker = None
        mock_qt.QApplication.quit.reset_mock()
        tray._quit()
        mock_qt.QApplication.quit.assert_called_once()

    def test_apply_state_active(self):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        tray._status_action = MagicMock()
        tray._start_action = MagicMock()
        tray._stop_action = MagicMock()
        tray._apply_state("active")
        tray._start_action.setEnabled.assert_called_with(False)
        tray._stop_action.setEnabled.assert_called_with(True)

    def test_apply_state_stopped(self):
        _, CaffeineTray, _, _ = _import_main()
        tray = CaffeineTray()
        tray._status_action = MagicMock()
        tray._start_action = MagicMock()
        tray._stop_action = MagicMock()
        tray._apply_state("stopped")
        tray._start_action.setEnabled.assert_called_with(True)
        tray._stop_action.setEnabled.assert_called_with(False)


class TestMain:
    def test_main_exits_when_no_tray(self):
        _, _, _, main = _import_main()
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_happy_path(self, mock_qt):
        _, _, _, main = _import_main()
        mock_qt.QSystemTrayIcon.isSystemTrayAvailable = staticmethod(lambda: True)
        mock_app = MagicMock()
        mock_app.exec.return_value = 0
        mock_qt.QApplication.return_value = mock_app
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
        mock_app.setQuitOnLastWindowClosed.assert_called_with(False)
        mock_app.exec.assert_called_once()


class TestInhibitorIntegration:
    def _make_tray(self, CaffeineTray, acquire_succeeds=True):
        """Build a tray whose inhibitor is a stateful MagicMock."""
        import pycaffeine.__main__ as main_mod

        inhibitor = MagicMock()
        inhibitor.active = False

        def fake_acquire():
            inhibitor.active = acquire_succeeds
            return acquire_succeeds

        def fake_release():
            inhibitor.active = False

        inhibitor.acquire.side_effect = fake_acquire
        inhibitor.release.side_effect = fake_release
        with patch.object(main_mod, "create_inhibitor", return_value=inhibitor):
            tray = CaffeineTray()
        return tray, inhibitor

    def test_init_acquires_inhibitor_via_autostart(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        inhibitor.acquire.assert_called_once()
        assert inhibitor.active is True

    def test_stop_releases_inhibitor(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        tray._stop()
        inhibitor.release.assert_called_once()
        assert inhibitor.active is False

    def test_quit_releases_inhibitor(self, mock_qt):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        tray._worker = None
        tray._quit()
        inhibitor.release.assert_called_once()

    def test_worker_death_keeps_active_while_inhibited(self):
        """Worker dies on its own while the inhibitor holds -> stays active."""
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        tray._status_action = MagicMock()
        tray._start_action = MagicMock()
        tray._stop_action = MagicMock()
        tray._on_worker_stopped()
        # still active: stop stays enabled
        tray._stop_action.setEnabled.assert_called_with(True)

    def test_worker_death_goes_stopped_when_not_inhibited(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray, acquire_succeeds=False)
        tray._status_action = MagicMock()
        tray._start_action = MagicMock()
        tray._stop_action = MagicMock()
        tray._on_worker_stopped()
        tray._stop_action.setEnabled.assert_called_with(False)

    def test_mechanisms_label_inhibit_only(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        # conftest QThread mock: isRunning() is always False -> mouse not counted
        assert tray._mechanisms_label() == "sleep-inhibit"

    def test_mechanisms_label_both(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)
        running_worker = MagicMock()
        running_worker.isRunning.return_value = True
        tray._worker = running_worker
        assert tray._mechanisms_label() == "sleep-inhibit + mouse"

    def test_mechanisms_label_mouse_only(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray, acquire_succeeds=False)
        running_worker = MagicMock()
        running_worker.isRunning.return_value = True
        tray._worker = running_worker
        assert tray._mechanisms_label() == "mouse"

    def test_mechanisms_label_none(self):
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray, acquire_succeeds=False)
        assert tray._mechanisms_label() == "none"

    def test_stop_releases_inhibitor_before_stopping_worker(self):
        """The release-before-stop ordering lets _on_worker_stopped distinguish
        user-initiated stops from the worker dying on its own."""
        _, CaffeineTray, _, _ = _import_main()
        tray, inhibitor = self._make_tray(CaffeineTray)

        call_order = []
        inhibitor.release.side_effect = lambda: call_order.append("release")
        mock_worker = MagicMock()
        mock_worker.stop.side_effect = lambda: call_order.append("worker_stop")
        tray._worker = mock_worker

        tray._stop()

        assert call_order == ["release", "worker_stop"]

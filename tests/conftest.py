import pytest
import sys
from unittest.mock import MagicMock

# Mock Qt classes that need to be real-enough for subclassing
_mock_qt_core = MagicMock()
_mock_qt_gui = MagicMock()
_mock_qt_widgets = MagicMock()

_mock_qt_core.QThread = type(
    "QThread",
    (),
    {
        "__init__": lambda self, *a, **kw: None,
        "isRunning": lambda self: False,
        "start": lambda self: None,
        "wait": lambda self, *a: None,
    },
)
_mock_qt_core.pyqtSignal = MagicMock(return_value=MagicMock())

_mock_qt_widgets.QSystemTrayIcon = type(
    "QSystemTrayIcon",
    (),
    {
        "__init__": lambda self, *a, **kw: None,
        "show": lambda self: None,
        "setIcon": lambda self, *a: None,
        "setToolTip": lambda self, *a: None,
        "setContextMenu": lambda self, *a: None,
        "showMessage": lambda self, *a, **kw: None,
        "MessageIcon": MagicMock(),
        "isSystemTrayAvailable": staticmethod(lambda: False),
    },
)
_mock_qt_widgets.QMenu = MagicMock
_mock_qt_widgets.QApplication = MagicMock()
_mock_qt_widgets.QApplication.quit = MagicMock()


@pytest.fixture()
def mock_qt(monkeypatch):
    """Mock all PyQt6 modules so tests run without a display."""
    monkeypatch.setitem(sys.modules, "PyQt6", MagicMock())
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", _mock_qt_core)
    monkeypatch.setitem(sys.modules, "PyQt6.QtGui", _mock_qt_gui)
    monkeypatch.setitem(sys.modules, "PyQt6.QtWidgets", _mock_qt_widgets)
    monkeypatch.setitem(sys.modules, "PyQt6.QtDBus", MagicMock())
    if "pycaffeine.__main__" in sys.modules:
        del sys.modules["pycaffeine.__main__"]
    return _mock_qt_widgets

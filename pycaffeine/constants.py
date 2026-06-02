from typing import Final

DEFAULT_SLEEP_INTERVAL: Final = 30
SLEEP_INTERVAL_CHOICES: Final = (5, 15, 30, 45, 60)
MOVE_PIXELS: Final = 1

STATE_META: Final[dict[str, dict[str, str]]] = {
    "active": {"color": "#27ae60", "label": "Active", "icon": "pycaffeine-icon.svg"},
    "stopped": {"color": "#95a5a6", "label": "Stopped", "icon": "pycaffeine-icon-off.svg"},
}

APP_NAME: Final = "pycaffeine"
INHIBIT_REASON: Final = "Keeping system awake"

# Windows SetThreadExecutionState flags
# https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_CONTINUOUS: Final = 0x80000000
ES_SYSTEM_REQUIRED: Final = 0x00000001
ES_DISPLAY_REQUIRED: Final = 0x00000002

from typing import Final

DEFAULT_SLEEP_INTERVAL: Final = 30
SLEEP_INTERVAL_CHOICES: Final = (5, 15, 30, 45, 60)
MOVE_PIXELS: Final = 1

STATE_META: Final[dict[str, dict[str, str]]] = {
    "active": {"color": "#27ae60", "label": "Active", "icon": "pycaffeine-icon.svg"},
    "stopped": {"color": "#95a5a6", "label": "Stopped", "icon": "pycaffeine-icon-off.svg"},
}

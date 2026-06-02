from pycaffeine import __version__
from pycaffeine.constants import DEFAULT_SLEEP_INTERVAL, MOVE_PIXELS, SLEEP_INTERVAL_CHOICES


class TestConstants:
    def test_default_sleep_interval(self):
        assert DEFAULT_SLEEP_INTERVAL == 30

    def test_sleep_interval_choices(self):
        assert SLEEP_INTERVAL_CHOICES == (5, 15, 30, 45, 60)

    def test_default_in_choices(self):
        assert DEFAULT_SLEEP_INTERVAL in SLEEP_INTERVAL_CHOICES

    def test_move_pixels(self):
        assert MOVE_PIXELS == 1


class TestVersion:
    def test_version_exists(self):
        assert __version__
        assert isinstance(__version__, str)

    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) >= 2
        for part in parts:
            assert part.isdigit()

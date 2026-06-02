from importlib.metadata import PackageNotFoundError, version

try:
    __version__: str = version("pycaffeine")
except PackageNotFoundError:
    __version__: str = "0.0.0"

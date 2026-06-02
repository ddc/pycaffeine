import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT / "spec" / "pycaffeine.spec"
VERSION_RC = ROOT / "spec" / "version.rc"
PYPROJECT = ROOT / "pyproject.toml"
BUILD_DIR = ROOT / "dist" / "build"


def get_version() -> str:
    """Read version from pyproject.toml."""
    text = PYPROJECT.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        print("ERROR: Could not find version in pyproject.toml")
        sys.exit(1)
    return match.group(1)


def update_version_rc(version: str) -> None:
    """Rewrite version.rc with the current version from pyproject.toml."""
    if not VERSION_RC.exists():
        return

    v_parts = [int(x) for x in version.split(".")]
    v_parts += [0] * (4 - len(v_parts))
    v_tuple = str(tuple(v_parts))

    rc = VERSION_RC.read_text()
    rc = re.sub(r"filevers=\([^)]+\)", f"filevers={v_tuple}", rc)
    rc = re.sub(r"prodvers=\([^)]+\)", f"prodvers={v_tuple}", rc)
    rc = re.sub(r"(u'FileVersion',\s*u')[^']*(')", rf"\g<1>{version}\2", rc)
    rc = re.sub(r"(u'ProductVersion',\s*u')[^']*(')", rf"\g<1>{version}\2", rc)
    VERSION_RC.write_text(rc)
    print(f"Updated version.rc to {version}")


def run_pyinstaller() -> None:
    """Run PyInstaller with the spec file."""
    cmd = [
        "pyinstaller",
        "-y",
        "--clean",
        "--log-level",
        "INFO",
        "--workpath",
        str(BUILD_DIR),
        "--distpath",
        str(ROOT / "dist"),
        str(SPEC_FILE),
    ]
    result = subprocess.call(cmd)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print("Cleaned up build directory")
    sys.exit(result)


if __name__ == "__main__":
    version = get_version()
    update_version_rc(version)
    run_pyinstaller()

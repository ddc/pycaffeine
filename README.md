<h1 align="center">
  <img src="https://raw.githubusercontent.com/ddc/pycaffeine/refs/heads/main/assets/pycaffeine-icon.svg" alt="pycaffeine" width="150">
  <br>
  pycaffeine
</h1>

<p align="center">
    <a href="https://github.com/sponsors/ddc"><img src="https://img.shields.io/static/v1?style=plastic&label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=ff69b4" alt="Sponsor"/></a>
    <br>
    <a href="https://ko-fi.com/ddc"><img src="https://img.shields.io/badge/Ko--fi-ddc-FF5E5B?style=plastic&logo=kofi&logoColor=white&color=brightgreen" alt="Ko-fi"/></a>
    <a href="https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ"><img src="https://img.shields.io/badge/Donate-PayPal-brightgreen.svg?style=plastic&logo=paypal&logoColor=white" alt="Donate"/></a>
    <br>
    <a href="https://www.python.org/downloads"><img src="https://img.shields.io/badge/python-3.14-blue.svg?style=plastic&logo=python&logoColor=3776AB" alt="Python"/></a>
    <a href="https://pypi.org/project/PyQt6"><img src="https://img.shields.io/badge/PyQt-6-blue.svg?style=plastic&logo=qt&logoColor=green&logoSize=auto" alt="PyQt6"/></a>
    <a href="https://github.com/astral-sh/uv"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=plastic" alt="uv"/></a>
    <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=plastic" alt="Ruff"/></a>
    <br>
    <a href="https://pypi.python.org/pypi/pycaffeine"><img src="https://img.shields.io/pypi/v/pycaffeine.svg?style=plastic&logo=python&cacheSeconds=3600" alt="PyPi"/></a>
    <a href="https://pepy.tech/projects/pycaffeine"><img src="https://img.shields.io/pepy/dt/pycaffeine?style=plastic&logo=pypi&logoColor=3776AB" alt="PyPI Downloads"/></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=plastic&logo=creativecommons&logoColor=white" alt="License: MIT"/></a>
    <br>
    <a href="https://github.com/ddc/pycaffeine/issues"><img src="https://img.shields.io/github/issues/ddc/pycaffeine?style=plastic&logo=github&logoColor=white" alt="issues"/></a>
    <a href="https://sonarcloud.io/component_measures?id=ddc_pycaffeine&metric=coverage"><img src="https://img.shields.io/sonar/coverage/ddc_pycaffeine?server=https%3A%2F%2Fsonarcloud.io&style=plastic&logo=sonarqubecloud&logoColor=white" alt="SonarCloud Coverage"/></a>
    <a href="https://sonarcloud.io/dashboard?id=ddc_pycaffeine"><img src="https://img.shields.io/sonar/quality_gate/ddc_pycaffeine?server=https%3A%2F%2Fsonarcloud.io&style=plastic&logo=sonarqubecloud&logoColor=white" alt="Quality Gate Status"/></a>
    <a href="https://github.com/ddc/pycaffeine/actions/workflows/workflow.yml"><img src="https://img.shields.io/github/actions/workflow/status/ddc/pycaffeine/workflow.yml?style=plastic&logo=github&logoColor=white&label=CI%2FCD%20Pipeline" alt="CI/CD Pipeline"/></a>
    <a href="https://actions-badge.atrox.dev/ddc/pycaffeine/goto?ref=main"><img src="https://img.shields.io/endpoint.svg?url=https%3A//actions-badge.atrox.dev/ddc/pycaffeine/badge?ref=main&label=build&logo=github&style=plastic" alt="Build Status"/></a>
</p>

<p align="center">Keep computer awake by moving the cursor by 1 pixel back and forth every few seconds</p>


## Table of Contents
- [Features](#features)
- [Usage](#usage)
- [Desktop Environment Notes (Linux)](#desktop-environment-notes-linux)
- [Development and Testing](#development-and-testing)
  - [Setup](#setup)
  - [Running Unit Tests](#running-unit-tests)
  - [Build](#build)
  - [Other Tasks](#other-tasks)
- [License](#license)
- [Support](#support)


## Features

- System tray application with start/stop controls
- Native sleep/screensaver inhibition (D-Bus on Linux, SetThreadExecutionState on Windows, caffeinate on macOS)
- Mouse simulation to also appear "Active" in chat apps (Teams/Slack)
- Configurable interval (5s, 15s, 30s, 45s, 60s) from the tray menu
- Cross-platform (Linux, Windows, macOS)
- Standalone executable via PyInstaller


## Usage

```shell
# Run from source
uv run python -m pycaffeine
```

Or download the latest standalone executable from [Releases](https://github.com/ddc/pycaffeine/releases/latest).

The app runs in the system tray. Right-click the tray icon to start, stop, change the interval, or quit.


## Desktop Environment Notes (Linux)

| Environment                            | Tray icon                      | Sleep inhibit | Mouse simulation                 |
|----------------------------------------|--------------------------------|---------------|----------------------------------|
| KDE / XFCE / Cinnamon (X11 or Wayland) | ✓                              | ✓             | ✓ (Wayland needs XWayland 23.2+) |
| Ubuntu GNOME                           | ✓                              | ✓             | ✓                                |
| Vanilla GNOME (e.g. Fedora)            | needs AppIndicator extension ¹ | ✓             | ✓                                |

- ¹ **GNOME tray icon:** GNOME removed legacy tray support; install the [AppIndicator extension](https://extensions.gnome.org/extension/615/appindicator-support/) / `gnome-shell-extension-appindicator` package (preinstalled on Ubuntu).
- **Mouse simulation on Wayland:** requires XWayland 23.2+ with libei support (Plasma 6, GNOME 45+). Sleep inhibition works regardless.


# Development and Testing

Requires [UV](https://docs.astral.sh/uv/getting-started/installation/) to be installed.

## Setup
```shell
uv lock --upgrade && uv sync --all-extras --all-groups
```

## Running Unit Tests
```shell
poe test
```

## Build
Build a standalone executable with [PyInstaller](https://pyinstaller.org):
```shell
poe build
```
The executable will be generated in the `./dist` directory.

## Other Tasks
```shell
poe linter

poe updatedev
```


# License
Released under the [MIT License](LICENSE)


# Support
If you find this project helpful, consider supporting development.

<a href='https://github.com/sponsors/ddc' target='_blank'><img height='24' style='border:0px;height:24px;' src='https://img.shields.io/badge/Sponsor-❤-ea4aaa?style=plastic&logo=github&logoColor=white' border='0' alt='Sponsor on GitHub' /></a>
<a href='https://ko-fi.com/ddc' target='_blank'><img height='30' style='border:0px;height:30px;' src='https://storage.ko-fi.com/cdn/kofi2.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
<a href='https://www.paypal.com/ncp/payment/6G9Z78QHUD4RJ' target='_blank'><img height='30' style='border:0px;height:30px;' src='https://www.paypalobjects.com/digitalassets/c/website/marketing/apac/C2/logos-buttons/optimize/44_Yellow_PayPal_Pill_Button.png' border='0' alt='Donate via PayPal' /></a>

# hatch-msgfmt

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-msgfmt.svg)](https://pypi.org/project/hatch-msgfmt)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-msgfmt.svg)](https://pypi.org/project/hatch-msgfmt)

-----

# Automatically compile po files to mo ones at build time using msgfmt.py

## Table of Contents

- [Goal](#goal)
- [Status](#current-status)
- [Installation](#installation)
- [License](#license)

## Goal
This package is a [hatchling]() plugin that helps to automatically compile
translation sources at build time.
It internally uses a patched version of
the `msgfmt.py` script from the Tools folder of a standard CPython
installation.

## Current Status

This is currently only a work in progress.

## Installation

```console
pip install hatch-msgfmt
```

## License

`hatch-msgfmt` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

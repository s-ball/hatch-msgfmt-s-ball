# hatch-msgfmt-s-ball

[![PyPI - Version](https://img.shields.io/pypi/v/hatch-msgfmt-s-ball.svg)](https://pypi.org/project/hatch-msgfmt-s-ball)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/hatch-msgfmt-s-ball.svg)](https://pypi.org/project/hatch-msgfmt-s-ball)

-----

# Automatically compile po files to mo ones at build time using msgfmt.py

## Table of Contents

<!-- TOC 
* [hatch-msgfmt-s-ball](#hatch-msgfmt-s-ball)
* [Automatically compile po files to mo ones at build time using msgfmt.py](#automatically-compile-po-files-to-mo-ones-at-build-time-using-msgfmtpy)
  * [Table of Contents](#table-of-contents)
-->
  * [Goal](#goal)
  * [Current Status](#current-status)
  * [Usage](#usage)
    * [`.po` files](#po-files)
      * [`LANG` folders organization](#lang-folders-organization)
    * [`.mo` files](#mo-files)
    * [Configuration](#configuration)
  * [Installation](#installation)
    * [Developer installation](#developer-installation)
  * [Contributing](#contributing)
  * [License](#license)
<!-- TOC -->

## Goal
This package is a [hatchling]() plugin that helps to automatically compile
translation sources at build time.
It internally uses a patched version of
the `msgfmt.py` script from the Tools folder of the CPython
source. Because of that it has no dependency and does not require any external
tools.

## Current Status

This is currently only a work in progress. The rest of this document may not
be accurate until a first usable version is published on PyPI.

Releases use a semantic major.minor.patch versioning. The full source code
is available on [GitHub](https://github.com/s-ball/hatch-msgfmt-s-ball.git).

## Usage

As it is only a `hatchling` hook plugin, this package has no direct interface.
It uses the `logging` package for its messages which are written to the
standard output stream, so it is possible to increase its verbosity when
the behaviour is unexpected.

### `.po` files

The source `.po` are expected to be in a folder under the root source
directory. The default directory is `messages` but it can be changed through 
the configuration file. It can even be `.` if the files are
*directly* in the root directory.

They are expected to be named `LANG.po` or `domain-LANG.po`. When no domain
is present in the file name, the default domain is the last component of the
source folder, or the package name if the source folder is `.` or `messages`.

#### `LANG` folders organization

Alternatively the source directory can contain `LANG` folders (e.g. *fr*
or *es*) that in turn contain `domain.po` files, possibly under a hierarchy
of subfolders. The goal is to mimic a classical `locale` hierarchy:
`LANG/LC_MESSAGES/domain.po`

It is even possible (but not recommended) to mix both organizations.

### `.mo` files

For every `.po` file found, a corresponding compiled file is generated as
`locale/LANG/LC_MESSAGES/domain.mo` under the build directory. The default
`locale` name can be changed through the builder configuration.

### Configuration

The `hatch-msgfmt-s-ball` plugin can be configured as any other plugin through
the `pyproject.toml` file. You must first declare it with:

```toml
[build-system]
requires = ["hatchling", "hatch-msgfmt-s-ball"]
build-backend = "hatchling.build"
```

Then you have to tell the builder that it must be called for the `wheel`
target:

```toml
[tool.hatch.build.targets.wheel.hooks.msgfmt]
```

That section can be left empty if you accept the defaults. It is equivalent
to:

```toml
[tool.hatch.build.targets.wheel.hooks.msgfmt]
locale = "locale"
messages = "messages"
logging.level = "WARNING"
logging.format = "%(name)s - %(levelname)s - %(message)s"
```

## Installation

For normal usage, no installation is required. Any Python installer using
the `pyproject.toml` file will be able to automatically download and install
it at build time.

### Developer installation

If you want to use the source of `hatch-msgfmt-s-ball`, you can download a source
package form PyPI, or better clone it from GitHub:

```commandline
git clone https://github.com/s-ball/hatch-msgfmt-s-ball.git
```

You will benefit from `git` for you own changes.

## Contributing

As I am the only developer, I cannot guarantee very 
fast feedbacks. Anyway, I shall be glad to receive issues or pull requests
on GitHUB.

## License

`hatch-msgfmt-s-ball` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

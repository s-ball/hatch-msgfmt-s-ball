#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
"""
This module contains the implementation of a hatchling hook plugin.

This plugin allows to compile gettext .po files to .mo ones when building
a wheel and to install them under an appropriate (but local) directory.
"""
# required for 3.8 support
# TODO: can be removed as soon as 3.8 support will be dropped
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Generator

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

from .vendor.msgfmt import make


class MsgFmtBuildHook(BuildHookInterface):
    """The implementation of the hook interface"""

    PLUGIN_NAME = "msgfmt"  # required by the interface
    locale: Path  # local folder for the gettext localedir folder
    src: Path  # local folder for the source .po files

    def clean(self, _versions: list[str]) -> None:
        # Described in BuildHookInterface
        # This implementation tries to remove .mo files (or any file if
        #  the direction force_clean=True is given) and empty directories
        # In any case a remove error is not fatal and will not abort the build
        self.build_conf()
        self.app.display_debug("Cleaning everything in " + self.config["locale"], 2)
        force = self.config.get("force_clean")
        for name in sorted(self.locale.rglob("*"), reverse=True):
            if name.is_dir():
                try:
                    name.rmdir()
                except OSError:
                    self.app.display_warning(
                        f"Folder {name.name} not removed (not empty?)"
                    )
            elif force or name.suffix == ".mo":
                try:
                    name.unlink()
                except OSError:
                    self.app.display_warning(f"File {name.name} not removed")

    def initialize(self, _version: str, build_data: dict[str, Any]) -> None:
        # Described in BuildHookInterface
        self.build_conf()
        self.app.display_debug(f"hatch-msgfmt-s-ball building {self.target_name}")
        if self.target_name != "wheel":
            # The plugin only makes sense when building a wheel
            # but calling it for another target does not deserve an abort
            self.app.display_warning(
                f"{self.target_name}: unexpected target - call ignored"
            )
            return
        if not self.src.is_dir():
            self.app.display_error(
                f'{self.config["messages"]} is not a directory: giving up'
            )
            return
        for path, lang, domain in self.source_files():
            (self.locale / lang / "LC_MESSAGES").mkdir(parents=True, exist_ok=True)
            mo = str(self.locale / lang / "LC_MESSAGES" / (domain + ".mo"))
            make(str(path), mo)
            mox = "locale/{lang}/LC_MESSAGES/{domain}.mo".format(
                lang=lang, domain=domain
            )
            build_data["force_include"][mox] = mox
            self.app.display_debug(
                "Compiling {src} to {locale}".format(src=str(path), locale=mox), 1
            )

    def build_conf(self) -> None:
        """
        Set default values for parameters not present in config files

        :return: None
        """
        if "messages" not in self.config:
            self.config["messages"] = "messages"
        if "locale" not in self.config:
            self.config["locale"] = "locale"
        self.locale = Path(self.root) / self.config["locale"]
        self.src = Path(self.root) / self.config["messages"]
        if "domain" not in self.config:
            self.config["domain"] = (
                self.metadata.name
                if self.config["messages"] in (".", "messages")
                else self.src.name
            )

    def source_files(self) -> Generator[tuple[Path, str, str], None, None]:
        """
        Yield tuples (file_path, lang, domain) of po files.

        :return: the generator
        """
        # a compiled regex to extract the domain if present and the lang code
        rx = re.compile(r"^(?:(.+)-)?([a-z]{2,3}(?:_[A-Z]+)?)$")
        for child in self.src.iterdir():
            if child.is_dir():
                # found a LANG folder
                for po in child.rglob(r"*.po"):
                    yield po, child.name, po.stem
            elif child.suffix == ".po":
                m = rx.match(child.stem)
                if m:
                    domain = self.config["domain"] if m.group(1) is None else m.group(1)
                    yield child, m.group(2), domain

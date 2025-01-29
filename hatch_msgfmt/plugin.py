#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class MsgFmtBuildHook(BuildHookInterface):
    PLUGIN_NAME = "msgfmt"
    locale: Path
    src: Path

    def clean(self, _versions: list[str]) -> None:
        self.build_conf()
        self.app.display_debug('Cleaning everything in '
                               + self.config['locale'], 2)
        force = self.config.get("force_clean")
        for name in sorted(self.locale.rglob('*'), reverse=True):
            if name.is_dir():
                try:
                    name.rmdir()
                except OSError:
                    self.app.display_warning(
                        f'Folder {name.name} not removed (not empty?)')
            elif force or name.suffix == '.mo':
                try:
                    name.unlink()
                except OSError:
                    self.app.display_warning(f'File {name.name} not removed')

    def initialize(self, _version: str, _build_data: dict[str, Any]) -> None:
        self.build_conf()
        self.app.display_debug(f'hatch-msgfmt-s-ball building {self.target_name}')
        if self.target_name != 'wheel':
            self.app.display_warning(
                f'{self.target_name}: unexpected target - call ignored')
            return
        if not self.src.is_dir():
            self.app.display_error(
                f'{self.config["messages"]} is not a directory: giving up')
            return

    def build_conf(self):
        print('app verbosity', self.app.verbosity)
        if 'messages' not in self.config:
            self.config['messages'] = 'messages'
        if 'locale' not in self.config:
            self.config['locale'] = 'locale'
        self.locale = Path(self.directory) / self.config['locale']
        self.src = Path(self.root) / self.config['messages']
        if 'domain' not in self.config:
            self.config['domain'] = (
                self.metadata.name
                if self.config['messages'] in ('.', 'messages')
                else self.src.name)

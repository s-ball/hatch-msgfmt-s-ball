#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import re
from pathlib import Path
from typing import Any, Generator
from .vendor.msgfmt import make

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class MsgFmtBuildHook(BuildHookInterface):
    PLUGIN_NAME = "msgfmt"
    locale: Path
    src: Path
    full = re.compile('^(.*)-([a-z]{2}(?:_[A-Z]{2})?)$')

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

    def initialize(self, _version: str, build_data: dict[str, Any]) -> None:
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
        for (path, lang, domain) in self.source_files():
            (self.locale / lang / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
            mo = str(self.locale / lang / 'LC_MESSAGES' / (domain + '.mo'))
            make(str(path), mo)
            mox = 'locale/{lang}/LC_MESSAGES/{domain}.mo'.format(lang=lang,
                                                               domain=domain)
            build_data['force_include'][mox] = mox

    def build_conf(self) -> None:
        if 'messages' not in self.config:
            self.config['messages'] = 'messages'
        if 'locale' not in self.config:
            self.config['locale'] = 'locale'
        self.locale = Path(self.root) / self.config['locale']
        self.src = Path(self.root) / self.config['messages']
        if 'domain' not in self.config:
            self.config['domain'] = (
                self.metadata.name
                if self.config['messages'] in ('.', 'messages')
                else self.src.name)

    def source_files(self) -> Generator[tuple[Path, str, str], None, None]:
        rx = re.compile(r'^(?:(.+)-)?([a-z]{2,3}(?:_[A-Z]+)?)$')
        for child in self.src.iterdir():
            if child.is_dir():
                # found a LANG folder
                for po in child.rglob(r'*.po'):
                    yield po, child.name, po.stem
            elif child.suffix == '.po':
                m = rx.match(child.stem)
                if m:
                    domain = (self.config['domain'] if m.group(1) is None
                              else m.group(1))
                    yield child, m.group(2), domain

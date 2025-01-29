#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import logging.config
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class MsgFmtBuildHook(BuildHookInterface):
    PLUGIN_NAME = "msgfmt"
    logger: logging.Logger = None
    locale: Path
    src: Path

    def clean(self, _versions: list[str]) -> None:
        self.build_conf()
        self.logger.info('Cleaning everything in %s', str(self.locale))
        force = self.config.get("force_clean")
        for name in sorted(self.locale.rglob('*'), reverse=True):
            if name.is_dir():
                try:
                    name.rmdir()
                except OSError as e:
                    self.logger.warning('Folder %s not removed (not empty?)',
                                        str(name), exc_info=e)
            elif force or name.suffix == '.mo':
                try:
                    name.unlink()
                except OSError as e:
                    self.logger.warning('File %s not removed',
                                        str(name), exc_info=e)


    def initialize(self, _version: str, _build_data: dict[str, Any]) -> None:
        self.build_conf()
        self.logger.info('hatch-msgfmt building %s', self.target_name)
        if self.target_name != 'wheel':
            self.logger.warning('%s: unexpected target - call ignored',
                                self.target_name)
            return
        if not self.src.is_dir():
            self.logger.error('%s is not a directory: giving up',
                              self.config['messages'])
            return

    def build_logger(self, conf:[dict[str, str]]=None) -> logging.Logger:
        default_conf = {'level': logging.WARNING,
                       'format': "%(name)s - %(levelname)s - %(message)s"}
        log_config = {
            'version': 1,
            'formatters': {'fmt': {}},
            'handlers': {'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'fmt',
                'stream': sys.stdout
            }},
            'loggers': {self.PLUGIN_NAME:{
                'handlers': ['console']
            }}
        }
        if conf is not None:
            default_conf.update(conf)
        # noinspection PyTypedDict
        log_config['formatters']['fmt'] = {'format': default_conf['format']}
        log_config['handlers']['console']['level'] = default_conf['level']
        log_config['loggers'][self.PLUGIN_NAME]['level'] = default_conf['level']
        logging.config.dictConfig(log_config)
        return logging.getLogger(self.PLUGIN_NAME)

    def build_conf(self):
        if not self.logger:
            self.logger = self.build_logger(self.config.get('logging'))
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

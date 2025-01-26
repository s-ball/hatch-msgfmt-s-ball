#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import logging.config
import sys
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class MsgFmtBuildHook(BuildHookInterface):
    PLUGIN_NAME = "msgfmt"
    def clean(self, versions: list[str]) -> None:
        pass
    logger = None

    def initialize(self, _version: str, _build_data: dict[str, Any]) -> None:
        self.logger = self.build_logger(self.config.get('logging'))
        self.logger.info('hatch-msgfmt building %s', self.target_name)
        if self.target_name != 'wheel':
            self.logger.warning('%s: unexpected target', self.target_name)

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

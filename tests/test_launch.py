#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import logging
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import Mock

import pytest
from hatchling.metadata.core import ProjectMetadata

from hatch_msgfmt.plugin import MsgFmtBuildHook


def build_hook(config: dict[str, Any]=None,
               target_name:str = 'wheel', directory = '.'):
    if config is None:
        config = {}
    from hatchling.builders.config import BuilderConfig
    return MsgFmtBuildHook('.', config, Mock(BuilderConfig),
                           Mock(ProjectMetadata), directory, target_name)

@pytest.fixture
def hook():
    return build_hook()


def test_logger_default(hook):
    logger = hook.build_logger(None)
    assert logger.level == logging.WARNING


def test_logger_debug(hook):
    logger = hook.build_logger({'level': 'DEBUG'})
    assert logger.level == logging.DEBUG
    assert logger.handlers[0].level == logging.DEBUG

def test_wrong_target():
    hook = build_hook(target_name='sdist')
    hook.logger = Mock(logging.Logger)
    hook.initialize('', {})
    hook.logger.warning.assert_called()
    assert hook.logger.warning.call_args_list[0][0][1] == 'sdist'


class TestClean:
    @pytest.fixture
    def locale(self):
        with TemporaryDirectory() as d:
            directory = Path(d, 'locale')
            directory.mkdir()
            yield directory

    @pytest.fixture
    def hook(self, locale):
        return build_hook(config={'logging': {'level': 'DEBUG'}},
                          directory=str(locale.parent))

    def test_simple(self, locale, hook):
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        mo.write_bytes(b'abcd')
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.glob('*'))) == 0

    def test_other_than_mo(self, locale, hook):
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        other = fr/'foo'
        mo.write_bytes(b'abcd')
        other.write_bytes(b'ef')
        assert len(list(locale.rglob('*'))) == 3
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.rglob('*'))) == 2

    def test_unlink_error(self, locale, hook):
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        mo.write_bytes(b'abcd')
        mo.chmod(0o444)
        assert len(list(locale.rglob('*'))) == 2
        hook.logger = Mock(logging.Logger)
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.rglob('*'))) == 2
        assert hook.logger.warning.call_args_list[0][0][0].startswith('File')
        assert hook.logger.warning.call_args_list[0][0][1].endswith('foo.mo')

    def test_force(self, locale, hook):
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        other = fr/'foo'
        mo.write_bytes(b'abcd')
        other.write_bytes(b'ef')
        assert len(list(locale.rglob('*'))) == 3
        hook.config['force_clean'] = True
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.rglob('*'))) == 0

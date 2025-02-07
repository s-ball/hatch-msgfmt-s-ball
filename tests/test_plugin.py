#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import filecmp
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Union
from unittest.mock import Mock, PropertyMock, patch

from hatch_msgfmt import plugin
import pytest
from hatchling.bridge.app import Application
from hatchling.metadata.core import ProjectMetadata

from hatch_msgfmt.plugin import MsgFmtBuildHook


def build_hook(config: dict[str, Any]=None,
               target_name:str = 'wheel',
               directory: Union[str, Path] = '.',
               root: Union[str, Path] ='.'):
    if config is None:
        config = {}
    from hatchling.builders.config import BuilderConfig
    return MsgFmtBuildHook(root, config, Mock(BuilderConfig),
                           Mock(ProjectMetadata), directory, target_name,
                           Mock(Application))

@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / 'data'

@pytest.fixture
def hook():
    return build_hook()


# noinspection PyUnresolvedReferences
def test_wrong_target():
    hook = build_hook(target_name='sdist')
    hook.initialize('', {})
    hook.app.display_warning.assert_called()
    assert 'sdist' in hook.app.display_warning.call_args_list[0][0][0]

@pytest.fixture
def locale():
    with TemporaryDirectory() as d:
        directory = Path(d, 'locale')
        directory.mkdir()
        yield directory


class TestClean:
    @pytest.fixture
    def hook(self, locale):
        return build_hook(root=str(locale.parent))

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

    # noinspection PyUnresolvedReferences
    def test_unlink_error(self, locale, hook):
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        mo.write_bytes(b'abcd')
        mo.chmod(0o444)
        assert len(list(locale.rglob('*'))) == 2
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.rglob('*'))) == 2
        assert hook.app.display_warning.call_args_list[0][0][0].startswith('File')
        assert 'foo.mo' in hook.app.display_warning.call_args_list[0][0][0]

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


class TestDefaultDomain:
    # noinspection PyPropertyAccess
    def test_proj_name(self, hook):
        type(hook.metadata).name = PropertyMock(return_value = 'proj_name')
        hook.build_conf()
        assert hook.config['domain'] == 'proj_name'

    def test_message(self):
        hook = build_hook({'messages': 'dom'})
        hook.build_conf()
        assert hook.config['domain'] == 'dom'

    def test_domain(self):
        hook = build_hook({'messages': 'src', 'domain': 'dom'})
        hook.build_conf()
        assert hook.config['domain'] == 'dom'


@pytest.fixture
def messages(locale):
    directory = locale.parent / 'messages'
    directory.mkdir()
    yield directory


class TestPoList:

    def test_flat_single_domain(self, messages):
        po1 = messages / 'en.po'
        po1.write_text('#foo')
        po2 = po1.with_stem('myapp-fr_CA')
        po2.write_text('#bar')
        hook = build_hook({'domain': 'myapp'}, root = str(messages.parent))
        hook.build_conf()
        lst = list(hook.source_files())
        assert len(lst) == 2
        assert (po1, 'en', 'myapp') in lst
        assert (po2, 'fr_CA', 'myapp') in lst

    def test_flat_many_domains(self, messages):
        po1 = messages / 'en.po'
        po1.write_text('#foo')
        po2 = po1.with_stem('foo-fr_CA')
        po2.write_text('#bar')
        hook = build_hook({'domain': 'myapp'}, root = str(messages.parent))
        hook.build_conf()
        lst = list(hook.source_files())
        assert len(lst) == 2
        assert (po1, 'en', 'myapp') in lst
        assert (po2, 'fr_CA', 'foo') in lst

    def test_lang_folders(self, messages):
        fr = messages / 'fr_FR' / 'LC_MESSAGES'
        fr.mkdir(parents=True)
        de = messages /'de' / 'LC_MESSAGES'
        de.mkdir(parents=True)
        po1 = fr / 'myapp.po'
        po1.write_text('#foo')
        po2 = de / 'myapp.po'
        po2.write_text('#bar')
        hook = build_hook(root=messages.parent)
        hook.build_conf()
        lst = list(hook.source_files())
        assert len(lst) == 2
        assert (po1, 'fr_FR', 'myapp') in lst
        assert (po2, 'de', 'myapp') in lst


class TestFmt:
    def test_mocked(self, data_dir, messages):
        shutil.copy(data_dir / 'foo-fr.po', messages / 'foo-fr.po')
        hook = build_hook({'domain': 'foo'},root=messages.parent)
        build_data = {'force_include': {}}
        with patch('hatch_msgfmt.plugin.make'):
            hook.initialize('standard', build_data)
            # noinspection PyUnresolvedReferences
            plugin.make.assert_called_with(
                str(messages / 'foo-fr.po'),
                str(messages.parent / 'locale' / 'fr' / 'LC_MESSAGES' / 'foo.mo'))

    def test_flat(self, data_dir, messages, locale):
        shutil.copy(data_dir / 'foo-fr.po', messages / 'foo-fr.po')
        shutil.copy(data_dir / 'foo-fr.po', messages / 'bar-fr.po')
        shutil.copy(data_dir / 'foo-fr.po', messages / 'fr.po')
        hook = build_hook({'domain': 'fee'},root=messages.parent)
        build_data = {'force_include': {}}
        hook.initialize('standard', build_data)
        assert (locale / 'fr' / 'LC_MESSAGES').is_dir()
        assert (locale / 'fr' / 'LC_MESSAGES' / 'foo.mo').exists()
        assert (locale / 'fr' / 'LC_MESSAGES' / 'bar.mo').exists()
        assert (locale / 'fr' / 'LC_MESSAGES' / 'fee.mo').exists()
        assert filecmp.cmp(locale / 'fr' / 'LC_MESSAGES' / 'foo.mo',
                           locale / 'fr' / 'LC_MESSAGES' / 'bar.mo', 0)
        assert filecmp.cmp(locale / 'fr' / 'LC_MESSAGES' / 'foo.mo',
                           locale / 'fr' / 'LC_MESSAGES' / 'fee.mo', 0)
        assert {'locale/fr/LC_MESSAGES/foo.mo', 'locale/fr/LC_MESSAGES/bar.mo',
                'locale/fr/LC_MESSAGES/fee.mo'
                } == set(build_data['force_include'].values())

class TestGettext:
    def test_data(self, data_dir, messages, locale):
        import gettext

        shutil.copy(data_dir / 'foo-fr.po', messages / 'foo-fr.po')
        hook = build_hook({'domain': 'fee'},root=messages.parent)
        build_data = {'force_include': {}}
        hook.initialize('standard', build_data)

        assert gettext.find('foo', locale, ['fr_FR']) is not None

        trans = gettext.translation('foo', locale, ['fr_FR'])
        assert isinstance(trans, gettext.GNUTranslations)

        assert 'éè' == trans.gettext('foo')
        assert 'àç' == trans.ngettext('bar', 'baz', 1)
        assert 'ça' == trans.ngettext('bar', 'baz', 2)
        assert 'ça' == trans.ngettext('bar', 'baz', 0)

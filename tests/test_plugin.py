#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
"""
This pytest module does the heavy testing of the plugin module.

It ensures that every methode does the expected job when given the
appropriate parameters
"""
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
    """
    Builds a MsgFmtBuildHook with the correct parameters.

    The parameters BuilderConfig, ProjectMetadata and Application are
    always Mock values.

    :param config: a populated config or None
    :param target_name: the target name
    :param directory: the build directory (should be dist in the real world)
    :param root: the root directory (containing pyproject.toml in real)
    :return: a MsgFmtBuildHook
    """
    if config is None:
        config = {}
    from hatchling.builders.config import BuilderConfig
    return MsgFmtBuildHook(root, config, Mock(BuilderConfig),
                           Mock(ProjectMetadata), directory, target_name,
                           Mock(Application))


@pytest.fixture
def data_dir() -> Path:
    """
    pytest fixtures returning the pathlib.Path of the tests/data folder

    :return: the path of the tests/data folder
    """
    return Path(__file__).parent / 'data'


@pytest.fixture
def hook():
    """
    A pytest fixture returning a default MsgFmtBuildHook

    :return: a default MsgFmtBuildHook
    """
    return build_hook()


# noinspection PyUnresolvedReferences
def test_wrong_target():
    """
    Ensures that a warning is emitted is target is not wheel

    :return: None
    """
    hook = build_hook(target_name='sdist')
    hook.initialize('', {})
    hook.app.display_warning.assert_called()
    assert 'sdist' in hook.app.display_warning.call_args_list[0][0][0]

@pytest.fixture
def locale():
    """
    A yield pytest fixture providing a temporary locale folder.

    Using yield allows automatic removal of the temporary directory
    after the test.

    :return: a Path to a temporary locale folder
    """
    with TemporaryDirectory() as d:
        directory = Path(d, 'locale')
        directory.mkdir()
        yield directory


class TestClean:
    """
    Tests for the clean method of MsgFmtBuildHook
    """
    @pytest.fixture
    def hook(self, locale):
        """
        A specialized fixture providing a MsgFmtBuildHook having a
        locale directory

        :param locale: the Path to the locale folder
        :return: a MsgFmtBuildHook
        """
        return build_hook(root=str(locale.parent))

    def test_simple(self, locale, hook):
        """
        Ensures that a single mo file under the locale directory is removed

        :param locale: path to the locale directory
        :param hook: a configured MsgFmtBuildHook
        :return: None
        """
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        mo.write_bytes(b'abcd')
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.glob('*'))) == 0

    def test_other_than_mo(self, locale, hook):
        """
        Ensures that files without the .mo suffix are not removed.

        The folder containing them shall not be removed either

        :param locale: path to the locale folder
        :param hook: a configured MsgFmtBuildHook
        :return: None
        """
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        other = fr/'foo'
        mo.write_bytes(b'abcd')
        other.write_bytes(b'ef')
        assert len(list(locale.rglob('*'))) == 3
        hook.clean(['sdist', 'wheel'])
        # both fr/foo and fr shall remain...
        assert len(list(locale.rglob('*'))) == 2

    # noinspection PyUnresolvedReferences
    def test_unlink_error(self, locale, hook):
        """
        Ensures that an OS error when removing a .mo file issues a warning

        :param locale: path to the locale directory
        :param hook: a configured MsgFmtBuildHook
        :return: None
        """
        fr = locale / 'fr'
        fr.mkdir()
        mo = fr / 'foo.mo'
        mo.write_bytes(b'abcd')
        mo.chmod(0o444)            # mark the foo.mo file as read only
        assert len(list(locale.rglob('*'))) == 2
        hook.clean(['sdist', 'wheel'])
        assert len(list(locale.rglob('*'))) == 2
        assert hook.app.display_warning.call_args_list[0][0][0].startswith('File')
        assert 'foo.mo' in hook.app.display_warning.call_args_list[0][0][0]

    def test_force(self, locale, hook):
        """
        Ensures that any file is removed with the force_clean option

        :param locale: path to the locale directory
        :param hook: a configured MsgFmtBuildHook
        :return: None
        """
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
    """
    Test for detection and usage of a default gettext domain
    """
    # noinspection PyPropertyAccess
    def test_proj_name(self, hook):
        """
        Ensures that the default domain is the project name

        :param hook: a default MsgFmtBuildHook
        :return: None
        """
        type(hook.metadata).name = PropertyMock(return_value = 'proj_name')
        hook.build_conf()
        assert hook.config['domain'] == 'proj_name'

    def test_message(self):
        """
        Ensures that the default domain is the name of the source folder

        :return: None
        """
        hook = build_hook({'messages': 'dom'})
        hook.build_conf()
        assert hook.config['domain'] == 'dom'

    def test_domain(self):
        """
        Ensures that a specified domain name takes precedence

        :return: None
        """
        hook = build_hook({'messages': 'src', 'domain': 'dom'})
        hook.build_conf()
        assert hook.config['domain'] == 'dom'


@pytest.fixture
def messages(locale):
    """
    A pytest fixture that builds a messages folder as a sibling of the locale one

    :param locale: the result of the locale fixture
    :return: None
    """
    directory = locale.parent / 'messages'
    directory.mkdir()
    yield directory


class TestPoList:
    """
    Tests for the generation of the list of .po files
    """

    def test_flat_single_domain(self, messages):
        """
        Ensures that the list uses the default domain when the file name is LANG.po

        :param messages: a messages folder
        :return: None
        """
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
        """
        Ensures that a domain specified in the file name takes precedence

        :param messages: a messages folder
        :return: None
        """
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
        """
        Ensures that a language folder is used

        :param messages: a messages folder
        :return: None
        """
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
    """
    Tests for the generation of a .mo file by FmtMsg.py
    """
    def test_mocked(self, data_dir, messages):
        """
        Ensures (through a Mock) that the make function is correctly called

        :param data_dir: the tests/data folder containing a .po file
        :param messages: a messages folder
        :return: None
        """
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
        """
        Ensures that the .mo files are generated in the correct folder

        Also ensures that the list of the generated .mo files is passed
        back for the calling hatchling builder.

        :param data_dir: the tests/data folder containing a .po file
        :param messages: a messages folder
        :param locale: the locale folder
        :return: None
        """
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
    """
    End-to-end test for the usage of the generated .mo file
    """
    def test_data(self, data_dir, messages, locale):
        """
        Ensures that the generated .mo file is correctly used by gettext

        :param data_dir: the tests/data folder containing a .po file
        :param messages: the source messages folder
        :param locale: the locale folder
        :return: None
        """
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

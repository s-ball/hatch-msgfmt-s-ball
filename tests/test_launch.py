#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
"""
pytest module for testing the integration of the hook in the hatchling
machinery.
"""
import shutil
import subprocess
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(scope='session')
def plugin_dir():
    """
    A pytest fixture yielding a populated copy of the project folder

    The yield ensures that the temporary folders are removed after test

    :return: A populated copy of the project folder
    """
    with TemporaryDirectory() as d:
        directory = Path(d, 'plugin')
        shutil.copytree(
            Path.cwd(), directory, ignore=shutil.ignore_patterns(
                '.git', 'venv*', 'dist')
        )

        yield directory.resolve()


@pytest.fixture
def new_project(tmp_path, plugin_dir):
    """
    A pytest fixture providing a tiny project using hatch-msgfmt-s-ball

    :param tmp_path: a folder for temporary files
    :param plugin_dir: the result of the plugin_dir fixture
    :return: the path for the new project using hatch-msgfmt-s-ball
    """
    project_dir = tmp_path / 'my_app'
    project_dir.mkdir()
    (project_dir / 'src').mkdir()

    project_file = project_dir / 'pyproject.toml'
    project_file.write_text(
        f"""\
[build-system]
requires = ["hatchling", "hatch-msgfmt-s-ball@ {plugin_dir.as_uri()}"]
build-backend = "hatchling.build"

[project]
name = "my_app"
version = "0.1.0"

[tool.hatch.build.targets.wheel.hooks.msgfmt]
messages = "src"
domain = "my_app"
""",
        encoding='utf-8',
    )
    return project_dir


def test_context(new_project):
    """
    Ensures that the plugin is correctly called and is silent

    :param new_project: the result of the new_project fixture
    :return: None
    """
    # print(new_project)  # uncomment to spy the project build
    hatch = shutil.which('hatch')
    build = subprocess.run([hatch, 'build', '--hooks-only'],
                           cwd=new_project, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
    # print(build)        # uncomment to see the result of the build
    assert build.returncode == 0
    assert b'INFO' not in build.stderr


def test_context_debug(new_project):
    """
    Ensures that the plugin correctly uses the verbosity of the hatch call

    :param new_project: the result of the new_project fixture
    :return: None
    """
    # print(new_project)
    hatch = shutil.which('hatch')
    build = subprocess.run([hatch, '-v', 'build', '--hooks-only'],
                           cwd=new_project, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
    # print(build)
    assert build.returncode == 0
    assert b'hatch-msgfmt-s-ball building wheel' in build.stderr
    assert b'building sdist' not in build.stderr


@pytest.fixture
def data_dir() -> Path:
    """
    A pytest fixture returning the path to the tests/data folder.

    This folder contains a perfectly defined .po file

    :return: the path to the tests/data folder
    """
    return Path(__file__).parent / 'data'


def test_build(data_dir, new_project):
    """
    Ensures that the built wheel contains the expected .mo file

    :param data_dir: path to the tests/data folder containing a .po file
    :param new_project: the result of the new_project fixture
    :return: None
    """
    src = new_project / 'src'
    shutil.copy(data_dir / 'foo-fr.po', src / 'my_app-fr.po')
    py_folder = new_project / 'my_app'
    py_folder.mkdir()
    (py_folder/ '__init__.py').write_text("")
    (py_folder/ '__main__.py').write_text("""
print('my_app was launched'
""")
    hatch = shutil.which('hatch')
    build = subprocess.run([hatch, 'build'],
                           cwd=new_project, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, check=False)
    assert build.returncode == 0
    file = next((new_project / 'dist').glob('*.whl'))
    z =zipfile.ZipFile(file)
    assert z.getinfo('locale/fr/LC_MESSAGES/my_app.mo') is not None
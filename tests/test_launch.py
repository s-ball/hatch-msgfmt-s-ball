#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture(scope='session')
def plugin_dir():
    with TemporaryDirectory() as d:
        directory = Path(d, 'plugin')
        shutil.copytree(
            Path.cwd(), directory, ignore=shutil.ignore_patterns(
                '.git', 'venv*', 'dist')
        )

        yield directory.resolve()


@pytest.fixture
def new_project(tmp_path, plugin_dir):
    project_dir = tmp_path / 'my-app'
    project_dir.mkdir()

    project_file = project_dir / 'pyproject.toml'
    project_file.write_text(
        f"""\
[build-system]
requires = ["hatchling", "hatch-msgfmt-s-ball@ {plugin_dir.as_uri()}"]
build-backend = "hatchling.build"

[project]
name = "my-app"
version = "0.1.0"

[tool.hatch.build.targets.wheel.hooks.msgfmt]
messages = "src"
""",
        encoding='utf-8',
    )
    return project_dir


@pytest.fixture
def new_project_debug(new_project):
    project_file = new_project / 'pyproject.toml'
    with project_file.open('a', encoding='utf-8',) as fd:
        fd.write("""
logging.level = "DEBUG"
logging.format = "%(name)s - %(levelname)s - %(message)s"
"""
        )
    return new_project


def test_context(new_project):
    print(new_project)
    hatch = shutil.which('hatch')
    build = subprocess.run([hatch, 'build', '--hooks-only'],
                           cwd=new_project, stdout=subprocess.PIPE, check=False)
    print(build)
    assert build.returncode == 0
    assert b'INFO' not in build.stdout


def test_context_debug(new_project_debug):
    print(new_project_debug)
    hatch = shutil.which('hatch')
    build = subprocess.run([hatch, 'build', '--hooks-only'],
                           cwd=new_project_debug, stdout=subprocess.PIPE, check=False)
    print(build)
    assert build.returncode == 0
    assert b'INFO - hatch-msgfmt-s-ball building wheel' in build.stdout
    assert b'building sdist' not in build.stdout

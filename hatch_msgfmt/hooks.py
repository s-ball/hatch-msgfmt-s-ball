#  SPDX-FileCopyrightText: 2025-present s-ball <s-ball@laposte.net>
#  #
#  SPDX-License-Identifier: MIT
"""
This is just the registration of the plugin module.
"""
from hatchling.plugin import hookimpl

from .plugin import MsgFmtBuildHook


@hookimpl
def hatch_register_build_hook():
    return MsgFmtBuildHook

# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2025 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

# ruff: noqa: F401
from .._internal.signal import create_effect
from ._primitives import bind, computed, effect, render_effect, writeback
from ._reactive_class import reactive_class, reactive_instance
from ._signal import signal
from ._store import ReactiveDict as reactive_dict
from ._store import ReactiveList as reactive_list

__version__ = "0.1.2"


@reactive_class
class Reactive:
    pass

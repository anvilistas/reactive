# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from ._primitives import bind, computed_property, effect, render_effect, writeback
from ._reactive_class import reactive_class
from ._signal import signal

__version__ = "0.0.1"


@reactive_class
class Reactive:
    pass

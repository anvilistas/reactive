# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil import is_server_side

from .constants import STATE_CLEAN, STATE_DISPOSED
from .core import Computation
from .owner import handleError

__version__ = "0.1.0"

if is_server_side():

    def queueMicrotask(fn):
        return fn()

else:
    from anvil.js.window import queueMicrotask


scheduledEffects = False
runningEffects = False
renderEffects: list["RenderEffect"] = []
effects: list["Effect"] = []


def flushSync():
    if not runningEffects:
        runEffects()


def flushEffects():
    global scheduledEffects
    scheduledEffects = True
    # log("FLUSHING EFFECTS IN MICRO TASK")
    queueMicrotask(runEffects)


def runTop(node: Computation):
    ancestors: list[Computation] = []

    current = node
    while current is not None:
        if current._state is not STATE_CLEAN:
            ancestors.append(current)
        current = current._parent

    for ancestor in reversed(ancestors):
        if ancestor._state is not STATE_DISPOSED:
            ancestor._updateIfNecessary()


def runEffects():
    global effects, scheduledEffects, runningEffects, renderEffects
    # log("RUNNING EFFECTS")

    if not effects and not renderEffects:
        scheduledEffects = False
        return

    runningEffects = True

    try:
        for r in renderEffects:
            if r._state is not STATE_CLEAN:
                r._updateIfNecessary()

        for r in renderEffects:
            if r.modified:
                r.effect(r._value)
                r.modified = False

        for e in effects:
            if e._state is not STATE_CLEAN:
                runTop(e)

    finally:
        effects = []
        scheduledEffects = False
        runningEffects = False


class Effect(Computation):
    def __init__(self, initialValue, compute, name="effect", **options):
        super().__init__(initialValue, compute, name=name, **options)
        self._updateIfNecessary()
        queueMicrotask(self._updateIfNecessary)
        # effects.append(self)

    def _notify(self, state):
        global effects, scheduledEffects

        if self._state >= state:
            return

        if self._state is STATE_CLEAN:
            effects.append(self)

        self._state = state
        if not scheduledEffects and effects:
            flushEffects()

    def write(self, value, flags=0):
        self._value = value
        return value

    def _setError(self, error):
        handleError(self, error)


class RenderEffect(Computation):
    def __init__(self, compute, effect, name="renderEffect", **options):
        self.modified = False
        self.effect = effect
        super().__init__(None, compute, name=name, **options)
        self._updateIfNecessary()
        # renderEffects.append(self)

    def _notify(self, state):
        global renderEffects, scheduledEffects

        if self._state >= state:
            return

        if self._state is STATE_CLEAN:
            renderEffects.append(self)

        self._state = state

        if not scheduledEffects and renderEffects:
            flushEffects()

    def write(self, value, flags=0):
        self._value = value
        self.modified = True
        return value

    def _setError(self, error):
        handleError(self, error)

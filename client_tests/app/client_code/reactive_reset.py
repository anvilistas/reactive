# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil.js import await_promise, window
from anvil_reactive._internal import core, effect, owner
from anvil_reactive._internal.flags import DEFAULT_FLAGS
from anvil_reactive._internal.signal import create_root
from anvil_reactive.main import _primitives

_disposals = []


def run_in_test_root(fn):
    def run(dispose):
        _disposals.append(dispose)
        return fn()

    return create_root(run)


def _clear_effect_queue():
    effect.effects.clear()
    effect.renderEffects.clear()
    effect.scheduledEffects = False
    effect.runningEffects = False


def drain_before_reset():
    _clear_effect_queue()
    await_promise(window.Promise.resolve())


def hard_reset():
    _clear_effect_queue()

    while _disposals:
        _disposals.pop()()

    core.currentObserver = None
    core.currentMask = DEFAULT_FLAGS
    core.newSources = None
    core.newSourcesIndex = 0
    core.newFlags = 0
    owner.setCurrentOwner(None)

    # WeakMap has no clear operation, so replace the test-owned caches.
    _primitives.REACTIVE_CACHE = window.WeakMap()
    _primitives.REACTIVE_COMPONENT = window.WeakMap()

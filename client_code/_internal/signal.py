# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from .core import Computation, compute
from .effect import Effect, RenderEffect
from .helpers import is_callable
from .owner import HANDLER, Owner, handleError

__version__ = "0.0.2"


def create_signal(initial_value):
    node = Computation(initial_value, None)

    def set_signal(v):
        if is_callable(v):
            return node.write(v(node._value))
        else:
            return node.write(v)

    return [node.read, set_signal]


def create_memo(compute, initialValue=None, name=None):
    node = Computation(initialValue, compute, name=name or "memo")
    return node.read


SENTINEL = object()


def create_effect(effect, initialValue=SENTINEL, name=None):
    def wrap_effect(value=None):
        return effect()

    if initialValue is not SENTINEL:
        wrap_effect = effect

    return Effect(initialValue, wrap_effect, name=name)


def create_render_effect(compute, effect):
    def wrap_effect(value=None):
        return effect()

    def wrap_compute(value=None):
        return compute()

    return RenderEffect(wrap_compute, wrap_effect)


# TODO should these be suspension wrapped?


def create_root(init):
    owner = Owner()

    # TODO - determine number of args to include dispose function
    def wrap_init(value):
        return init(owner.dispose)

    return compute(owner, wrap_init, None)


def run_with_owner(owner, run):
    try:
        return compute(owner, run, None)
    except Exception as e:
        handleError(owner, e)


def catch_error(fn, handler):
    owner = Owner()
    owner._context = {HANDLER: handler}
    try:
        compute(owner, fn, None)
    except Exception as e:
        handleError(owner, e)


# TODO
def create_reaction(fn, initialValue=None, name=None):
    def track(fn):
        node = Computation(initialValue, lambda prev: fn(), name=name)
        node.read()

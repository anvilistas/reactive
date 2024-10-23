# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from functools import partial, wraps

import anvil
from anvil import Component

from .._internal.signal import create_effect, create_memo, create_root
from ._constants import MISSING
from ._utils import CacheDict, noop

if not anvil.is_server_side():
    from anvil.js.window import WeakMap
else:

    class WeakMap(dict):
        has = dict.__contains__
        set = dict.__setitem__


__version__ = "0.0.11"

REACTIVE_CACHE = WeakMap()
REACTIVE_COMPONENT = WeakMap()
REACTIVE_REG = "__reactive_register__"


def wrap(fn):
    @wraps(fn)
    def wrapper(prev=None):
        return fn()

    return wrapper


def create_component_root(component, dispose):
    rcs = REACTIVE_COMPONENT.get(component)
    rcs.disposal.append(dispose)
    for computation in rcs.writebacks:
        computation(component)


def create_reactive_root(obj, dispose):
    cls = type(obj)
    rcs = REACTIVE_CACHE.get(obj)
    for base in cls.__mro__:
        rc = getattr(base, REACTIVE_REG, None)
        if rc is None:
            continue
        for computation in rc:
            rcs[computation] = computation.create(obj)
    if isinstance(obj, Component):
        create_component_root(obj, dispose)


def add_reactivity(sender, **event_args):
    create_root(lambda dispose: create_reactive_root(sender, dispose))


def dispose_reactivity(sender, **event_args):
    disposal = REACTIVE_COMPONENT.get(sender).disposal
    for dispose in disposal:
        dispose()
    disposal.clear()
    rcs = REACTIVE_CACHE.get(sender)
    if rcs is not None:
        rcs.clear()


def wrap_dunder(dunder):
    @wraps(dunder)
    def wrapper(self, *args, **kws):
        return dunder(self._v, *args, **kws)

    return wrapper


for dunder in dict.__dict__:
    if dunder.startswith("__") and dunder not in (
        "__init__",
        "__new__",
        "__getattribute__",
    ):
        setattr(CacheDict, dunder, wrap_dunder(dict.__dict__[dunder]))


class ReactiveComputation:
    _type = ""
    _creator = noop
    _property = False

    def __new__(cls, fn=None, *, init_value=MISSING):
        if fn is None:
            return lambda fn: cls(fn, init_value=init_value)
        self = object.__new__(cls)
        self.fn = fn
        self._prev = init_value is not MISSING
        self._init_value = init_value if self._prev else None
        self.creator = type(self)._creator
        return self

    def setup(self, owner):
        if REACTIVE_REG in owner.__dict__:
            owner.__reactive_register__.append(self)
            return
        owner.__reactive_register__ = [self]

        old_init = owner.__init__
        if hasattr(old_init, "__reactive_init__"):
            return

        @wraps(old_init)
        def __init__(obj, *args, **kws):
            if REACTIVE_CACHE.has(obj):
                return old_init(obj, *args, **kws)

            REACTIVE_CACHE.set(obj, CacheDict())
            old_init(obj, *args, **kws)

            if isinstance(obj, Component):
                if REACTIVE_COMPONENT.has(obj):
                    return
                REACTIVE_COMPONENT.set(obj, CacheDict(writebacks=[], disposal=[]))
                obj.add_event_handler("x-anvil-page-added", add_reactivity)
                obj.add_event_handler("x-anvil-page-removed", dispose_reactivity)
            else:
                create_reactive_root(obj, noop)

        __init__.__reactive_init__ = True
        owner.__init__ = __init__

    def _fn_compute(self, obj, ob_type=None):
        return self.fn.__get__(obj, ob_type or type(obj))

    def get_compute(self, obj):
        if self._prev:
            return self._fn_compute(obj)
        else:
            return wrap(self._fn_compute(obj))

    def __get__(self, obj=None, type=None):
        if obj is None:
            return self
        return self.fn.__get__(obj, type)

    def __set_name__(self, owner, name):
        self.setup(owner)
        self.name = f"{self._type}-{name}"

    def create(self, obj):
        return self.creator(self.get_compute(obj), self._init_value, name=self.name)

    def __call__(self, obj):
        return self.__get__(obj)()


class computed(ReactiveComputation):
    _creator = create_memo

    def _fn_compute(self, obj, ob_type=None):
        if type(self.fn) is property:
            return self.fn.fget.__get__(obj, ob_type or type(obj))
        return self.fn.__get__(obj, ob_type or type(obj))

    def __get__(self, obj=None, type=None):
        if obj is None:
            return self
        rcs = REACTIVE_CACHE.get(obj) or {}
        rv = rcs.get(self, None)
        if rv is None:
            rv = self._fn_compute(obj, type)
        return rv()

    def __call__(self, obj):
        return self.__get__(obj)


class effect(ReactiveComputation):
    _creator = create_effect


class render_effect(ReactiveComputation):
    _creator = create_effect


class MethodLike:
    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kws):
        return self.fn(*args, **kws)


def noop_method(self):
    return


# TODO
# class reaction(ReactiveComputation):
#     _creator = create_reaction
#     _tracker = noop_method

#     def get_compute(self, obj):
#         rcs = REACTIVE_CACHE.get(obj) or {}
#         rv = rcs.get(self, None)
#         if rv is None:
#             rv = wrap(self.fn.__get__(obj))
#             rv = MethodLike(rv)
#             rv.tracker = self._tracker.__get__(obj)
#             rcs[self] = rv
#         return rv

#     def __call__(self, obj):
#         reaction = self.get_compute(obj)
#         track = create_reaction(reaction, name=self.name)

#         def wrap_track(tracker=None):
#             tracker = tracker or reaction.tracker
#             return track(tracker)

#         reaction.track = wrap_track

#     def tracker(self, tracker):
#         self._tracker = tracker


def writeback(component, prop, reactive_or_getter, attr_or_effect=None, events=()):
    """create a writeback between a component property and an atom attribute
    or bind the property to an atom selector
    and call an action when the component property is changed
    events - should be a single event str or a list of events
    If no events are provided this is the equivalent of a data-binding with no writeback
    """
    if not isinstance(component, Component):
        raise TypeError(
            "The first argument to writeback should be a component, "
            f"not {type(component).__name__}"
        )
    rc, attr = reactive_or_getter, attr_or_effect
    if type(events) is str:
        events = [events]
    if isinstance(rc, dict):
        assert attr is not None, "if a dict is provided the attr must be a str"
        getter = partial(rc.__getitem__, attr)
        setter = partial(rc.__setitem__, attr)
    elif callable(rc):
        getter = rc
        setter = attr
        assert callable(attr), "a getter must be combined with a callable effect"
    else:
        assert attr is not None, "if an object is provided the attr must be a str"
        getter = partial(getattr, rc, attr)
        setter = partial(setattr, rc, attr)

    def action(**event_args):
        setter(getattr(component, prop))

    for event in events:
        component.add_event_handler(event, action)

    def render():
        setattr(component, prop, getter())

    if not REACTIVE_COMPONENT.has(component):
        component.add_event_handler("x-anvil-page-added", add_reactivity)
        component.add_event_handler("x-anvil-page-removed", dispose_reactivity)
        REACTIVE_COMPONENT.set(component, CacheDict(writebacks=[], disposal=[]))

    REACTIVE_COMPONENT.get(component).writebacks.append(
        lambda component: create_effect(render)
    )


def bind(component, prop, reactive_or_getter, attr=MISSING):
    """create a data-binding between an component property
    and an atom and its attribute"""
    attr = noop if attr is MISSING else attr
    return writeback(component, prop, reactive_or_getter, attr)

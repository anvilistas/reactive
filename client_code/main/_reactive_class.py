# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import anvil

from ._computations import StoreSignal
from ._constants import MISSING
from ._store import ReactiveDict
from ._utils import is_testing

__version__ = "0.0.12"

dict_getitem = dict.__getitem__
dict_setitem = dict.__setitem__
dict_pop = dict.pop
dict_contains = dict.__contains__

object_new = object.__new__


def is_reactive_root(cls):
    return cls.__dict__.get("__reactive_root__", False)


def has_reactive_root(cls):
    return getattr(cls, "__reactive_root__", False)


class SignalGetterDescriptor:
    def __init__(self, original_descriptor):
        self.original_descriptor = original_descriptor

    def __get__(self, instance, owner):
        if instance is None:
            return self
        rv = self.original_descriptor.__get__(instance, owner)
        if type(rv) is StoreSignal:
            return rv.read()
        return rv

    def __set__(self, instance, value):
        from ._store import wrap

        try:
            prev = self.original_descriptor.__get__(instance, type(instance))
        except AttributeError:
            prev = MISSING

        if type(prev) is not StoreSignal:
            prev = StoreSignal(prev)
            self.original_descriptor.__set__(instance, prev)

        prev.write(wrap(value))

    def __ensure_signal__(self, instance):
        try:
            value = self.original_descriptor.__get__(instance, type(instance))
        except AttributeError:
            return

        if type(value) is not StoreSignal:
            self.__set__(instance, value)


class _:
    __slots__ = "_"


get_set_descriptor = type(_._)


def walk_slots(cls):
    for c in cls.__mro__:
        if c is object:
            return
        slots = getattr(c, "__slots__", None)
        if slots is None:
            continue
        if isinstance(slots, str):
            slots = (slots,)

        yield from (s for s in slots if s != "__dict__")


def walk_slot_descriptors(cls, descriptor_type):
    for slot in walk_slots(cls):
        descriptor = getattr(cls, slot, None)
        if descriptor is None:
            continue

        if isinstance(descriptor, descriptor_type):
            yield slot, descriptor


def override_slots(cls):
    # walks all the slots
    # checks whether the slot on the class is a getter descriptor
    # if it is, then we replace the slot with a getter descriptor that wraps the signal
    for slot, descriptor in walk_slot_descriptors(cls, get_set_descriptor):
        setattr(cls, slot, SignalGetterDescriptor(descriptor))


def override_slot_values(instance=None):
    # if it is, then we replace the slot with a getter descriptor that wraps the signal
    cls = type(instance)
    for _, descriptor in walk_slot_descriptors(cls, SignalGetterDescriptor):
        descriptor.__ensure_signal__(instance)


def reactive_class(base):
    """decorator for an reactive class"""
    if anvil.is_server_side() and not is_testing():
        return base

    if is_reactive_root(base):
        return base

    elif has_reactive_root(base):
        base.__reactive_root__ = True
        override_slots(base)
        return base

    base.__reactive_root__ = True

    old_new = base.__new__
    old_getattr = base.__getattribute__
    old_setattr = base.__setattr__

    override_slots(base)

    @staticmethod
    def __new__(cls, *args, **kws):
        if old_new is object_new:
            self = old_new(cls)
        else:
            self = old_new(cls, *args, **kws)
        try:
            old_dict = self.__dict__
        except AttributeError:
            pass
        else:
            self.__dict__ = ReactiveDict(old_dict)
            old_dict.clear()
        return self

    def __getattribute__(self, attr):
        rv = old_getattr(self, attr)
        if type(rv) is StoreSignal:
            return rv.read()
        return rv

    # This is a bit of faff
    # python setattr doesn't call __dict__.__setitem__
    # instead uses internal .__setitem__ so we let that happen
    # before putting it back into the reactive __dict__
    def __setattr__(self, attr, val):
        d = getattr(self, "__dict__", None)
        if type(d) is dict or d is None:
            return old_setattr(self, attr, val)
        prev = None
        if dict_contains(d, attr):
            prev = dict_getitem(d, attr)
            assert type(prev) is StoreSignal, "expected a signal"
        old_setattr(self, attr, val)
        if not dict_contains(d, attr):
            return
        val = dict_pop(d, attr)
        if prev is not None:
            dict_setitem(d, attr, prev)
        d[attr] = val

    base.__new__ = __new__
    base.__getattribute__ = __getattribute__
    base.__setattr__ = __setattr__

    return base


def reactive_instance(self):
    if anvil.is_server_side() and not is_testing():
        return self

    cls = type(self)

    reactive_class(cls)

    d = getattr(self, "__dict__", None)
    if type(d) is dict:
        self.__dict__ = ReactiveDict(d)

    override_slot_values(self)

    return self

# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import anvil

from ._computations import StoreSignal
from ._store import ReactiveDict

__version__ = "0.0.7"

dict_getitem = dict.__getitem__
dict_setitem = dict.__setitem__
dict_pop = dict.pop

object_new = object.__new__


def reactive_class(base):
    """decorator for an reactive class"""
    if anvil.is_server_side():
        return base

    if hasattr(base, "__is_reactive__"):
        return base

    old_new = base.__new__
    old_getattr = base.__getattribute__
    old_setattr = base.__setattr__

    @staticmethod
    def __new__(cls, *args, **kws):
        if old_new is object_new:
            self = old_new(cls)
        else:
            self = old_new(cls, *args, **kws)
        old_dict = self.__dict__
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
    # instead uses internal .__setitem__ so we let that happen before putting it back into the reactive __dict__
    def __setattr__(self, attr, val):
        d = self.__dict__
        if type(d) is dict:
            return old_setattr(self, attr, val)
        prev = None
        if attr in d:
            prev = dict_getitem(d, attr)
            assert type(prev) is StoreSignal, "expected a signal"
        old_setattr(self, attr, val)
        if attr not in d:
            return
        val = dict_pop(d, attr)
        if prev is not None:
            dict_setitem(d, attr, prev)
        d[attr] = val

    base.__new__ = __new__
    base.__getattribute__ = __getattribute__
    base.__setattr__ = __setattr__
    base.__is_reactive__ = True

    return base


def reactive_instance(self):
    if anvil.is_server_side():
        return self
    reactive_class(type(self))
    if type(self.__dict__) is dict:
        self.__dict__ = ReactiveDict(self.__dict__)
    return self

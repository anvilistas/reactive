# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil import is_server_side
from anvil.server import portable_class

from .._internal.core import isEqual, untrack
from ._computations import StoreSignal, UniqueSignal
from ._constants import MISSING

__version__ = "0.0.3"


def wrap(val):
    if type(val) is dict:
        return ReactiveDict(val)
    elif type(val) is list:
        return ReactiveList(val)
    elif type(val) is StoreSignal:
        return val._value
    else:
        return val


def as_signal(val, name=None):
    return StoreSignal(wrap(val), name)


dict_getitem = dict.__getitem__
dict_setitem = dict.__setitem__
dict_pop = dict.pop


@portable_class
class ReactiveDict(dict):
    __slots__ = ["DICT_KEYS", "DICT_VALS", "DICT_ITEMS"]

    def __init__(self, *args, **kws):
        target = dict(*args, **kws)
        dict.__init__(self, ((k, as_signal(v, name=k)) for k, v in target.items()))
        self.DICT_KEYS = UniqueSignal("dict_keys")
        self.DICT_VALS = UniqueSignal("dict_vals")
        self.DICT_ITEMS = UniqueSignal("dict_items")

    def __getitem__(self, key):
        res = dict_getitem(self, key)
        return res.read()

    def __setitem__(self, key, val):
        current = dict.get(self, key)

        if type(current) is StoreSignal:
            if not isEqual(current._value, val):
                self.DICT_VALS.update()
                self.DICT_ITEMS.update()
            return current.write(wrap(val))

        val = as_signal(val, name=key)
        dict_setitem(self, key, val)

        self.DICT_VALS.update()
        self.DICT_ITEMS.update()
        self.DICT_KEYS.update()

    def __delitem__(self, key):
        self.pop(key)

    def update(self, *args, **kws):
        for k, v in dict(*args, **kws).items():
            self[k] = v

    def clear(self):
        for k in list(dict.keys(self)):
            self.pop(k)

    def pop(self, key, default=MISSING):
        if default is MISSING:
            res = dict_pop(self, key)
        else:
            res = dict_pop(self, key, MISSING)
            if res is MISSING:
                return default

        self.DICT_VALS.update()
        self.DICT_ITEMS.update()
        self.DICT_KEYS.update()
        rv = res._value
        res.write(MISSING)  # force observers to re-run
        return rv

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def __iter__(self):
        return iter(self.keys())

    def __bool__(self):
        self.DICT_KEYS.read()
        return dict.__bool__(self)

    def keys(self):
        self.DICT_KEYS.read()
        return dict.keys(self)

    def values(self):
        self.DICT_VALS.read()
        return [v._value for v in dict.values(self)]

    def items(self):
        self.DICT_ITEMS.read()
        return [(k, v._value) for k, v in dict.items(self)]

    def __repr__(self):
        d = {k: v._value for k, v in dict.items(self)}
        return f"ReactiveDict({d})"

    def __serialize__(self, gbl_data):
        with untrack():
            return dict(self)

    @staticmethod
    def __new_deserialized__(data, gbl_data):
        if is_server_side():
            return dict(data)
        return ReactiveDict(data)


list_get = list.__getitem__
list_set = list.__setitem__
list_len = list.__len__
list_iter = list.__iter__


@portable_class
class ReactiveList(list):
    __slots__ = ["LIST_LEN", "LIST_BOOL"]

    def __init__(self, *args, **kws):
        target = list(*args, **kws)
        list.__init__(self, (as_signal(v) for v in target))
        self.LIST_LEN = UniqueSignal("list_len")

    def __getitem__(self, i):
        rv = list.__getitem__(self, i)
        if type(rv) is StoreSignal:
            return rv.read()
        if type(rv) is list:
            self.LIST_LEN.read()
            return [v.read() for v in rv]

    def __setitem__(self, i, val):
        items = list_get(self, i)
        if type(i) is int:
            items.write(wrap(val))
        else:
            self.LIST_LEN.update()
            list_set(self, i, [as_signal(v) for v in val])

    def remove(self, val):
        list.remove(self, val)
        self.LIST_LEN.update()

    def extend(self, val):
        list.extend(self, (as_signal(v) for v in val))
        self.LIST_LEN.update()

    def append(self, val):
        list.append(self, as_signal(val))
        self.LIST_LEN.update()

    def insert(self, i, val):
        list.insert(self, i, as_signal(val))
        self.LIST_LEN.update()

    def __iter__(self):
        self.LIST_LEN.read()
        return [v.read() for v in list_iter(self)].__iter__()

    def clear(self):
        if not len(self):
            return
        list.clear(self)
        self.LIST_LEN.update()

    def pop(self, *args):
        rv = list.pop(self, *args)
        self.LIST_LEN.update()
        return rv.read()

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __add__(self, other):
        me = [x._value for x in list_iter(self)]
        if type(other) is type(self):
            return me + [x._value for x in list_iter(other)]
        return me + other

    def __radd__(self, other):
        me = [x._value for x in list_iter(self)]
        if type(other) is type(self):
            return [x._value for x in list_iter(other)] + me
        return other + me

    def __imul__(self, x):
        n = len(self)
        for i in range(1, x):
            for j in range(n):
                self.append(as_signal(list_get(self, j)))

        if x <= 0:
            self.clear()

        return self

    def __mul__(self, x):
        return [r._value for r in list_iter(self) for _ in range(x)]

    def __repr__(self):
        return f"ReactiveList({[x._value for x in list_iter(self)]})"

    def __serialize__(self, gbl_data):
        with untrack():
            return list(self)

    @staticmethod
    def __new_deserialized__(data, gbl_data):
        if is_server_side():
            return list(data)
        return ReactiveList(data)

    def __len__(self):
        self.LIST_LEN.read()
        return list_len(self)

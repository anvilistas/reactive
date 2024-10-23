# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil import is_server_side
from anvil.js.window import WeakMap
from anvil.server import portable_class

from .._internal.core import Computation, getObserver, isEqual, untrack
from ._computations import StoreSignal, UniqueSignal
from ._constants import MISSING

__version__ = "0.0.9"

# 0: Data, 1: Has
NODES = [WeakMap(), WeakMap()]


def get_nodes(obj, type):
    node = NODES[type].get(obj)
    if node is None:
        print("Not in nodes", obj, type)
        NODES[type].set(obj, {})
        node = NODES[type].get(obj)
    else:
        print("ALREADY in nodes", obj, type)
    return node


def get_node(node, prop, value=None):
    if prop in node:
        print("PROP ALREADY IN NODE", node, prop)
        return node[prop]

    c = Computation(value, None, equals=False)
    print("PROP NOT IN NODE", node, prop, c)
    node[prop] = c
    return c


def wrap(val):
    if type(val) is dict: # noqa: E721
        return ReactiveDict(val)
    elif type(val) is list: # noqa: E721
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
dict_get = dict.get

class Obscure:
    _id = 0
    def __init__(self, v):
        self.v = v
        self.id = Obscure._id
        Obscure._id += 1

    def __repr__(self):
        return f"<{self.id}:  {repr(self.v)}>"

@portable_class
class ReactiveDict(dict):
    __slots__ = ["DICT_ID","DICT_KEYS", "DICT_VALS", "DICT_ITEMS", "DICT_BOOL"]

    def __init__(self, *args, **kws):
        self.DICT_ID = Obscure(self)
        self.DICT_KEYS = UniqueSignal("dict_keys")
        self.DICT_VALS = UniqueSignal("dict_vals")
        self.DICT_ITEMS = UniqueSignal("dict_items")
        self.DICT_BOOL = UniqueSignal(
            "dict_bool", bool(dict.__len__(self)), equals=None
        )
        target = dict(*args, **kws)
        for k, v in target.items():
            self[k] = v

    def __getitem__(self, key):
        nodes = get_nodes(self.DICT_ID, 0)
        tracked = nodes.get(key)

        print("READING", self, nodes, tracked, key)

        if tracked is not None:
            print("ALREADY TRACKING", self.DICT_ID, tracked, key)
            value = tracked.read()
        else:
            # TODO we don't want to throw here
            value = dict_get(self, key, MISSING)
            print("NOT TRACKING", self.DICT_ID, key, value)

        print("determining whether to track", self, tracked, getObserver(), value)
        if tracked is None and getObserver() is not None: # and value is not MISSING:
            # TODO i think we we need MISSING here too
            print("YES, we should track", self, key, value)
            value = get_node(nodes, key, value).read()

        if value is MISSING:
            raise KeyError(key)

        return value

    def __setitem__(self, key, val):
        print("SETTING", self.DICT_ID, key, val)
        current = dict_get(self, key, MISSING)

        val = wrap(val)

        if current is not MISSING and isEqual(current, val):
            # nothing has changed
            print("NOTHING HAS CHANGED", current, val)
            return

        nodes = get_nodes(self.DICT_ID, 0)
        node = get_node(nodes, key, current)
        node.write(val)
        print("NOTHING YET IN SELF", self.DICT_ID, key, val)
        dict_setitem(self, key, val)

        self.DICT_VALS.update()
        self.DICT_ITEMS.update()
        self.DICT_KEYS.update()
        self.DICT_BOOL.update(bool(dict.__len__(self)))

    def __delitem__(self, key):
        self.pop(key)


    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

    def update(self, *args, **kws):
        for k, v in dict(*args, **kws).items():
            self[k] = v

    def clear(self):
        for k in list(dict.keys(self)):
            self.pop(k)

    def pop(self, key, default=MISSING):
        if default is MISSING:
            rv = dict_pop(self, key)
        else:
            rv = dict_pop(self, key, MISSING)
            if rv is MISSING:
                return default

        nodes = get_nodes(self.DICT_ID, 0)
        node = get_node(nodes, key, rv)

        self.DICT_VALS.update()
        self.DICT_ITEMS.update()
        self.DICT_KEYS.update()
        self.DICT_BOOL.update(bool(dict.__len__(self)))
        node.write(MISSING)  # force observers to re-run
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

    def __len__(self):
        self.DICT_KEYS.read()
        # TODO - we probably want a __bool__ here too
        # that way truthy/falsy won't fire whenever the keys change
        return dict.__len__(self)

    def __bool__(self):
        self.DICT_BOOL.read()
        return bool(dict.__len__(self))

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
        self.DICT_ITEMS.read()
        d = {k: v for k, v in dict.items(self)}
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
        self.LIST_BOOL = UniqueSignal(
            "list_bool", bool(list.__len__(self)), equals=None
        )

    def _update_len(self):
        self.LIST_LEN.update()
        self.LIST_BOOL.update(bool(list.__len__(self)))

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
            self._update_len()
            list_set(self, i, [as_signal(v) for v in val])

    def remove(self, val):
        list.remove(self, val)
        self._update_len()

    def extend(self, val):
        list.extend(self, (as_signal(v) for v in val))
        self._update_len()

    def append(self, val):
        list.append(self, as_signal(val))
        self._update_len()

    def insert(self, i, val):
        list.insert(self, i, as_signal(val))
        self._update_len()

    def __iter__(self):
        self.LIST_LEN.read()
        return [v.read() for v in list_iter(self)].__iter__()

    def clear(self):
        if not len(self):
            return
        list.clear(self)
        self._update_len()

    def pop(self, *args):
        rv = list.pop(self, *args)
        self._update_len()
        return rv.read()

    def sort(self, *, key=None, reverse=False):
        key_ = key
        if key_ is not None:

            def key(x):
                return key_(x._value)

        rv = list.sort(self, key=key, reverse=reverse)
        self._update_len()
        return rv

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
        self.LIST_LEN.read()
        return f"ReactiveList({[x.read() for x in list_iter(self)]})"

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

    def __bool__(self):
        self.LIST_BOOL.read()
        return bool(list.__len__(self))

# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2025 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from ._constants import MISSING
from ._store import StoreSignal, as_signal, wrap

__version__ = "0.1.2"


class signal:
    def __init__(self, default=None, *, default_factory=MISSING):
        self._default = default
        self._default_factory = default_factory

    def __set_name__(self, owner, name):
        self._name = name

    def _get_signal(self, obj):
        d = obj.__dict__
        node = dict.get(d, self._name)
        if node is None:
            if self._default_factory is not MISSING:
                value = self._default_factory()
            else:
                value = self._default
            node = as_signal(value, name=self._name)
            dict.__setitem__(d, self._name, node)
        elif type(node) is not StoreSignal:
            node = as_signal(node, name=self._name)
            dict.__setitem__(d, self._name, node)

        return node

    def __get__(self, obj=None, type=None):
        if obj is None:
            return self
        node = self._get_signal(obj)
        return node.read()

    def __set__(self, obj, value):
        node = self._get_signal(obj)
        # TODO is this just confusing? Probably
        # if callable(value):
        #     return node.write(value(s._value))
        return node.write(wrap(value))

# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil import is_server_side
from anvil.server import portable_class

from .._internal.core import Computation
from ._constants import MISSING

__version__ = "0.0.9"


class UniqueSignal(Computation):
    def __init__(self, name=None, value=0, equals=False):
        super().__init__(value, None, equals=equals, name=name or "unique")

    def update(self, value=MISSING):
        if value is not MISSING:
            return self.write(value)
        return self.write(self._value + 1)


def _cmp(dunder):
    def fn(self, other):
        if type(other) is StoreSignal:
            other = other._value
        try:
            return getattr(self._value, dunder)(other)
        except AttributeError:
            return NotImplemented

    fn.__name__ = dunder
    return fn


@portable_class
class StoreSignal(Computation):
    def __init__(self, val, name=None):
        super().__init__(val, None, name=name)

    def __hash__(self):
        return hash(self._value)

    __eq__ = _cmp("__eq__")
    __ne__ = _cmp("__ne__")
    __lt__ = _cmp("__lt__")
    __le__ = _cmp("__le__")
    __gt__ = _cmp("__gt__")
    __ge__ = _cmp("__ge__")

    def __serialize__(self, gbl_data):
        return self._value

    @staticmethod
    def __new_deserialize__(data, gbl_data):
        if is_server_side():
            return data
        return StoreSignal(data)

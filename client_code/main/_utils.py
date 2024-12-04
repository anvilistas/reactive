# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from functools import wraps

__version__ = "0.1.2"


class CacheDict:
    __slots__ = ["_v", "__dict__"]

    def __init__(self, *args, **kws):
        self._v = dict(*args, **kws)
        self.__dict__ = self._v

    def __getattr__(self, attr):
        return getattr(self._v, attr)


def wrap_dunder(dunder):
    @wraps(dunder)
    def wrapper(self, *args, **kws):
        return dunder(self._v, *args, **kws)

    return wrapper


_special = (
    "__init__",
    "__new__",
    "__getattribute__",
)

for dunder in dict.__dict__:
    if dunder.startswith("__") and dunder not in _special:
        setattr(CacheDict, dunder, wrap_dunder(dict.__dict__[dunder]))


def noop(*args, **kws):
    pass


def is_testing():
    return False

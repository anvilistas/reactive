# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

__version__ = "0.0.5"


class _A:
    def _b(self):
        pass


_FunctionType = type(lambda: None)
_MethodType = type(_A()._b)


def is_callable(x):
    X = type(x)
    return X is _FunctionType or X is _MethodType

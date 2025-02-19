# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2025 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

__version__ = "0.1.3"


class _MISSING:
    def __repr__(self):
        return "<MISSING object>"


MISSING = _MISSING()

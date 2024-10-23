# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

__version__ = "0.0.10"

ERROR_OFFSET = 0
ERROR_BIT = 1 << ERROR_OFFSET
ERROR = object()

LOADING_OFFSET = 1
LOADING_BIT = 1 << LOADING_OFFSET
LOADING = object()

DEFAULT_FLAGS = ERROR_BIT

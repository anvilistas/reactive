# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

__version__ = "0.0.10"

STATE_CLEAN = 0
STATE_CHECK = 1
STATE_DIRTY = 2
STATE_DISPOSED = 3

state_repr = {
    0: "CLEAN",
    1: "CHECK",
    2: "DIRTY",
    3: "DISPOSED",
}


def get_state_repr(state):
    return state_repr[state]

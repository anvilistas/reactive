# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

CASES = []


class Case:
    def __init__(self, fn, classification, reason=None, fresh_page=False):
        self.name = fn.__name__.lstrip("_")
        self.fn = fn
        self.classification = classification
        self.reason = reason
        self.fresh_page = fresh_page


def _register(classification, reason=None, fresh_page=False):
    def decorator(fn):
        CASES.append(Case(fn, classification, reason, fresh_page))
        return fn

    return decorator


def contract(fn=None, *, fresh_page=False):
    decorator = _register("contract", fresh_page=fresh_page)
    return decorator if fn is None else decorator(fn)


def known_gap(reason, *, fresh_page=False):
    return _register("known_gap", reason, fresh_page)

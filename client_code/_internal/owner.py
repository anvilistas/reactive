# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from .constants import STATE_CLEAN, STATE_DISPOSED

__version__ = "0.0.12"

HANDLER = object()

currentOwner = None  # type: Owner | None


def setCurrentOwner(owner=None):
    global currentOwner
    out = currentOwner
    currentOwner = owner
    return out


def getOwner():
    return currentOwner


id = 0


class Owner:
    def __init__(self, signal=False, name=None):
        global id
        self._id = id
        id += 1
        self._name = name
        self._parent = None
        self._nextSibling = None
        self._prevSibling = None
        self._state = STATE_CLEAN
        self._disposal = None
        self._context = None
        if currentOwner and not signal:
            currentOwner.append(self)
        # log(f"creating {id}")

    def append(self, owner: "Owner"):
        owner._parent = self
        owner._prevSibling = self
        if self._nextSibling:
            self._nextSibling._prevSibling = owner
        owner._nextSibling = self._nextSibling
        self._nextSibling = owner

    def dispose(self, include_self=True):
        if self._state is STATE_DISPOSED:
            return

        current = self._nextSibling

        while current and current._parent is self:
            current.dispose(True)
            current = current._nextSibling

        head = self._prevSibling if include_self else self
        if include_self:
            self._disposeNode()
        elif current:
            current._prevSibling = self._prevSibling

        if head:
            head._nextSibling = current

    def _disposeNode(self):
        # log(f"{self}:\n\tdisposing")
        if self._nextSibling:
            self._nextSibling._prevSibling = self._prevSibling
        self._parent = None
        self._prevSibling = None
        self._context = None
        self._state = STATE_DISPOSED
        self.emptyDisposal()

    def emptyDisposal(self):
        # log(f"{self}\n\tempty disposal")
        disposal = self._disposal
        if disposal is None:
            return

        if type(disposal) is list:
            for cb in disposal:
                cb()
        else:
            disposal()

        self._disposal = None

    def __repr__(self):
        cls = type(self).__name__
        id = f"{self._name}-{self._id}" if self._name else self._id
        return f"<{cls}-{id}>"


def onCleanup(disposable):
    if not currentOwner:
        return

    node = currentOwner

    if not node._disposal:
        node._disposal = disposable
    elif type(node._disposal) is list:
        node._disposal.append(disposable)
    else:
        node._disposal = [node._disposal, disposable]


def lookup(owner, key):
    if not owner:
        return

    current = owner

    while current:
        context = current._context
        current = current._parent
        if context is None:
            continue

        value = context.get(key)
        if value is not None:
            return value


def coerceError(error):
    if not isinstance(error, Exception):
        return Exception(error)
    return error


def handleError(owner, error):
    handler = lookup(owner, HANDLER)
    if handler is None:
        raise coerceError(error)

    try:
        handler(coerceError(error))
    except Exception:
        handleError(owner and owner._parent, error)

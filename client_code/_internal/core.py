# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023-2024 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from .constants import (
    STATE_CHECK,
    STATE_CLEAN,
    STATE_DIRTY,
    STATE_DISPOSED,
    get_state_repr,
)
from .error import NotReadyError
from .flags import DEFAULT_FLAGS, ERROR_BIT, LOADING_BIT
from .owner import Owner, getOwner, setCurrentOwner
from .utils import wrap_compute

__version__ = "0.0.12"

currentObserver = None
currentMask = DEFAULT_FLAGS

newSources = None
newSourcesIndex = 0
newFlags = 0

UNCHANGED = object()


class Computation(Owner):
    def __init__(self, initialValue, compute, equals=None, name=None):
        Owner.__init__(self, compute is None)
        self._sources = None
        self._observers = None
        self._value = initialValue
        self._compute = compute and wrap_compute(compute)
        self._state = STATE_DIRTY if compute else STATE_CLEAN
        self._name = name or ("compute" if compute else "signal")
        self._equals = equals if equals is not None else isEqual
        self._stateFlags = 0
        self._handlerMask = DEFAULT_FLAGS
        self._error = None
        self._loading = None

    def _read(self):
        global newFlags

        if self._compute:
            self._updateIfNecessary()

        track(self)

        newFlags |= self._stateFlags & ~currentMask

        if self._stateFlags & ERROR_BIT:
            raise self._value
        else:
            return self._value

    def read(self):
        # log(f"{self}:\n\tread")
        return self._read()

    def wait(self):
        if self.loading():
            raise NotReadyError()
        return self._read()

    def loading(self):
        if self._loading is None:
            self._loading = loadingState(self)
        return self._loading.read()

    def error(self):
        if self._error is None:
            self._error = errorState(self)
        return self._error.read()

    def write(self, value, flags=0):
        valueChanged = value is not UNCHANGED and (
            bool(flags & ERROR_BIT)
            or self._equals is False
            or not self._equals(self._value, value)
        )
        if valueChanged:
            self._value = value

        # log(f"{self}:\n\twriting, valueChanged: {valueChanged} flags: {flags}")

        changedFlagMask = self._stateFlags ^ flags
        changedFlags = changedFlagMask & flags
        self._stateFlags = flags

        observers = self._observers

        if observers is not None:
            for o in observers:
                if valueChanged:
                    o._notify(STATE_DIRTY)
                elif changedFlagMask:
                    o._notifyFlags(changedFlagMask, changedFlags)

        return self._value

    def _notify(self, state):
        if self._state >= state:
            return

        self._state = state
        observers = self._observers
        if observers is not None:
            for o in observers:
                o._notify(STATE_CHECK)

    def _notifyFlags(self, mask, newFlags):
        if self._state >= STATE_DIRTY:
            return

        if mask & self._handlerMask:
            self._notify(STATE_DIRTY)
            return

        if self._state >= STATE_CHECK:
            return

        prevFlags = self._stateFlags & mask
        deltaFlags = prevFlags ^ newFlags

        if newFlags == prevFlags:
            pass
        elif deltaFlags & prevFlags & mask:
            self._notify(STATE_CHECK)
        else:
            self._stateFlags ^= deltaFlags

            observers = self._observers
            if observers is not None:
                for o in observers:
                    o._notifyFlags(mask, newFlags)

    def _setError(self, error):
        self.write(error, self._stateFlags | ERROR_BIT)

    def _updateIfNecessary(self):
        if self._state is STATE_DISPOSED:
            raise Exception("Tried to read a disposed computation")

        if self._state is STATE_CLEAN:
            return

        observerFlags = 0

        if self._state is STATE_CHECK:
            sources = self._sources
            if sources:
                for s in sources:
                    s._updateIfNecessary()
                    observerFlags |= s._stateFlags

                    if self._state is STATE_DIRTY:
                        break

        if self._state is STATE_DIRTY:
            update(self)
        else:
            self.write(UNCHANGED, observerFlags)
            self._state = STATE_CLEAN

    def _disposeNode(self):
        if self._state is STATE_DISPOSED:
            return
        if self._sources is not None:
            removeSourceObservers(self, 0)

        return super()._disposeNode()

    def __repr__(self):
        cls = type(self).__name__
        state = get_state_repr(self._state)
        return f"<{cls}-{self._name}-{self._id}: {self._value} ({state})>"


def loadingState(node: Computation):
    prevOwner = setCurrentOwner(node._parent)

    def compute():
        track(node)
        node._updateIfNecessary()
        return bool(node._stateFlags & LOADING_BIT)

    s = Computation(None, compute, name=f"loading {node._name}")
    s._handlerMask = ERROR_BIT | LOADING_BIT
    setCurrentOwner(prevOwner)
    return s


def errorState(node):
    prevOwner = setCurrentOwner(node._parent)

    def compute():
        track(node)
        node._updateIfNecessary()
        return bool(node._stateFlags & ERROR_BIT)

    s = Computation(None, compute, name=f"error {node._name}")
    s._handlerMask = ERROR_BIT
    setCurrentOwner(prevOwner)
    return s


def track(computation):
    global currentObserver, newSources, newSourcesIndex

    if currentObserver:
        if (
            not newSources
            and currentObserver._sources
            and len(currentObserver._sources) < newSourcesIndex
            and currentObserver._sources[newSourcesIndex] is computation
        ):
            newSourcesIndex += 1
        elif not newSources:
            newSources = [computation]
        elif computation is not newSources[-1]:
            newSources.append(computation)


def update(node: Computation):
    # log(f"{node}: UPDATING")
    global newSources, newSourcesIndex, newFlags
    prevSources = newSources
    prevSourcesIndex = newSourcesIndex
    prevFlags = newFlags

    newSources = None
    newSourcesIndex = 0
    newFlags = 0

    try:
        node.dispose(False)
        node.emptyDisposal()

        result = compute(node, node._compute, node)

        node.write(result, newFlags)

    except Exception as e:
        node._setError(e)
        raise e

    finally:
        if newSources:
            if node._sources:
                removeSourceObservers(node, newSourcesIndex)

            if node._sources and newSourcesIndex > 0:
                node._sources += [None] * newSourcesIndex

                for i, s in enumerate(newSources):
                    node._sources[newSourcesIndex + i] = s

            else:
                node._sources = newSources

            i = newSourcesIndex
            while i < len(node._sources):
                s = node._sources[i]
                if not s._observers:
                    s._observers = [node]
                else:
                    s._observers.append(node)
                i += 1
        elif node._sources and newSourcesIndex < len(node._sources):
            removeSourceObservers(node, newSourcesIndex)
            node._sources = node._sources[:newSourcesIndex]

        newSources = prevSources
        newSourcesIndex = prevSourcesIndex
        newFlags = prevFlags

        node._state = STATE_CLEAN


def removeSourceObservers(node, index):
    sources = node._sources
    if not sources:
        return

    for s in sources:
        observers = s._observers
        if observers:
            swap = observers.index(node)
            observers[swap] = observers[-1]
            observers.pop()


def isEqual(a, b):
    if a is b:
        return True
    A = type(a)
    B = type(b)
    if A is not B:
        return False
    if A is str or A is int or A is float:
        return a == b
    return False


# def untrack(fn):
#     global currentObserver
#     if currentObserver is None:
#         return fn()

#     return compute(getOwner(), fn, None)


class compute:
    def __new__(cls, owner, compute=None, observer=None):
        self = object.__new__(cls)
        self.owner = owner
        if callable(compute):
            self.observer = observer
        else:
            self.observer = compute

        if callable(compute):
            with self:
                return compute(observer._value if observer else None)
        else:
            return self

    def __enter__(self):
        global currentMask, currentObserver
        self.prevOwner = setCurrentOwner(self.owner)
        self.prevObserver = currentObserver
        self.prevMask = currentMask
        currentObserver = self.observer
        currentMask = self.observer._handlerMask if self.observer else DEFAULT_FLAGS

    def __exit__(self, exc, excType, *e):
        global currentMask, currentObserver
        setCurrentOwner(self.prevOwner)
        currentObserver = self.prevObserver
        currentMask = self.prevMask
        return None


class untrack(compute):
    def __new__(cls, fn=None):
        if fn is not None and currentObserver is None:
            return fn()
        return compute.__new__(cls, getOwner(), fn, None)


# compute = Compute()

# def compute(owner, compute, observer):
#     global currentMask, currentObserver
#     prevOwner = setCurrentOwner(owner)
#     prevObserver = currentObserver
#     prevMask = currentMask
#     currentObserver = observer
#     currentMask = observer._handlerMask if observer else DEFAULT_FLAGS

#     try:
#         return compute(observer._value if observer else None)
#     except NotReadyError:
#         raise
#     except Exception as e:
#         # TODO
#         raise
#         return observer._value if observer else None
#     finally:
#         setCurrentOwner(prevOwner)
#         currentObserver = prevObserver
#         currentMask = prevMask


def getObserver():
    global currentObserver
    return currentObserver

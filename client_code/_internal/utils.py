# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import anvil

from .logging import DEBUG, INFO, WARNING, Logger

__version__ = "0.0.4"

dev_log = Logger("REACTIVE DEV", WARNING, "{name}: {msg}")


def log(msg):
    dev_log.debug(msg)


def set_dev_mode(dev=True):
    dev_log.level = DEBUG if dev else WARNING


if not anvil.is_server_side():
    from anvil.js.window import Function
else:

    def Function(*args):
        def wrapper(cb):
            return cb()

        return wrapper


# TODO - ideally we'd do something awesome here
# LIKE - check if the return value is a suspension
# and then wrapup the suspension with the current owner/observers or something
# Probably more hassle then it's worth
wrap_suspension = Function(
    "cb",
    """
const rv = cb();
if (rv instanceof Promise) {
    return {then: (x) => rv.then(x), catch: (e) => rv.catch(e)}
}
return rv;
""",
)


class Result:
    def __init__(self, value):
        self._value = value

    def unwrap(self):
        return self.value

    @property
    def value(self):
        return self._value


def wrap_compute(compute):
    def wrapper(*args, **kws):
        return wrap_suspension(lambda: Result(compute(*args, **kws)).value)

    return wrapper

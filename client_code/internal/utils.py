# SPDX-License-Identifier: MIT
#
# Copyright (c) 2023 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from .logging import DEBUG, INFO, WARNING, Logger

__version__ = "0.0.1"

dev_log = Logger("REACTIVE DEV", WARNING, "{name}: {msg}")


def log(msg):
    dev_log.debug(msg)


def set_dev_mode(dev=True):
    dev_log.level = DEBUG if dev else WARNING

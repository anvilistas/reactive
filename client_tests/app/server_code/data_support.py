# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import time

import anvil.server
from anvil.tables import app_tables

from . import models  # noqa: F401


@anvil.server.callable
def reset_counter():
    app_tables.counters.delete_all_rows()
    app_tables.owners.delete_all_rows()
    owner = app_tables.owners.add_row(name="Ada")
    return app_tables.counters.add_row(value=2, owner=owner)


@anvil.server.callable
def reset_reactive_counter():
    app_tables.reactive_counters.delete_all_rows()
    return app_tables.reactive_counters.add_row(value=2)


@anvil.server.callable
def get_counter():
    return app_tables.counters.get()


@anvil.server.callable
def get_counter_value():
    return app_tables.counters.get()["value"]


@anvil.server.callable
def echo_counter(counter):
    return counter


@anvil.server.callable
def create_owner(name):
    return app_tables.owners.add_row(name=name)


@anvil.server.callable
def update_counter(counter, value):
    counter["value"] = value
    counter.save()
    return counter


@anvil.server.callable
def delayed_value(value, delay_ms=20):
    time.sleep(delay_ms / 1000)
    return value


@anvil.server.callable
def delayed_error(message, delay_ms=20):
    time.sleep(delay_ms / 1000)
    raise RuntimeError(message)

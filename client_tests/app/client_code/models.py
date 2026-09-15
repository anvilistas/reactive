# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil.tables import app_tables
from anvil_reactive.main import reactive_class


class OwnerModel(app_tables.owners.Row, attrs=True, client_writable=True):
    pass


class CounterModel(
    app_tables.counters.Row,
    attrs=True,
    buffered=True,
    client_writable=True,
):
    @property
    def doubled(self):
        return self.value * 2

    @property
    def owner_name(self):
        return self.owner.name


@reactive_class
class ReactiveCounterModel(
    app_tables.reactive_counters.Row,
    attrs=True,
    buffered=True,
    client_writable=True,
):
    pass

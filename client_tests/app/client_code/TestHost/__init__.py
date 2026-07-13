# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from ._anvil_designer import TestHostTemplate


class TestHost(TestHostTemplate):
    def __init__(self, **properties):
        self.init_components(**properties)
        self._suite_started = False

    def form_show(self, **event_args):
        if self._suite_started:
            return
        self._suite_started = True

        from ..runner import run

        run(self)

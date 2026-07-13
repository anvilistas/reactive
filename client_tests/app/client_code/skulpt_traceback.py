# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

from anvil.js import window

_capture = window.Function(
    "callback",
    """
    try {
      callback();
    } catch (error) {
      const type = error && (error.tp$name || error.name) || "Exception";
      const value = error && error.args && error.args.v && error.args.v[0];
      const message = value && value.v !== undefined
        ? value.v
        : String(error);
      const frames = error && error.traceback || [];
      const lines = [`${type}: ${message}`];
      for (const frame of frames) {
        lines.push(`  at ${frame.filename}:${frame.lineno}`);
      }
      return lines.join("\\n");
    }
    return null;
    """,
)


def format_exception(error):
    def reraise():
        raise error

    return _capture(reraise)

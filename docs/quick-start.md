---
title: Quick start
weight: -9.8
---

# Build a reactive counter

In this guide, you'll store a count in a Form and bind it to a Label. Every time
the count changes, Anvil Reactive will update the Label for you.

## Build the Form

Create a Form named `CounterForm`. Add:

- a Label named `count_label`;
- a Button named `add_button` with the text `Add one`.

## Add a signal

Open the Form's Python code. Add a `count` signal, then bind the Label's `text`
property to it after the Form components have been created:

```python
from anvil import *

from ._anvil_designer import CounterFormTemplate
from anvil_reactive.main import bind, signal


class CounterForm(CounterFormTemplate):
    count = signal(0)

    def __init__(self, **properties):
        super().__init__(**properties)
        bind(
            self.count_label,
            "text",
            lambda: f"Count: {self.count}",
        )

    @handle("add_button", "click")
    def add_button_click(self, **event_args):
        self.count += 1
```

Run the app and click **Add one**. The event handler changes `self.count`, and
the Label updates automatically.

## What happened?

`signal(0)` creates a value that Reactive can watch. `bind()` reads that value
when it sets the Label text, so Reactive knows to update the Label whenever the
count changes.

The binding follows the Label's page lifetime. It updates while the component is
on the page, stops after the component is removed, and catches up with the latest
count if the component is added again.

Next, read [How automatic updates work](tracking.md) or learn when to use a
[reactive class](reactive-classes.md).

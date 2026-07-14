---
title: Component binding and write-back
weight: -9.3
---

# Keep component properties in sync

Use `bind()` to update an Anvil component property from reactive state. Use
`writeback()` when changes made in the component should also update that state.

When an app uses Anvil Reactive for state, prefer these functions for new
component bindings. They update from the same state as your computed values and
effects, and they stop and start with the component's page lifetime.

Existing native Anvil Data Bindings remain compatible and do not need to be
migrated just because Reactive is installed.

## Update a component from state

Call `bind()` after the Form has created its components:

```python
def __init__(self, **properties):
    super().__init__(**properties)

    bind(
        self.count_label,
        "text",
        lambda: f"Count: {self.state.count}",
    )
```

You can also bind directly to an object attribute or a dictionary key:

```python
bind(self.name_label, "text", self.state, "name")
bind(self.status_label, "text", self.state_dict, "status")
```

`bind()` sets the component property immediately. Later updates run while the
component is on the page, stop when it is removed, and catch up with the latest
state if it is added again.

Set up each binding once, normally in the Form's `__init__`. Calling `bind()` or
`writeback()` again installs another binding; it does not replace the earlier
one. In particular, do not call either function from a property setter that may
run more than once.

## Update state from a component

`writeback()` includes the one-way behavior of `bind()` and writes the component
property back when one of the chosen events fires:

```python
from anvil_reactive.main import writeback

writeback(
    self.name_box,
    "text",
    self.state,
    "name",
    "change",
)
```

After the TextBox raises its `change` event, `self.state.name` contains the new
text. A `change` handler added afterward can read the updated state.

Use a getter and setter when the value needs conversion or validation. You can
also listen for more than one event:

```python
writeback(
    self.name_box,
    "text",
    lambda: self.state.name,
    lambda value: setattr(self.state, "name", value.strip()),
    ("change", "pressed_enter"),
)
```

The event is part of the interaction design. For example, `change` writes after
the user commits an edit; an event that fires for each keystroke writes more
often.

## Edit a buffered Model Class

A reactive, buffered Data Table Model Class can be used directly as a Form's
editing state. This example writes the TextBox value to the model on `change`
and enables Save while the model has buffered changes:

```python
from anvil_reactive.main import bind, writeback


class BookForm(BookFormTemplate):
    def __init__(self, book, **properties):
        super().__init__(**properties)
        self.book = book

        writeback(self.title_box, "text", self.book, "title", "change")
        bind(
            self.save_button,
            "enabled",
            lambda: bool(self.book.buffered_changes),
        )

    def save_button_click(self, **event_args):
        self.book.save()

    def cancel_button_click(self, **event_args):
        self.book.reset()
```

`writeback()` also performs the initial state-to-component update. Calling
`reset()` restores both the buffered model and the bound components. The Model
Class must be [made reactive](reactive-classes.md#make-a-model-class-reactive)
for later changes to update the Form.

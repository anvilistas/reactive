---
title: Computed values and effects
weight: -9.5
---

# Calculate values and run automatic code

Use a computed value when one value can be calculated from other state. Use an
effect when a state change should run code, such as updating several components
or calling another API.

For a single component property, [`bind()`](component-bindings.md) is usually the
simpler choice.

## Calculate a value from other state

Apply `computed` outside `property`:

```python
from anvil_reactive.main import computed, reactive_class


@reactive_class
class OrderState:
    def __init__(self):
        self.price = 10
        self.quantity = 2

    @computed
    @property
    def total(self):
        return self.price * self.quantity
```

Read `order.total` like any other property. Reactive remembers the result until
`price` or `quantity` changes.

A method decorated with `@computed` but not `@property` is also read as an
attribute, without parentheses.

Computed values should calculate and return a value. Use an effect for code that
changes something outside the state object.

## Run code when state changes

An effect runs once when Reactive sets it up, watches the reactive values it
reads, and runs again after one of those values changes:

```python
from anvil_reactive.main import effect


class OrderForm(OrderFormTemplate):
    @effect
    def update_order_summary(self):
        self.total_label.text = f"Total: {self.order.total}"
        self.item_count_label.text = len(self.order.items)
```

An effect method is still an ordinary callable method. You can call it directly
when you need to run it immediately; Reactive manages its automatic runs.

## Effects on Forms and components

An effect declared on an Anvil component follows that component's page
lifetime:

- It waits until the component is added to the page before its first automatic
  run.
- It responds to state changes while the component is on the page.
- It continues to run if `visible` is set to `False` but the component remains
  on the page.
- It stops when the component is removed.
- If the component is added again, the effect starts again with the latest
  state.

This lets a Form own its UI updates without continuing to update after the Form
has been closed or replaced.

## Refresh an imperative component

Some components expose methods such as `set_data()` or `refresh()` instead of a
property that can be bound. A small version signal can tell an effect that the
component's external data is stale:

```python
from anvil_reactive.main import effect, signal


class ResultsStore:
    version = signal(0)

    def mark_changed(self):
        self.version += 1


class ResultsForm(ResultsFormTemplate):
    @effect
    def refresh_table(self):
        _ = self.store.version
        self.results_table.clear_cache()
        self.results_table.set_data()
```

Call `mark_changed()` after a successful save, delete, or refresh. The signal
does not need to contain the table data; it only connects a change in your app
to the component's imperative update API. The `_ = self.store.version` line is
the read that makes the effect depend on that signal. Because the effect belongs
to the Form, it runs only while that Form is on the page.

`render_effect` remains available for existing apps and currently behaves like
`effect`. Prefer `effect` for new code.

## Create an effect outside a class

Use `create_effect()` when an effect does not belong to an object:

```python
from anvil_reactive.main import create_effect


@create_effect
def report_status():
    print(state.status)
```

When an object or component should control the effect's lifetime, prefer an
`@effect` method.

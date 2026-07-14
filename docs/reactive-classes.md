---
title: Signals and reactive classes
weight: -9.6
---

# Store reactive state

Use a signal when you want to choose individual values for Reactive to watch.
Use a reactive class when most of an object's attributes are state.

## Choose individual values with `signal()`

Declare signals on a class. Each instance gets its own value:

```python
from anvil_reactive.main import signal


class SearchState:
    query = signal("")
    results = signal(default_factory=list)
```

Use `default_factory` for lists, dictionaries, and other mutable defaults. This
gives each instance a separate value.

## Make every attribute reactive

Use `reactive_class` when the attributes you set on an object should be watched
automatically:

```python
from anvil_reactive.main import reactive_class


@reactive_class
class CartState:
    def __init__(self):
        self.items = []
        self.discount = 0
```

This works with ordinary attributes, slots, inherited classes, and attributes
added later. Plain dictionaries and lists assigned to the object become
[reactive collections](collections.md).

You can inherit from `Reactive` instead of adding the decorator:

```python
from anvil_reactive.main import Reactive


class CartState(Reactive):
    def __init__(self):
        self.items = []
```

## Make a Model Class reactive

If you control a Data Table Model Class, apply `reactive_class` to the class
itself:

```python
from anvil.tables import app_tables
from anvil_reactive.main import reactive_class


@reactive_class
class Book(
    app_tables.books.Row,
    attrs=True,
    buffered=True,
    client_writable=True,
):
    pass
```

Reactive can then watch the Model's attributes, custom properties, linked rows,
and `buffered_changes`. This is useful for an editing Form that should enable its
Save button when the row changes. See [Edit a buffered Model
Class](component-bindings.md#edit-a-buffered-model-class) for the complete Form
pattern.

## Make an existing object reactive

Use `reactive_instance()` when another API created the object and you cannot
decorate its class. For example, you can make a Data Table Model instance
reactive:

```python
from anvil.tables import app_tables
from anvil_reactive.main import reactive_instance

counter = reactive_instance(app_tables.counter.get())
```

Reactive can then watch values read through attributes, item access, custom
properties, and linked rows. Updates to that object after a server call can also
update code that uses it.

!!! warning

    Calling `reactive_instance()` on one object also changes the behavior of
    other objects created from the same class. This is particularly important
    for Data Table Model Classes. Use `reactive_class` for classes you control,
    and do not assume that adapting one Model instance is isolated from the
    others.

Built-in values and Anvil base types that cannot be adapted are returned
unchanged.

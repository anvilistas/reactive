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
itself. Create a `books` table with a text column named `title`, then define the
class in a Module named `models`:

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

Import `models` from your startup Form and server code before fetching rows.
Anvil uses that import to register the class for the table. Configure the
table's [client access](https://anvil.works/docs/data-tables/model-classes/client-writable)
to allow the edits your app needs; the decorator does not grant access.

Reactive can then watch the Model's attributes, custom properties, linked rows,
and `buffered_changes`. This is useful for an editing Form that should enable its
Save button when the row changes. See [Edit a buffered Model
Class](component-bindings.md#edit-a-buffered-model-class) for the complete Form
pattern.

## Make an existing object reactive

Use `reactive_instance()` when another API created the object and you cannot
decorate its class:

```python
from anvil_reactive.main import reactive_instance

# existing_object was created by another library.
state = reactive_instance(existing_object)
```

Reactive can then watch supported instance attributes and values read by its
properties. For Data Tables, prefer the decorated Model Class above.

!!! warning

    Calling `reactive_instance()` on one object also changes the behavior of
    other objects created from the same class. This is particularly important
    for Data Table Model Classes. Use `reactive_class` for classes you control,
    and do not assume that adapting one Model instance is isolated from the
    others.

Built-in values and Anvil base types that cannot be adapted are returned
unchanged.

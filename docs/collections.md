---
title: Reactive collections
weight: -9.4
---

# React to changes inside dictionaries and lists

A normal signal can tell Reactive when you replace a complete value. A reactive
dictionary or list can also tell Reactive when you change an item inside the
collection.

## Use a reactive dictionary

Create a dictionary with `reactive_dict`:

```python
from anvil_reactive.main import reactive_dict

state = reactive_dict({
    "user": {"name": "Ada"},
    "filters": [],
})
```

Plain dictionaries and lists inside it are made reactive automatically.

Reactive can watch:

- one key, including a key that is currently missing;
- membership checks and `get()`;
- iteration, keys, values, items, length, and whether the dictionary is empty;
- assignment, deletion, `update()`, `setdefault()`, `pop()`, and `clear()`.

If a binding reads only `state["user"]`, changing an unrelated existing key does
not update that binding. Code that iterates over the dictionary updates when its
contents change.

## Use a reactive list

Create a list with `reactive_list`:

```python
from anvil_reactive.main import reactive_list

tasks = reactive_list(["write docs", "run tests"])
tasks.append("publish")
tasks.sort()
```

Reactive can watch items, slices, iteration, length, and whether the list is
empty. Assignment, deletion, `append()`, `extend()`, `insert()`, `remove()`,
`pop()`, `clear()`, sorting, and in-place addition or multiplication trigger the
code that uses the relevant list values.

Concatenation and slicing create a normal Python list. Wrap the result in
`reactive_list()` if changes inside the new list should also be watched.

## Pass a collection to server code

Server code receives a reactive dictionary or list as an ordinary `dict` or
`list`. If that value is returned to client code, it is restored as a reactive
collection.

As with other values passed between client and server code, do not rely on it
being the same Python object after the round trip.

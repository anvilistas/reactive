---
title: Reactive collections
weight: -9.4
---

# React to changes inside dictionaries and lists

A reactive dictionary or list lets bindings and effects watch changes inside
the collection. Plain dictionaries and lists assigned to a signal or reactive
object are wrapped automatically. Use `reactive_dict()` or `reactive_list()`
when you need a standalone reactive collection.

## Use a reactive dictionary

Create a dictionary with `reactive_dict`:

```python
from anvil_reactive.main import reactive_dict

state = reactive_dict(
    {
        "user": {"name": "Ada"},
        "filters": [],
    }
)
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

Iteration and slices track changes to the list's contents and order. Reading
`len(tasks)` tracks structural changes; `bool(tasks)` tracks whether it is empty.

Reading one index tracks assignment to that item, but can miss an insertion,
deletion, or sort that moves a different item into its position. If a binding
needs the current first item, iterate before selecting it:

```python
from anvil_reactive.main import bind

bind(self.first_task_label, "text", lambda: next(iter(tasks), "No tasks"))
```

For another position, use `list(tasks)[index]`. The iteration tracks structural
changes as well as item values.

Concatenation and slicing create a normal Python list. Wrap the result in
`reactive_list()` if changes inside the new list should also be watched.
Concatenation itself does not track its inputs; use `list(tasks) + extra_tasks`
inside a computed value when changes to `tasks` should recalculate the result.

## Pass a collection to server code

Server code receives a reactive dictionary or list as an ordinary `dict` or
`list`. Returning it to the client does not restore reactivity automatically.
Wrap the response when you need to track later edits:

```python
import anvil.server
from anvil_reactive.main import reactive_list

tasks = reactive_list(anvil.server.call("get_tasks"))
```

Assigning the response to a signal or an attribute of a reactive object also
wraps plain collections automatically.

As with other values passed between client and server code, do not rely on it
being the same Python object after the round trip.

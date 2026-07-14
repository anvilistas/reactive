---
title: How automatic updates work
weight: -9.7
---

# How automatic updates work

Anvil Reactive watches which values your bindings, computed values, and effects
read. When one of those values changes, Reactive updates only the code that used
it.

You do not need to maintain a separate list of dependencies.

## Reactive watches the values you read

Suppose a Form stores a quantity and a note:

```python
from anvil_reactive.main import bind, reactive_dict

self.state = reactive_dict({"quantity": 1, "note": ""})

bind(
    self.quantity_label,
    "text",
    lambda: f"Quantity: {self.state['quantity']}",
)
```

The binding reads `quantity`, so changing that key updates the Label. Changing
`note` does not update this binding because the binding did not read it.

## The values being watched can change

A binding can choose which value to read:

```python
bind(
    self.value_label,
    "text",
    lambda: (
        self.state["primary"]
        if self.state["use_primary"]
        else self.state["fallback"]
    ),
)
```

If `use_primary` changes, the binding runs again and watches the newly selected
value. A value that is no longer used stops triggering that binding.

## Several changes are grouped together

If an event handler changes several reactive values, Reactive groups the
resulting work. Your bindings and effects update after the current handler has
finished instead of updating after every assignment.

Setting a string or number to the value it already contains does not cause an
update. If you need changes inside a dictionary or list to trigger updates, use
a [reactive collection](collections.md).

## Automatic updates run in client code

Reactive watches values in Anvil client code. Server code receives normal
serialized values and does not become reactive. If an effect waits for a server
call, there is an additional rule about which values are watched; see
[Server calls inside effects](server-calls.md).

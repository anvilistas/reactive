---
title: Server calls inside effects
weight: -9.2
---

# Use server calls safely inside effects

Most bindings and effects finish immediately. An effect can also call a server
function or wait for browser work. While it waits, the rest of your app can keep
responding to the user.

Anvil calls this pause in client Python a *suspension*. You do not need to resume
the function yourself, but you do need to know which state changes will run the
effect again and what happens if two runs overlap.

## Read the state you need before waiting

Reactive watches values that an effect reads before it first has to wait:

```python
@effect
def load_customer(self):
    customer_id = self.customer_id
    show_email = self.show_email

    customer = anvil.server.call("get_customer", customer_id)

    self.name_label.text = customer["name"]
    self.email_label.visible = show_email
```

After this run has finished, changing `customer_id` or `show_email` can run the
effect again. If the effect first read `show_email` after the server call
returned, changing it would not run this effect. Do not rely on a change made
while the server call is still waiting to start a new run; the next section
shows a safer pattern for rapidly changing input.

Put every reactive value that should trigger the effect into a local variable
before the first operation that might wait. This rule applies to any operation
that pauses client Python, not only `anvil.server.call()`.

The wait may be hidden inside a helper. This order is fragile if
`initialise()` sometimes calls the server:

```python
def search(self):
    self.initialise()
    version = self.version  # Too late if initialise() had to wait.
    return self.view.search()
```

Read the trigger first:

```python
def search(self):
    version = self.version
    self.initialise()
    return self.view.search()
```

Where possible, load data explicitly in an event handler or page-lifecycle
method and keep computed values synchronous. A property that looks like a read
but sometimes loads from the server is difficult to reason about.

The function can wait more than once and will continue in order. Errors raised
after it resumes still appear through Anvil's normal error handling.

## Do not expect an older request to be cancelled

Suppose an effect searches the server whenever a user changes some text. If the
user types again while the first search is waiting, both searches may complete.
The older result is not automatically cancelled and may arrive last.

For user actions that can happen quickly, an event handler with a request number
makes the intended behavior explicit:

```python
def __init__(self, **properties):
    super().__init__(**properties)
    self._search_request = 0

@handle("search_box", "change")
def search_box_change(self, **event_args):
    self._search_request += 1
    request = self._search_request
    query = self.search_box.text

    results = anvil.server.call("search", query)

    if request != self._search_request:
        return

    self.results_grid.items = results
```

This ignores an older result if the user has started another search in the
meantime.

!!! warning

    Removing a Form does not cancel work that is already waiting. Do not rely on
    a component's removal to prevent the rest of an effect or event handler from
    running.

For state that changes synchronously, bindings, computed values, and effects can
manage updates directly. For a user-driven workflow that waits for the server,
an event handler is often easier to reason about.

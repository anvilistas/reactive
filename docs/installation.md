---
title: Installation
weight: -9.9
---

# Install Anvil Reactive

Add Anvil Reactive to an Anvil app as a third-party dependency, then import its
public API from `anvil_reactive.main` in client code.

## Add the dependency

In the Anvil Editor:

1. Open **App Browser > Dependencies**.
2. Click **Add Dependency**.
3. Enter the third-party dependency ID `N7KFE4YBWMGWJ5OX`.
4. Choose a tagged version so your app does not change unexpectedly.

You can also clone the
[GitHub repository](https://github.com/anvilistas/reactive) into your Anvil
account and add that app as a dependency.

## Import the API

Import only the names you need:

```python
from anvil_reactive.main import effect, signal
```

Anvil Reactive's dependency tracking is intended for browser code.
`reactive_class()` and `reactive_instance()` are no-ops on the server, while
reactive dictionaries and lists serialize as normal Python collections for
server calls.

Continue with the [quick start](quick-start.md).

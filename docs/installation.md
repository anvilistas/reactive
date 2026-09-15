---
title: Installation
weight: -9.9
---

# Install Anvil Reactive

Add Anvil Reactive to an Anvil app as a third-party dependency, then import its
public API from `anvil_reactive.main` in client code.

## Add the dependency

In the Anvil Editor:

1. Open **Settings > Dependencies**.
2. Choose **Third Party**.
3. Enter the third-party dependency ID `N7KFE4YBWMGWJ5OX`.
4. Choose a tagged version so your app does not change unexpectedly.

See Anvil's [dependency guide](https://anvil.works/docs/deployment/dependencies)
for help choosing a version.

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

---
title: Anvil Reactive
weight: -10
---

# Keep your Anvil app in sync with its state

Anvil Reactive updates your app when its Python state changes. You describe the
relationship between a value and the parts of your app that use it; Reactive
then keeps those parts up to date.

This is useful when several components use the same state, or when you would
otherwise need to call refresh methods from several event handlers.

## Start here

1. [Install Anvil Reactive](installation.md) as a third-party dependency.
2. [Build a reactive counter](quick-start.md) to update a Label from a value.
3. Read [How automatic updates work](tracking.md) before building more complex
   state.

## What do you want to do?

- Store changing state with [signals and reactive classes](reactive-classes.md).
- Calculate values from other state with
  [computed values](computed-and-effects.md#calculate-a-value-from-other-state).
- Run code automatically when state changes with
  [effects](computed-and-effects.md#run-code-when-state-changes).
- React to changes inside [dictionaries and lists](collections.md).
- Keep Anvil component properties in sync with
  [`bind()` and `writeback()`](component-bindings.md).

Reactive updates happen in client code. If an effect calls the server or waits
for other work, read [Server calls inside effects](server-calls.md) before relying
on its update order.

The [API reference](api-reference.md) lists the complete public interface.

## Based on Solid Signals

Anvil Reactive follows a specific version of Solid Signals. When the project
adopts a different Solid Signals version, Anvil Reactive's own version is bumped
as well. Pin a tagged Anvil Reactive version so your app continues to use the
same behavior.

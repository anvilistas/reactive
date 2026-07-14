---
title: API reference
weight: -9.1
---

# API reference

Use this page to look up the complete public interface. If you are choosing a
pattern for new code, begin with the [documentation overview](index.md).

Import public names from `anvil_reactive.main`.

## State

`signal(default=None, *, default_factory=...)`
: Declares an explicitly reactive class attribute. `default_factory` is called
  once for each instance when its value is first read.

`reactive_class(cls)`
: Class decorator that makes instance attributes reactive. Supports normal
  instance dictionaries, slots, and inheritance. It is a no-op in server code.

`Reactive`
: Empty convenience base class already decorated with `reactive_class`.

`reactive_instance(obj)`
: Makes a supported existing client object reactive and returns the same object.
  Calling it can also make other objects from the same class reactive, so the
  change is not isolated to that instance. Unsupported built-in and Anvil base
  types are returned unchanged.

## Derived values and effects

`computed(fn=None, *, init_value=...)`
: Method decorator for a cached derived value. Combine it with `@property`, with
  `@computed` outermost, or read the decorated method as an attribute. Reactive
  reads made during evaluation become dependencies.

`effect(fn=None, *, init_value=...)`
: Method decorator for automatic work. It runs initially and reruns after a
  dependency changes. On an Anvil component, its owner follows the component's
  page-added/page-removed lifecycle. The decorated method remains callable.

`render_effect(fn=None, *, init_value=...)`
: Compatibility effect decorator. It currently has the same behavior and
  component lifecycle as `effect`; prefer `effect` for new code.

`create_effect(fn, initialValue=..., name=None)`
: Low-level callable form used as `@create_effect` or called with a function.
  Prefer `effect` when an instance should own the lifetime. If `initialValue` is
  supplied, it is passed to executions as the previous value.

## Collections

`reactive_dict(*args, **kwargs)`
: Reactive `dict` implementation. Tracks key values and structural operations,
  wraps nested plain dictionaries and lists, and serializes as a normal
  dictionary on the server.

`reactive_list(iterable=())`
: Reactive `list` implementation. Tracks item and structural operations, wraps
  nested plain dictionaries and lists, and serializes as a normal list on the
  server.

## Components

`bind(component, property_name, getter)`
`bind(component, property_name, object_or_dict, attribute_or_key)`
: Immediately sets a component property and keeps it synchronized from a getter,
  object attribute, or dictionary key while the component is mounted.

`writeback(component, property_name, object_or_dict, attribute_or_key, events=())`
`writeback(component, property_name, getter, setter, events=())`
: Adds one-way rendering plus event-driven updates from the component property
  to the source. `events` can be one event name or an iterable of names.

## Metadata

`__version__`
: The installed Anvil Reactive version string. The project bumps this version
  whenever it changes the Solid Signals version used as its implementation
  baseline.

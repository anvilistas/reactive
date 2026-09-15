# Next major version planning

This is an internal planning note, not user-facing documentation. Nothing here
is a committed interface or implementation design.

## Start gate

Wait for a stable Solid Signals 2.0 release before starting the port. Async,
ownership, cleanup, and pending-work semantics must be stable enough that we are
not designing against a moving beta target.

Before implementation starts:

- record the exact upstream release and commit we will follow;
- review its async and ownership behaviour against our client characterization
  suite;
- decide which known gaps become supported contracts;
- measure the client payload so the rewrite has a useful size baseline.

Changing the Solid Signals version on which Reactive is based should cause an
Anvil Reactive version bump. Breaking upstream behaviour requires a major bump.

## Direction

- A from-scratch rewrite is acceptable.
- Keep the client payload small. Adapters and test infrastructure should remain
  server-side or outside the production dependency wherever possible.
- Use the runtime-v3 client characterization suite as the compatibility boundary.
  Extract its reusable harness into a dependency later; keep Reactive-specific
  scenarios here.
- Prefer a small, isolated Skulpt integration seam. Do not expose suspensions or
  other Skulpt implementation details through the public API.
- A major release may remove compatibility that no longer earns its complexity.

## Async behaviour to decide

The current documented contract tracks reactive reads made before the first
wait. Reads after execution resumes are not dependencies. Sequential waits can
complete, but they do not extend dependency tracking.

Revisit this after Solid Signals is stable and decide whether computations
should be async-aware by default. In particular, resolve the existing expected
failures for:

- a newer async execution superseding an older result;
- a dependency changing while the first execution is pending;
- disposal invalidating pending completion;
- overlapping pending work preserving dependency-reconciliation state.

Do not assume that adopting Solid's implementation automatically resolves the
Python/Skulpt execution model. Keep any required suspension detection internal.

## `reactive_instance`

Prefer `@reactive_class` for classes the app controls, including Data Table Model
Classes. Keep `reactive_instance()` available for objects created by frameworks
or other libraries unless the major-version design supplies an equivalent.

`reactive_instance()` currently patches the object's class because Python
attribute hooks and descriptors are type-level behaviour. Consider making the
installed hooks active only for instances explicitly passed to
`reactive_instance()`:

- Skulpt's FFI wraps non-simple Python objects and caches those wrappers in a
  JavaScript `WeakMap`, so a JavaScript `WeakSet` may provide an instance marker
  without retaining objects;
- Python lists and dictionaries use different FFI conversion paths, so identity
  must be characterized for every supported object shape rather than assumed;
- explicitly decorated reactive classes should bypass any per-instance check;
- test the cost of a JavaScript membership check on attribute reads before
  adopting this design.

Anvil Row internals such as `_anvil` are private. They can help explain current
behaviour, but the design and tests must depend only on observable Model/Row
behaviour: reads, edits, buffering, reset, save, server updates, and bindings.

## Component lifecycle

Decide whether `effect` created on a Component should always belong to that
Component's add/remove lifecycle. If that gives `effect` the useful behaviour of
`render_effect`, consider removing `render_effect` rather than maintaining two
names for the same primitive.

## Completion criteria

- Existing contract cases either pass or have an explicitly agreed breaking
  change.
- Supported async behaviour has contract coverage; unsupported behaviour has a
  named expected failure or documented limitation.
- Model Classes work through public Anvil behaviour without treating private Row
  storage as an interface.
- Client/server boundaries and the production dependency payload have been
  reviewed deliberately.
- The public interface and migration notes match the implementation actually
  shipped.

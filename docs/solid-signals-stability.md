# Solid Signals stability assessment

Assessment date: 2026-07-13

## Conclusion

`@solidjs/signals` 2.0 is not yet a stable target for a complete behavioral port. Its synchronous reactive foundation and main primitive names are comparatively mature, but async, transition, optimistic, boundary, and error semantics are still changing materially.

It is reasonable to begin against a pinned snapshot if Anvil Reactive deliberately limits its initial contract. The recommended reference is `2.0.0-beta.17` at Solid commit `a51cac19`, with later upstream changes reviewed and adopted intentionally rather than followed continuously.

## Evidence

- The [official README](https://github.com/solidjs/solid/blob/next/packages/solid-signals/README.md) labels the package Beta and warns that breaking changes remain possible.
- The local `next` checkout identifies the package as `2.0.0-beta.17`; that release was committed on 2026-07-10.
- Eleven beta versions were published between beta.7 on 2026-04-16 and beta.17 on 2026-07-10.
- The package received 91 commits from 2026-06-01 through the beta.17 snapshot, including 65 during July 1–10.
- The [official changelog](https://github.com/solidjs/solid/blob/next/packages/solid-signals/CHANGELOG.md) records recent changes to effect error timing, async and pending behavior, optimistic semantics, error-halting behavior, cleanup ordering, refresh behavior, and public surface area.
- Between beta.7 and beta.17, `packages/solid-signals` changed across 83 files, with approximately 16,380 insertions and 1,356 deletions in the local Solid history.

## Stability by area

| Area | Assessment |
| --- | --- |
| Signals, dependency tracking, memos | Reasonably mature, suitable for a pinned port |
| Ownership and disposal | Mostly mature, but cleanup ordering has still changed during beta |
| Basic effect scheduling | Suitable for characterization and a pinned implementation |
| Async computations and pending state | Moving target |
| Transitions and lane entanglement | Moving target |
| Optimistic signals and stores | Actively redesigned during recent betas |
| Loading, reveal, and error boundaries | Still receiving semantic fixes |
| Stores and reconcile utilities | Broad and still receiving correctness fixes |

## Recommendation for Anvil Reactive

Start with a small pinned contract: signals, computed values/memos, effects, ownership/disposal, equality, and deterministic scheduling. Keep the Skulpt runtime seam small and test it separately. Treat advanced async, actions, optimistic state, transitions, and boundaries as later capability slices whose semantics must be rechecked against the then-current Solid release before implementation.

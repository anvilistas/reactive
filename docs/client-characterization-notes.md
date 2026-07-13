# Client characterization notes

These notes turn three usage areas into proposed runtime-v3 characterization cases. They describe what the current source appears to intend; where the result is uncertain, the test should record the observed behavior rather than force a production change.

## Data Table models as reactive instances

The forum's original Data Tables example predates Model Classes. It wraps an ordinary row, reads `counter_row["value"]` inside a `render_effect`, and passes the same row through a server call that updates it ([forum example](https://anvil.works/forum/t/anvil-reactive-add-reactivity-to-your-anvil-apps/19526#p-64837-example-usage-1)). Current Anvil Model Classes instead subclass `app_tables.<table>.Row`; `attrs=True` adds attribute access, and model instances retain the normal mapping API ([creating model classes](https://anvil.works/docs/data-tables/model-classes/creating)). Anvil also documents that a row passed through a server call has its client cache updated automatically ([Data Tables in code](https://anvil.works/docs/data-tables/data-tables-in-code)).

Exact model shape to exercise:

```python
class CounterModel(
    app_tables.counter.Row,
    attrs=True,
    buffered=True,
    client_writable=True,
):
    @property
    def doubled(self):
        return self.value * 2

counter = reactive_instance(app_tables.counter.get())
```

Characterize all of these separately:

- reads via `counter.value`, `counter["value"]`, and the `counter.doubled` property;
- client attribute and item assignment, buffered `save()` and `reset()`, and a server method updating the same row;
- whether a returned/rehydrated reference is the same reactive object and whether subsequent updates still notify;
- linked-row values and replacement of a linked row;
- calling `reactive_instance()` on one model followed by creating/fetching another instance of that model.

The last case matters because `reactive_instance()` currently calls `reactive_class(type(instance))`, so it mutates the class, not only the supplied instance ([Reactive source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_reactive_class.py#L179-L200)). It also wraps slot descriptors ([same source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_reactive_class.py#L80-L107)). This is potentially surprising for Model Classes: Anvil says models cannot hold arbitrary instance state, and their only state is Data Table columns ([model-class constraints](https://anvil.works/docs/data-tables/model-classes/creating#self-is-trustworthy)). Do not assume column updates notify until the browser test proves it; current Reactive instruments attributes/slots, while Data Table columns are owned by the Row implementation.

## Render effects and the screen lifecycle

The forum states that render effects run when a component is added to the screen ([forum example](https://anvil.works/forum/t/anvil-reactive-add-reactivity-to-your-anvil-apps/19526#p-64837-example-usage-1)). The implementation installs `x-anvil-page-added` and `x-anvil-page-removed` handlers, creates the component's reactive root on add, and disposes it on remove ([Reactive lifecycle source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L42-L73), [registration source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L108-L136)). `render_effect` and `effect` currently use the same effect creator; the component lifecycle supplies the render behavior ([source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L184-L189)).

Test this event sequence with an execution counter and a rendered value:

1. Construct the Form/component but do not add it: the decorated render effect should not have run.
2. Add it to an open Form: it should run initially and respond to signal changes.
3. Set `visible = False` while it remains mounted, then change the signal.
4. Remove it, then change the signal: it should no longer run.
5. Add it again: it should run with the latest value, exactly once, and resume updates.

The hidden step is intentionally distinct from removal. Anvil documents that `x-anvil-page-added` means mounted whether visible or not, while visibility uses `x-anvil-page-shown`/`x-anvil-page-hidden`; removal is the event after which no more page events occur until re-addition ([component lifecycle](https://anvil.works/docs/client/events/component-lifecycle)). On the current source, `visible=False` should therefore **not** pause effects. That wording is worth making explicit in later docs: “not on screen” means unmounted/removed, not merely hidden.

## `bind()` and `writeback()`

The forum's exact one-way shape is:

```python
bind(self.counter_label, "text", lambda: self.counter)
```

([forum example](https://anvil.works/forum/t/anvil-reactive-add-reactivity-to-your-anvil-apps/19526#p-64837-example-usage-1)). The public functions also accept an object plus attribute or a dict plus key. `writeback()` additionally accepts a setter and one event name or an iterable of event names ([implementation](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L233-L287)). Exact shapes to characterize:

```python
bind(label, "text", lambda: state.count)
bind(label, "text", state, "count")
bind(label, "text", state_dict, "count")

writeback(text_box, "text", state, "name", "change")
writeback(
    text_box,
    "text",
    lambda: state.name,
    lambda value: setattr(state, "name", value),
    ("change", "pressed_enter"),
)
```

For each shape, cover initial synchronization, source-to-component updates, unrelated signal isolation, event-to-source updates, removal, and re-addition. Compare event timing with native Anvil write-back: native Data Bindings write immediately before relevant event handlers run ([Data Bindings](https://anvil.works/docs/client/component-properties/data-bindings#two-way-data-bindings)); the Reactive test should verify its handler observes the updated source too.

Two source-level surprises deserve explicit cases:

- `bind()` performs an immediate, untracked render during setup, even before page addition; only subsequent reactive synchronization belongs to the mounted root ([source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L267-L287)). This differs from a decorated `render_effect`, whose component computation is created on page addition.
- Removal disposes reactive roots but does not unregister the event handler installed by `writeback()` ([source](https://github.com/anvilistas/reactive/blob/66f249de150b23d3e93bae9102fa040e4eeb11d8/client_code/main/_primitives.py#L261-L280)). Characterize whether an input event raised while unmounted still writes to the source, and whether repeated remove/add cycles create exactly one render computation and one write-back action.

These are good candidates for `contract` only after observing them in the real App Server. If they are useful but undesirable, record them as `known_gap` under the agreed broad meaning of “interesting unsupported behavior.”

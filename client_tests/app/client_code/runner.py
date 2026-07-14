# SPDX-License-Identifier: MIT
#
# Copyright (c) 2026 Anvilistas project team members listed at
# https://github.com/anvilistas/reactive/graphs/contributors
#
# This software is published at https://github.com/anvilistas/reactive

import json

import anvil
import anvil.server
from anvil.js import await_promise, window
from anvil_reactive.main import (
    bind,
    computed,
    create_effect,
    effect,
    reactive_class,
    reactive_dict,
    reactive_instance,
    render_effect,
    signal,
    writeback,
)

from .case_registry import CASES, contract, known_gap
from .models import CounterModel, OwnerModel, ReactiveCounterModel
from .reactive_reset import drain_before_reset, hard_reset, run_in_test_root
from .skulpt_traceback import format_exception

_RESET_PROBE = {}
_HOST = None
_RENDER_LOGS = {}
_PENDING_LOGS = {}
_sleep_promise = window.Function(
    "milliseconds",
    "return new Promise(resolve => setTimeout(resolve, milliseconds));",
)


@reactive_class
class _RenderEffectPanel(anvil.ColumnPanel):
    def __init__(self):
        super().__init__()
        self.value = 0
        _RENDER_LOGS[id(self)] = []

    @render_effect
    def record_render(self):
        _RENDER_LOGS[id(self)].append(self.value)


@reactive_class
class _EffectPanel(anvil.ColumnPanel):
    def __init__(self):
        super().__init__()
        self.value = 0
        _RENDER_LOGS[id(self)] = []

    @effect
    def record_effect(self):
        _RENDER_LOGS[id(self)].append(self.value)


@reactive_class
class _SuspendingEffectPanel(anvil.ColumnPanel):
    def __init__(self):
        super().__init__()
        self.value = 0
        _PENDING_LOGS[id(self)] = []

    @effect
    def record_effect(self):
        value = self.value
        anvil.server.call("delayed_value", None, 80)
        _PENDING_LOGS[id(self)].append(value)


@reactive_class
class _State:
    def __init__(self, value):
        self.value = value


def _render_log(panel):
    return _RENDER_LOGS[id(panel)]


def _sleep(milliseconds):
    await_promise(_sleep_promise(milliseconds))


def _flush_microtasks():
    await_promise(window.Promise.resolve())


def _reset_between_cases():
    drain_before_reset()
    if _HOST is not None:
        _HOST.clear()
    hard_reset()


def _run_case(case):
    _reset_between_cases()
    started = window.performance.now()
    try:
        details = run_in_test_root(case.fn)
    except Exception as error:
        return {
            "name": case.name,
            "classification": case.classification,
            "reason": case.reason,
            "status": "xfail" if case.classification == "known_gap" else "fail",
            "duration_ms": window.performance.now() - started,
            "error": f"{type(error).__name__}: {error}",
            "traceback": format_exception(error),
        }
    else:
        traceback = None
        if isinstance(details, dict):
            traceback = details.get("__harness_traceback__")
        return {
            "name": case.name,
            "classification": case.classification,
            "reason": case.reason,
            "status": "xpass" if case.classification == "known_gap" else "pass",
            "duration_ms": window.performance.now() - started,
            "error": None,
            "traceback": traceback,
        }


@contract
def _public_imports_work():
    assert callable(reactive_class)
    assert callable(computed)
    assert callable(signal)
    assert callable(reactive_dict)


@contract
def _reactive_class_updates_computed_values():
    @reactive_class
    class Counter:
        amount = signal(1)

        @computed
        @property
        def doubled(self):
            return self.amount * 2

    counter = Counter()
    assert counter.amount == 1
    assert counter.doubled == 2

    counter.amount = 4

    assert counter.amount == 4
    assert counter.doubled == 8


@contract
def _reactive_dict_wraps_nested_values():
    state = reactive_dict({"count": 1, "nested": {"enabled": True}})

    assert state["count"] == 1
    assert state["nested"]["enabled"] is True

    state["count"] = 2
    state["nested"]["enabled"] = False

    assert state["count"] == 2
    assert state["nested"]["enabled"] is False


@contract
def _suspending_case_is_awaited():
    result = await_promise(window.Promise.resolve("resumed"))
    assert result == "resumed"


@contract(fresh_page=True)
def _multiple_sequential_suspensions_resume_in_order():
    progress = ["before"]

    first = anvil.server.call("delayed_value", "first")
    progress.append(first)
    second = anvil.server.call("delayed_value", "second")
    progress.append(second)

    assert progress == ["before", "first", "second"]


@contract(fresh_page=True)
def _post_suspension_exception_reaches_the_caller():
    try:
        anvil.server.call("delayed_error", "after suspension")
    except Exception as error:
        traceback = format_exception(error)
    else:
        raise AssertionError("The suspended server error was not raised")

    assert "after suspension" in traceback
    assert "runner.py:" in traceback


@contract(fresh_page=True)
def _only_reads_before_first_suspension_are_tracked():
    state = reactive_dict({"before": 0, "after": 0})
    observed = []

    @create_effect
    def observe():
        before = state["before"]
        anvil.server.call("delayed_value", None)
        after = state["after"]
        observed.append((before, after))

    _sleep(100)
    observed.clear()

    state["before"] = 1
    _sleep(100)
    assert observed == [(1, 0)], repr(observed)

    state["after"] = 1
    _sleep(100)
    assert observed == [(1, 0)], repr(observed)


@known_gap(
    "A dependency change during the initial pending execution does not reliably "
    "schedule one execution for the new value",
    fresh_page=True,
)
def _dependency_change_while_first_execution_is_pending():
    state = reactive_dict({"value": 0})
    started = []

    def start_effect():
        @create_effect
        def observe():
            value = state["value"]
            started.append(value)
            anvil.server.call("delayed_value", None, 80)

    def change_dependency():
        state["value"] = 1

    window.setTimeout(start_effect, 0)
    window.setTimeout(change_dependency, 20)
    _sleep(300)

    assert started == [0, 1], repr(started)


@known_gap(
    "A newer async execution cannot supersede completion from an older value",
    fresh_page=True,
)
def _newer_async_execution_supersedes_older_result():
    state = reactive_dict({"value": 0})
    completed = []

    def start_effect():
        @create_effect
        def observe():
            value = state["value"]
            delay = 100 if value == 0 else 20
            anvil.server.call("delayed_value", None, delay)
            completed.append(value)

    def change_dependency():
        state["value"] = 1

    window.setTimeout(start_effect, 0)
    window.setTimeout(change_dependency, 20)
    _sleep(300)

    assert completed == [1], repr(completed)


@known_gap(
    "Removing a component does not invalidate completion of its pending effect",
    fresh_page=True,
)
def _disposal_invalidates_pending_completion():
    panel = _SuspendingEffectPanel()

    def mount():
        _HOST.add_component(panel)

    window.setTimeout(mount, 0)
    window.setTimeout(panel.remove_from_parent, 20)
    _sleep(300)

    assert _PENDING_LOGS[id(panel)] == [], repr(_PENDING_LOGS[id(panel)])


@known_gap(
    "Overlapping pending effects can duplicate executions or corrupt later "
    "dependency reconciliation",
    fresh_page=True,
)
def _pending_work_preserves_dependency_reconciliation():
    first = reactive_dict({"value": 0})
    second = reactive_dict({"value": 0})
    first_log = []
    second_log = []

    def start_first():
        @create_effect
        def observe_first():
            value = first["value"]
            anvil.server.call("delayed_value", None, 40)
            first_log.append(value)

    def start_second():
        @create_effect
        def observe_second():
            value = second["value"]
            anvil.server.call("delayed_value", None, 100)
            second_log.append(value)

    window.setTimeout(start_first, 0)
    window.setTimeout(start_second, 10)
    _sleep(300)
    first_log.clear()
    second_log.clear()

    first["value"] = 1
    _sleep(200)

    assert first_log == [1], repr(first_log)
    assert second_log == [], repr(second_log)


@contract
def _leave_a_queued_effect_for_reset():
    state = reactive_dict({"count": 0})
    observed = []

    @create_effect
    def observe():
        observed.append(state["count"])

    _flush_microtasks()
    state["count"] = 1
    _RESET_PROBE["state"] = state
    _RESET_PROBE["observed"] = observed

    assert observed == [0]


@contract
def _reset_discards_queued_effects():
    state = _RESET_PROBE["state"]
    observed = _RESET_PROBE["observed"]

    state["count"] = 2
    await_promise(window.Promise.resolve())

    assert observed == [0]


@contract
def _skulpt_traceback_is_reported():
    def traceback_probe():
        raise ValueError("traceback_probe")

    try:
        traceback_probe()
    except Exception as error:
        traceback = format_exception(error)

    assert "ValueError: traceback_probe" in traceback
    assert "runner.py:" in traceback
    return {"__harness_traceback__": traceback}


@contract
def _render_effect_waits_for_mount():
    panel = _RenderEffectPanel()
    assert _render_log(panel) == []

    _HOST.add_component(panel)

    assert _render_log(panel) == [0]


@contract
def _hidden_render_effect_remains_active():
    panel = _RenderEffectPanel()
    _HOST.add_component(panel)
    assert _render_log(panel) == [0]

    panel.visible = False
    panel.value = 1
    await_promise(window.Promise.resolve())

    assert _render_log(panel) == [0, 1]


@contract
def _removed_render_effect_pauses_and_restarts():
    panel = _RenderEffectPanel()
    _HOST.add_component(panel)
    assert _render_log(panel) == [0]
    _flush_microtasks()

    panel.remove_from_parent()
    panel.value = 1
    await_promise(window.Promise.resolve())
    assert _render_log(panel) == [0]

    _HOST.add_component(panel)
    assert _render_log(panel) == [0, 1]

    panel.value = 2
    await_promise(window.Promise.resolve())
    assert _render_log(panel) == [0, 1, 2]


@contract
def _component_effect_matches_render_effect_lifecycle():
    panel = _EffectPanel()
    assert _render_log(panel) == []

    _HOST.add_component(panel)
    assert _render_log(panel) == [0]
    _flush_microtasks()

    panel.remove_from_parent()
    panel.value = 1
    await_promise(window.Promise.resolve())
    assert _render_log(panel) == [0]

    _HOST.add_component(panel)
    assert _render_log(panel) == [0, 1]


@contract
def _component_roots_can_be_disposed_in_any_order():
    older = _EffectPanel()
    newer = _EffectPanel()
    _HOST.add_component(older)
    _HOST.add_component(newer)
    assert _render_log(older) == [0]
    assert _render_log(newer) == [0]
    _flush_microtasks()

    older.remove_from_parent()
    newer.remove_from_parent()
    older.value = 1
    newer.value = 1
    await_promise(window.Promise.resolve())

    assert _render_log(older) == [0], _render_log(older)
    assert _render_log(newer) == [0], _render_log(newer)


@contract
def _bind_lambda_syncs_across_lifecycle():
    state = _State("initial")
    label = anvil.Label(text="unset")
    bind(label, "text", lambda: state.value)
    assert label.text == "initial"

    _HOST.add_component(label)
    state.value = "mounted"
    await_promise(window.Promise.resolve())
    assert label.text == "mounted"

    label.remove_from_parent()
    state.value = "removed"
    await_promise(window.Promise.resolve())
    assert label.text == "mounted"

    _HOST.add_component(label)
    assert label.text == "removed"


@contract
def _bind_object_attribute_syncs():
    state = _State("initial")
    label = anvil.Label(text="unset")
    bind(label, "text", state, "value")
    assert label.text == "initial"

    _HOST.add_component(label)
    state.value = "updated"
    await_promise(window.Promise.resolve())

    assert label.text == "updated"


@contract
def _bind_dict_key_syncs():
    state = reactive_dict({"value": "initial"})
    label = anvil.Label(text="unset")
    bind(label, "text", state, "value")
    assert label.text == "initial"

    _HOST.add_component(label)
    state["value"] = "updated"
    await_promise(window.Promise.resolve())

    assert label.text == "updated"


@contract
def _writeback_object_attribute_updates_both_directions():
    state = _State("initial")
    text_box = anvil.TextBox(text="unset")
    writeback(text_box, "text", state, "value", "change")
    assert text_box.text == "initial"

    _HOST.add_component(text_box)
    state.value = "from source"
    await_promise(window.Promise.resolve())
    assert text_box.text == "from source"

    text_box.text = "from event"
    text_box.raise_event("change")
    assert state.value == "from event"


@contract
def _writeback_callable_accepts_multiple_events():
    state = _State("initial")
    text_box = anvil.TextBox(text="unset")
    writeback(
        text_box,
        "text",
        lambda: state.value,
        lambda value: setattr(state, "value", value),
        ("change", "pressed_enter"),
    )
    _HOST.add_component(text_box)

    text_box.text = "changed"
    text_box.raise_event("change")
    assert state.value == "changed"

    text_box.text = "entered"
    text_box.raise_event("pressed_enter")
    assert state.value == "entered"


@contract
def _writeback_updates_source_before_later_event_handlers():
    state = _State("initial")
    text_box = anvil.TextBox(text="unset")
    observed = []
    writeback(text_box, "text", state, "value", "change")

    def observe_source(**event_args):
        observed.append(state.value)

    text_box.add_event_handler("change", observe_source)
    _HOST.add_component(text_box)

    text_box.text = "changed"
    text_box.raise_event("change")

    assert state.value == "changed"
    assert observed == ["changed"]


@contract
def _writeback_does_not_duplicate_handlers_after_remount():
    state = _State("initial")
    text_box = anvil.TextBox(text="unset")
    writes = []

    def set_value(value):
        writes.append(value)
        state.value = value

    writeback(text_box, "text", lambda: state.value, set_value, "change")

    for _ in range(3):
        _HOST.add_component(text_box)
        _flush_microtasks()
        text_box.remove_from_parent()

    _HOST.add_component(text_box)
    text_box.text = "once"
    text_box.raise_event("change")

    assert writes == ["once"]


@known_gap("Writeback event handlers remain registered after component removal")
def _unmounted_writeback_event_is_ignored():
    state = _State("initial")
    text_box = anvil.TextBox(text="unset")
    writeback(text_box, "text", state, "value", "change")
    _HOST.add_component(text_box)
    _flush_microtasks()
    text_box.remove_from_parent()

    text_box.text = "unmounted"
    text_box.raise_event("change")

    assert state.value == "initial"


@contract
def _datatable_model_preserves_surface_and_linked_values():
    counter = anvil.server.call("reset_counter")

    assert isinstance(counter, CounterModel)
    assert isinstance(counter.owner, OwnerModel)
    assert counter.value == 2
    assert counter["value"] == 2
    assert counter.doubled == 4
    assert counter.owner.name == "Ada"
    assert counter.owner["name"] == "Ada"
    assert counter.owner_name == "Ada"


@contract
def _buffered_model_save_and_reset():
    counter = anvil.server.call("reset_counter")
    assert counter.buffered_changes == {}

    counter.value = 7
    assert counter.value == 7
    assert counter.buffered_changes == {"value": 7}
    counter.reset()
    assert counter.value == 2
    assert counter.buffered_changes == {}

    counter.value = 8
    counter.save()
    assert counter.buffered_changes == {}
    assert anvil.server.call("get_counter_value") == 8


@contract(fresh_page=True)
def _reactive_class_model_supports_buffered_editing():
    counter = anvil.server.call("reset_reactive_counter")
    assert isinstance(counter, ReactiveCounterModel)
    editor = anvil.TextBox(type="number")
    save_button = anvil.Button(enabled=False)

    writeback(editor, "text", counter, "value", "change")
    bind(save_button, "enabled", lambda: bool(counter.buffered_changes))
    _HOST.add_component(editor)
    _HOST.add_component(save_button)

    assert float(editor.text) == 2
    assert save_button.enabled is False

    editor.text = 7
    editor.raise_event("change")
    _flush_microtasks()

    assert counter.value == 7
    assert counter.buffered_changes == {"value": 7}
    assert save_button.enabled is True

    counter.reset()
    _flush_microtasks()

    assert float(editor.text) == 2
    assert counter.buffered_changes == {}
    assert save_button.enabled is False


@contract
def _server_round_trip_refreshes_same_model():
    counter = anvil.server.call("reset_counter")

    echoed = anvil.server.call("echo_counter", counter)
    assert isinstance(echoed, CounterModel)
    assert echoed.value == counter.value

    anvil.server.call("update_counter", counter, 6)
    assert counter.value == 6
    assert counter["value"] == 6

    fetched_again = anvil.server.call("get_counter")
    assert isinstance(fetched_again, CounterModel)
    assert fetched_again.value == 6


@known_gap("reactive_instance mutates the shared Model class, not only one row")
def _reactive_instance_does_not_mutate_model_class():
    counter = anvil.server.call("reset_counter")
    model_type = type(counter)
    assert not getattr(model_type, "__reactive_root__", False)

    assert reactive_instance(counter) is counter

    assert not getattr(model_type, "__reactive_root__", False)


@contract
def _reactive_model_attribute_updates_effect():
    counter = reactive_instance(anvil.server.call("reset_counter"))
    observed = []

    @create_effect
    def observe_value():
        observed.append(counter.value)

    counter.value = 3
    await_promise(window.Promise.resolve())

    assert observed == [2, 3]


@contract
def _reactive_model_property_updates_effect():
    counter = reactive_instance(anvil.server.call("reset_counter"))
    observed = []

    @create_effect
    def observe_doubled():
        observed.append(counter.doubled)

    counter.value = 5
    await_promise(window.Promise.resolve())

    assert observed == [4, 10]


@contract
def _reactive_model_item_updates_effect():
    counter = reactive_instance(anvil.server.call("reset_counter"))
    observed = []

    @create_effect
    def observe_value():
        observed.append(counter["value"])

    counter["value"] = 4
    await_promise(window.Promise.resolve())

    assert observed == [2, 4]


@contract
def _reactive_model_link_replacement_updates_effect():
    counter = reactive_instance(anvil.server.call("reset_counter"))
    observed = []

    @create_effect
    def observe_owner():
        observed.append(counter.owner.name)

    counter.owner = anvil.server.call("create_owner", "Grace")
    await_promise(window.Promise.resolve())

    assert observed == ["Ada", "Grace"]


@contract
def _server_model_update_notifies_effect():
    counter = reactive_instance(anvil.server.call("reset_counter"))
    observed = []

    @create_effect
    def observe_value():
        observed.append(counter.value)

    anvil.server.call("update_counter", counter, 9)
    await_promise(window.Promise.resolve())

    assert counter.value == 9
    assert observed == [2, 9]


def _publish_payload(payload):
    element = window.document.createElement("pre")
    element.id = "anvil-reactive-test-result"
    element.dataset.state = "done"
    element.textContent = json.dumps(payload)
    window.document.body.appendChild(element)


def _publish(results):
    status = (
        "pass"
        if all(case["status"] in ("pass", "xfail") for case in results)
        else "fail"
    )
    payload = {
        "status": status,
        "cases": results,
    }
    _publish_payload(payload)


def _discover():
    _publish_payload(
        {
            "status": "discovered",
            "cases": [
                {
                    "name": case.name,
                    "classification": case.classification,
                    "reason": case.reason,
                    "fresh_page": case.fresh_page,
                }
                for case in CASES
            ],
        }
    )


def run(host):
    global _HOST
    _HOST = host
    params = window.URLSearchParams(window.location.search)
    if params.has("discover"):
        _discover()
        return

    requested = params.get("case")
    if requested is not None:
        selected = [case for case in CASES if case.name == requested]
        if not selected:
            _publish_payload(
                {
                    "status": "fail",
                    "cases": [],
                    "error": f"Unknown client case: {requested}",
                }
            )
            return
    else:
        selected = [case for case in CASES if not case.fresh_page]

    _publish([_run_case(case) for case in selected])
    _reset_between_cases()

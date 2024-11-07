import anvil
from client_code._internal.effect import flushSync
from client_code.main import (
    bind,
    computed,
    create_effect,
    effect,
    reactive_class,
    reactive_dict,
    reactive_instance,
    reactive_list,
    signal,
    writeback,
)
from client_code.main._utils import is_testing

is_testing.__code__ = (lambda: True).__code__


@reactive_class
class RC:
    bar = signal(0)

    def __init__(self, foo):
        self.foo = foo

    def inc(self):
        self.foo += 1
        self.bar += 1

    def dec(self):
        self.foo -= 1
        self.bar -= 1

    @effect
    def update_foo(self):
        self.eggs = self.foo

    @computed
    @property
    def baz(self):
        return self.foo + self.bar

    @computed
    def baz2(self):
        return self.foo + self.bar


def test_reactive_class():
    rc = RC(42)

    # the effect is still callable
    rc.update_foo()

    assert rc.bar == 0
    assert rc.foo == 42
    assert rc.eggs == 42
    assert rc.baz == 42
    assert rc.baz2 == 42
    rc.inc()
    flushSync()
    assert rc.bar == 1
    assert rc.foo == 43
    assert rc.eggs == 43
    assert rc.baz == 44
    assert rc.baz2 == 44


def test_reactive_dict():
    x = reactive_dict()
    x["foo"] = 1
    assert x["foo"] == 1

    y = dict(x)

    assert y["foo"] == 1

    @create_effect
    def effect_fn():
        y["foo"] = x["foo"]

    x["foo"] = 2
    flushSync()
    assert y["foo"] == 2


def test_reactive_list():
    x = reactive_list()
    x.append(1)
    assert x[0] == 1
    assert x.count(1) == 1
    assert 1 in x

    y = []

    @create_effect
    def effect_fn():
        y.clear()
        for i in x:
            y.append(i)

    x.append(2)
    flushSync()
    assert y == [1, 2]

    x.sort(reverse=True)
    flushSync()
    assert y == [2, 1]

    x.sort(key=lambda x: x)
    x.pop()
    flushSync()
    assert y == [1]


def test_reactive_instance():
    class RC:
        pass

    rc = RC()
    rc.foo = 42

    reactive_instance(rc)

    assert rc.foo == 42

    @create_effect
    def effect_fn():
        rc.bar = rc.foo

    assert rc.bar == 42

    rc.foo += 1

    assert rc.bar == 43


def add_event_handler(self, event_name, fn):
    self._events = getattr(self, "_events", {})
    events = self._events.setdefault(event_name, [])
    events.append(fn)


def raise_event(self, event_name, **event_args):
    event_args["event_name"] = event_name
    event_args["sender"] = self

    for fn in self._events[event_name]:
        fn(**event_args)


anvil.Component.add_event_handler = add_event_handler
anvil.Component.raise_event = raise_event


def test_binding():
    @reactive_class
    class Custom(anvil.Component):
        __slots__ = ["_events"]

        def __init__(self, **properties):
            self.foo = 42
            bind(self, "bar", lambda: self.foo)

    c = Custom()
    c.raise_event("x-anvil-page-added")
    assert c.bar == 42
    c.foo += 1
    assert c.bar == 43
    c.raise_event("x-anvil-page-removed")
    c.foo += 1
    assert c.bar == 43
    c.raise_event("x-anvil-page-added")
    assert c.bar == 44
    c.raise_event("x-anvil-page-removed")

    @reactive_class
    class Custom(anvil.Component):
        __slots__ = ["_events"]

        def __init__(self, **properties):
            self.foo = 42
            bind(self, "bar", self, "foo")

    c = Custom()
    c.raise_event("x-anvil-page-added")
    assert c.bar == 42
    c.foo += 1
    assert c.bar == 43


def test_writeback():
    @reactive_class
    class Custom(anvil.Component):
        __slots__ = ["_events"]

        def __init__(self, **properties):
            self.foo = 42
            writeback(
                self,
                "bar",
                lambda: self.foo,
                lambda v: setattr(self, "foo", v),
                ("change"),
            )

    c = Custom()
    c.raise_event("x-anvil-page-added")

    assert c.bar == 42
    c.foo += 1
    assert c.bar == 43
    c.bar = 1
    assert c.bar == 1
    assert c.foo == 43
    c.raise_event("change")
    assert c.foo == 1

    @reactive_class
    class Custom(anvil.Component):
        __slots__ = ["_events"]

        def __init__(self, **properties):
            self.foo = 42
            writeback(
                self,
                "bar",
                self,
                "foo",
                ("change",),
            )

    c = Custom()
    c.raise_event("x-anvil-page-added")
    assert c.bar == 42
    c.foo += 1
    assert c.bar == 43
    c.bar = 1
    assert c.bar == 1
    assert c.foo == 43
    c.raise_event("change")
    assert c.foo == 1


def test_reactive_class_with_slots():
    class Namespace:
        pass

    @reactive_class
    class Custom:
        __slots__ = ("foo", "bar")

        def __init__(self):
            self.foo = 1
            self.bar = 2

    class Custom2(Custom):
        def __init__(self):
            self.ns = Namespace()
            self.ns.foo = 1

    c = Custom()
    c2 = Custom2()

    x = 0

    @create_effect
    def effect_fn():
        nonlocal x
        c.foo
        c2.ns.foo
        x += 1

    assert x == 1
    c.foo += 1
    assert x == 2
    c.bar += 1
    assert x == 2

    c.foo = lambda: None
    c.foo = set()
    c.foo = type
    c.foo = Custom

    assert x == 6

    c2.ns.foo += 1

    assert x == 7
    c2.ns.bar = 42
    assert x == 7

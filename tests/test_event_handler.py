import pytest
import logging
from unittest.mock import MagicMock
from whine import EventHandler


@pytest.fixture(scope="function")
def events():
    return EventHandler()


class SomeDispatch:
    def emit_message(self, message):
        pass


def test_add_dispatcher_must_be_instance(events):
    with pytest.raises(TypeError):
        events.add_dispatcher(SomeDispatch)


def test_dispatcher_must_be_of_protocol(events):
    with pytest.raises(TypeError):
        @events.register
        class BadDisp:
            pass


def test_register_dispatcher(events):
    @events.register
    class SomeDispatch:
        def emit_message(self, message):
            return None

    assert len(events.dispatchers) == 1


def test_register_dispatcher_with_init(events):
    @events.register("some-name")
    class SomeDispatch:
        def __init__(self, name):
            self.name = name

        def emit_message(self, message):
            pass

    assert len(events.dispatchers) == 1


def test_add_dispatcher_using_function(events):
    class SomeDispatch:
        def emit_message(self, message):
            pass

    assert len(events.dispatchers) == 0
    events.add_dispatcher(SomeDispatch())
    assert len(events.dispatchers) == 1


def test_subscribe_to_event(events):
    @events.subscribe("FOO")
    def foo():
        return "foo"

    assert "FOO" in events.subscribers
    assert events.subscribers["FOO"]() == "foo"


@pytest.mark.parametrize('not_func', [None, "a", 1, 3.14, [], {}, set()])
def test_subscribe_to_bad_func(events, not_func):
    with pytest.raises(TypeError):
        events.add_subscriber("FOO", not_func)


def test_unsubscribe(events):
    @events.subscribe("FOO")
    def foo():
        return "foo"

    def foo2():
        return "foo2"

    with pytest.raises(ValueError):
        events.add_subscriber("FOO", foo2)

    assert events.unsubscribe("BAD") is False
    assert events.unsubscribe("FOO") is True

    events.add_subscriber("FOO", foo2)
    assert events.subscribers["FOO"]() == "foo2"


def test_dispatch_bad_event(events, caplog):
    with caplog.at_level(logging.WARNING):
        events.dispatch("BAD")
    assert len(caplog.records) == 1
    assert "unsubscribed event" in caplog.records[0].message


def test_dispatch_event_error_in_func(events, caplog):
    events.add_dispatcher(SomeDispatch())

    @events.subscribe("FOO")
    def some_func():
        raise ValueError("bad value")

    with caplog.at_level(logging.ERROR):
        events.dispatch("FOO")

    assert len(caplog.records) == 1
    assert "failed to execute" in caplog.records[0].message


def test_dispatch_event_error_in_dispatcher(events, caplog):
    @events.register
    class SomeDispatch:
        def emit_message(self, message):
            raise ValueError("bad dispatch")

    @events.subscribe("FOO")
    def some_func():
        return "some-func"

    with caplog.at_level(logging.ERROR):
        events.dispatch("FOO")

    assert len(caplog.records) == 1
    assert "failed to execute" in caplog.records[0].message


def test_multiple_dispatchers_multiple_subs(events):
    mock_disp1 = MagicMock()
    mock_disp2 = MagicMock()

    @events.register
    class Disp1:
        def emit_message(self, message):
            mock_disp1(message)

    @events.register
    class Disp2:
        def emit_message(self, message):
            mock_disp2(message)

    assert len(events.dispatchers) == 2

    @events.subscribe("FOO")
    def foo(x):
        return f"my {x}"

    events.dispatch("FOO", "foo")

    mock_disp2.assert_called_once_with("my foo")
    mock_disp1.assert_called_once_with("my foo")

    assert len(events.dispatchers) == 2
    assert len(events.subscribers) == 1

    events.clear()

    assert len(events.dispatchers) == 0
    assert len(events.subscribers) == 0

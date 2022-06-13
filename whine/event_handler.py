import logging
from inspect import isclass
from functools import wraps
from dataclasses import dataclass, field
from typing import Protocol, Callable, List, Type, Any, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class Dispatcher(Protocol):
    def emit_message(self, message: str) -> None:
        """Method for implementing an how a message is emitted"""


@dataclass
class EventHandler:
    """
    Event Handler class for events subscriptions and dispatching messages. Takes no arguments.

    Attributes:
        dispatchers: list of dispatcher instances
        subscribers: dictionary containing subscription events and functions returning a string

    Decorators:
        - `@self.register`: to decorate classes to create and add instances of Dispatchers
        - `@self.register(*args, **kwargs)`: as above, but use args/kwargs for intialisation of a class
        - `@self.subscribe(event: str)`: decorate functions to subscribes an `event` name

    """

    dispatchers: List[Dispatcher] = field(default_factory=list, init=False)
    subscribers: dict = field(default_factory=dict, init=False)

    def register(self, *args, **kwargs):
        """
        Decorator for automatically registering Dispatchers by decorating class definitions.
        Initialization arguments can be passed via the decorator.

        Examples:
            - `@self.register`
            - `@self.register(os.environ["SECRET_TOKEN"], use_ssl=False)`
        """

        def _without_args(_cls: Type[Dispatcher]):
            self.add_dispatcher(_cls())
            return _cls

        def _with_args(_cls: Type[Dispatcher]):
            self.add_dispatcher(_cls(*args, **kwargs))
            return _cls

        if args and isclass(args[0]):
            return _without_args(args[0])
        return _with_args

    def add_dispatcher(self, dispatcher: Dispatcher) -> None:
        """Adds a `Dispatcher` instance to the dispatchers"""
        if not isinstance(dispatcher, Dispatcher):
            raise TypeError("The Dispatcher class does not match the required protocol")
        if isclass(dispatcher):
            raise TypeError("The Dispatcher class must be an initialized instance")
        dispatcher.emit_message = self._handle_exceptions(dispatcher.emit_message)
        self.dispatchers.append(dispatcher)
        logger.debug(f"{dispatcher.__class__.__name__} added to dispatchers")

    def subscribe(self, event: str):
        """Decorator for subscribing event functions with an event name"""

        def subscribe_decorator(func):
            self.add_subscriber(event, func)
            return func

        return subscribe_decorator

    def add_subscriber(self, event: str, func: Callable[[Any], str]) -> None:
        """Adds and event name and function to the subscriptions"""
        if event in self.subscribers:
            raise ValueError(
                f"{event=} is already subscribed. Unsubscribe or change the event name"
            )
        if not callable(func):
            raise TypeError(
                f"The subscriber must be a callable function, not {type(func)}"
            )
        self.subscribers[event] = self._handle_exceptions(func)
        logger.debug(f"{event=} has been subscribed")

    def unsubscribe(self, event: str) -> bool:
        """Removes an event name from subscriptions; Returns: bool"""
        if self.subscribers.pop(event, None):
            return True
        return False

    @staticmethod
    def _handle_exceptions(func):
        """Decorator used for handling Exceptions for graceful returns and logging errors"""

        @wraps(func)
        def handle_exceptions(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                logger.exception(f"{func} failed to execute gracefully")

        return handle_exceptions

    def dispatch(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Dispatches an event by event name.

        Args:
            event: str, name of the event to dispach
            *args: positional arguments for the event function
            **kwargs: keyword arguments for the event function
        """
        if event not in self.subscribers:
            logger.warning(
                f"{self.__class__.__name__}.dispatch received an unsubscribed {event=}"
            )
            return None
        func = self.subscribers[event]
        if message := func(*args, **kwargs):
            for dispatcher in self.dispatchers:
                dispatcher.emit_message(message)
                logger.debug(f"{event=} dispatched to {dispatcher.__class__.__name__}")

    def clear(self) -> None:
        """Resets the state of the instance to a clean state"""
        self.subscribers.clear()
        self.dispatchers.clear()
        logger.debug(f"{self} cleared from all configurations")

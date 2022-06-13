whine
===
![Build Workflow](https://github.com/den4uk/whine/actions/workflows/python-package-test.yml/badge.svg)
[![License](https://img.shields.io/github/license/den4uk/whine.svg)](https://pypi.python.org/pypi/whine)
[![PyPI Version](http://img.shields.io/pypi/v/whine.svg)](https://pypi.python.org/pypi/whine)

> _Because every system time-to-time needs to whine about something_

## Introduction

`whine` is a very lightweight package for custom implementations of subscribing and dispatching event messages, using an observer-like pattern.

The `whine.EventHandler` provides the means to create event-subscribing and dispatching activities.
It allows to separate the logic of responsability amongs the components, and bring them together.

Here is a breakdown of responsabilities, which are mentioned in the examples:
- **Dispatchers**: provide the functionality of conveying a message of an event. Dispatch classes need to have a `.emit_message` method implemented, and their instances would be registered with the `EventHandler`.
- **Event functions**: standalone functions, which compose your message text with any arguments (if needed). These functions would be used to subscribe to an `EventHandler` instance with an _event name_.
- **Event name**: a value, used to represent the event, using a string (treat it as a constant).
- **Dispatch**: an action when `EventHandler.dispatch` method is called with an _event name_ - a message is then created using the _event function_, and dispatched using registered _dispatchers_.

Such approach separates the logic, between how an event notification is conveyed, how a message is composed, and a way how an event message is emitted. If any means of these components are changed, they would not need to be altered in one place, keeping the rest of the setup working as intended.

### Use Cases
- Use a notification platform for dispatching a message (eg: Telegram, Slack, e-mail, logging, etc.)
- Create a function, that formats a message content (eg: failed scheduled task, new user registration). Since the functions are standalone, have the freedom of passing any parameters, those help to format the message value (eg: class instances).
- Dispatch an event notification in a convenient place (eg: in an except block, post-action signals)


## Installation

Requires Python 3.8+

```bash
pip install whine
```

## Quick Start

```python
from whine import EventHandler

events = EventHandler()

# Create a dispatcher class for processing messages
# Implement a `.emit_message` method in that class
# Use a decorator to automatically add to dispatchers
# There can be multiple dispatchers added to an EventHandler instance
@events.register
class SimpleDispatcher:
    def emit_message(self, message: str) -> None:
        print(message)

# Create a function, for processing a message, that returns a string
# The function can take any arguments it may need to form an event message
# Decorate an event function with the `.subscribe`, and provide an event name ('SIMPLE')
@events.subscribe("SIMPLE")
def simple_event(value) -> str:
    return f"Simple event for {value}"

# Trigger the event function, and pass any positional or keyword arguments
events.dispatch("SIMPLE", "my value")

# An output from the event function is then emitted by all registered dispatchers
```

## More Examples

### Logging and Telegram whiners

This example demonstrates an event handler, that uses Telegram and Logging dispatchers.
A function is created and subscribed to, so a pre-defined message is created from a `User` instance.
An event is dispatched when a user is created, so the message is emited to all dispatchers.

```python
import os
import logging
import telebot
from whine import EventHandler
from dataclasses import dataclass

events = EventHandler()

@dataclass
class User:
    name: str

@events.register(os.environ["TELEGRAM_CHAT_ID"], os.environ["TELEGRAM_TOKEN"])
class TelegramDispatcher:
    def __init__(self, chat_id: int, token: str):
        self.chat_id = chat_id
        self.bot = telebot.TeleBot(token)

    def emit_message(self, message: str) -> None:
        self.bot.send_message(self.chat_id, message)

class LoggerDispatcher:
    def __init__(self, level: int = logging.WARNING):
        self.level = level
        self.logger = logging.getLogger(__name__)

    def emit_message(self, message: str) -> None:
        self.logger.log(self.level, message)

# @events.register  # can be used as a naked decorator (when init takes no args)
# Alternatively, create a dispatcher instance and add to the EventHandler
events.add_dispatcher(LoggerDispatcher())

@events.subscribe("NEW_USER")
def event_new_user(user: User) -> str:
    return f"A new user was created {user.name}, welcome them on the platform!"

# Explicitly added subscribtion to an event with a static lambda function
events.add_subscriber("BACKUP_COMPLETED", lambda: "The weekly backup was completed!")

def create_new_user(name: str) -> User:
    """User creation function, also dispatches an event"""
    user = User(name=name)
    events.dispatch("NEW_USER", user)  # an event is dispatched with a position arg
    return user

def weekly_backup():
    """Some function that performs backups"""
    ...  # some implementation
    events.dispatch("BACKUP_COMPLETED")  # an event is dispatched (no args)

```

## Development

Install development dependencies:

```bash
# pip install pipenv
pipenv install --dev
````

Build docs:

```bash
pdoc --html --force -o docs whine
```

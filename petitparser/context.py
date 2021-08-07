from __future__ import annotations
from typing import Any, Generic, TextIO, TypeVar

T = TypeVar('T')


class Context:
    """An immutable parse context"""

    __slots__ = '_buffer', '_position'

    def __init__(self, buffer: str, position: int):
        self._buffer = buffer
        self._position = position

    @property
    def buffer(self):
        return self._buffer

    @property
    def position(self):
        return self._position

    def success(self, value: T, position=None) -> Success[T]:
        if position is None:
            position = self._position

        return Success(self._buffer, position, value)

    def failure(self, message: str, position=None) -> Failure:
        if position is None:
            position = self._position

        return Failure(self._buffer, position, message)

    def __str__(self):
        line, col = line_and_column_of(self._buffer, self._position)
        return f'{type(self).__name__}[{line}:{col}]'


class Result(Context, Generic[T]):
    __slots__ = ()

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return False

    @property
    def value(self) -> T:
        pass

    @property
    def message(self) -> str:
        pass


class Success(Result[T], Generic[T]):
    __slots__ = '_result',

    def __init__(self, buffer: str, position: int, result: T):
        super().__init__(buffer, position)
        self._result = result

    @property
    def is_success(self):
        return True

    @property
    def value(self) -> T:
        return self._result

    def __str__(self) -> str:
        return super().__str__() + ': ' + str(self._result)


class Failure(Result[None]):
    __slots__ = '_message',

    def __init__(self, buffer: str, position: int, message: str):
        super().__init__(buffer, position)
        self._message = message

    @property
    def message(self) -> str:
        return self._message

    @property
    def is_failure(self) -> bool:
        return True

    @property
    def value(self):
        raise ParseError(self)

    def __str__(self):
        return super().__str__() + ': ' + self._message


class ParseError(Exception):
    def __init__(self, failure: Failure):
        super().__init__(failure.message)
        self.failure = failure


class Token(Generic[T]):
    __slots__ = '_buffer', '_start', '_stop', '_value'

    def __init__(self, buffer: str, start: int, stop: int, value: T):
        self._buffer = buffer
        self._start = start
        self._stop = stop
        self._value = value

    @property
    def buffer(self):
        return self._buffer

    @property
    def start(self):
        return self._start

    @property
    def stop(self):
        return self._stop

    @property
    def value(self):
        return self._value

    @property
    def line(self):
        line_and_column_of(self._buffer, self._start)[0]

    @property
    def column(self):
        line_and_column_of(self._buffer, self._start)[1]

    def __str__(self):
        line, col = line_and_column_of(self._buffer, self._start)
        return f'Token[{line}:{col}]: {self._value}'

    def __eq__(self, other: 'Token'):
        if self is other:
            return True
        return (
            type(other) is Token
            and self._start == other._start
            and self._stop == other._stop
            and self._buffer == other._buffer
            and self._value == other._value)

    def __hash__(self):
        return hash((self._start, self._stop, self._buffer, self._value))


def line_and_column_of(buffer: str, position: int):
    line = 1
    col = 1
    for i in range(position):
        if buffer[i] in '\n':
            line += 1
            col = 1
        else:
            col += 1

    return line, col

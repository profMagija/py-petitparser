from __future__ import annotations
from petitparser.context import Context, Result
from typing import Callable, TypeVar, Union, overload
from petitparser.parser import Parser

T = TypeVar('T')

CharPredicate = Callable[[str], bool]


class CharacterParser(Parser[str]):
    __slots__ = '_predicate', '_message'

    def __init__(self, predicate: CharPredicate, message: str):
        self._predicate = predicate
        self._message = message

    def parse_on(self, context: Context) -> Result[T]:
        buffer = context.buffer
        position = context.position

        if position < len(buffer) and self._predicate(buffer[position]):
            return context.success(buffer[position], position + 1)
        return context.failure(self._message)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        if position < len(buffer) and self._predicate(buffer[position]):
            return position + 1
        return -1

    def neg(self, message: str = None) -> Parser[None]:
        if message is None:
            message = 'not ' + self._message
        return CharacterParser(lambda x: not self._predicate(x), message)

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._predicate == other._predicate
                and self._message == other._message)

    def copy(self) -> Parser[T]:
        return CharacterParser(self._predicate, self._message)

    def __str__(self):
        return super().__str__() + '[' + self._message + ']'


class EpsilonParser(Parser[None]):
    def parse_on(self, context: Context) -> Result[None]:
        return context.success(None)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        return position

    def copy(self) -> Parser[None]:
        return EpsilonParser()


class FailureParser(Parser[None]):
    __slots__ = '_message',

    def __init__(self, message: str):
        self._message = message

    def parse_on(self, context: Context) -> Result[T]:
        return context.failure(self._message)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        return -1

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._message == other._message)

    def copy(self) -> Parser[T]:
        return FailureParser(self._message)

    def __str__(self):
        return super().__str__() + '[' + self._message + ']'


class StringParser(Parser[str]):
    __slots__ = '_size', '_predicate', '_message'

    def __init__(self, size: int, predicate: Callable[[str], bool], message: str):
        self._size = size
        self._predicate = predicate
        self._message = message

    def parse_on(self, context: Context) -> Result[str]:
        buffer = context.buffer
        start = context.position

        stop = start + self._size
        if stop <= len(buffer):
            result = buffer[start:stop]
            if self._predicate(result):
                return context.success(result, stop)
        return context.failure(self._message)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        stop = position + self._size
        if stop <= len(buffer) and self._predicate(buffer[position:stop]):
            return stop
        else:
            return -1

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._size == other._size
                and self._predicate == other._predicate
                and self._message == other._message)

    def copy(self) -> Parser[T]:
        return StringParser(self._size, self._predicate, self._message)

    def __str__(self):
        return super().__str__() + '[' + self._message + ']'

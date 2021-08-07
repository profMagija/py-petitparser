from typing import Coroutine, Generic, List, Optional, TypeVar, Union
from . import Parser
from ..context import Context, Result

T = TypeVar('T', covariant=True)
U = TypeVar('U', covariant=True)


class DelegateParser(Parser[T], Generic[T]):
    __slots__ = '_delegate',

    def __init__(self, delegate: Parser[T]):
        self._delegate = delegate

    def parse_on(self, context: Context) -> Result[T]:
        return self._delegate.parse_on(context)

    def replace(self, source: Parser[T], target: Parser[T]):
        if self._delegate is source:
            self._delegate = target

    def get_children(self) -> List[Parser]:
        return [self._delegate]

    def copy(self) -> Parser[T]:
        return DelegateParser(self._delegate)


class AndParser(DelegateParser[T], Generic[T]):
    __slots__ = ()

    def parse_on(self, context: Context) -> Result[T]:
        res = self._delegate.parse_on(context)
        if res.is_success:
            return context.success(res.value)
        else:
            return res

    def fast_parse_on(self, buffer: str, position: int) -> int:
        i = self._delegate.fast_parse_on(buffer, position)
        return -1 if i < 0 else position

    def copy(self) -> Parser[T]:
        return AndParser(self._delegate)


class ListParser(Parser[T], Generic[T]):
    __slots__ = '_parsers',

    def __init__(self, *parsers: Parser):
        if any(parser is None for parser in parsers):
            raise TypeError(str(parsers))
        self._parsers = list(parsers)

    def replace(self, source, target):
        for i in range(len(self._parsers)):
            if self._parsers[i] is source:
                self._parsers[i] = target

    def get_children(self) -> List[Parser]:
        return self._parsers


class ChoiceParser(ListParser[Optional[T]], Generic[T]):
    __slots__ = ()

    def __init__(self, *parsers: Parser[T]):
        if len(parsers) == 0:
            raise ValueError('Choice parser cannot be empty')
        super().__init__(*parsers)

    def parse_on(self, context: Context) -> Result[Optional[T]]:
        for parser in self._parsers:
            res = parser.parse_on(context)
            if res.is_success:
                return res
        return context.failure('expected ' + ' or '.join(str(p) for p in self._parsers))

    def fast_parse_on(self, buffer: str, position: int) -> int:
        for parser in self._parsers:
            res = parser.fast_parse_on(buffer, position)
            if res >= 0:
                return res
        return -1

    def or_(self, *others: Parser[U]) -> Parser[Union[T, U]]:
        return ChoiceParser(*self._parsers, *others)

    def copy(self) -> Parser[T]:
        return ChoiceParser(*self._parsers)


class EndOfInputParser(Parser[None]):
    __slots__ = '_message',

    def __init__(self, message: str):
        self._message = message

    def parse_on(self, context: Context) -> Result[T]:
        if context.position < len(context.buffer):
            return context.failure(self._message)
        else:
            return context.success(None)

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._message == other._message)

    def copy(self) -> Parser[T]:
        return EndOfInputParser(self._message)

    def __str__(self):
        return super().__str__() + '[' + self._message + ']'


class NotParser(DelegateParser[None]):
    __slots__ = '_message'

    def __init__(self, delegate: Parser[T], message: str):
        super().__init__(delegate)
        self._message = message

    def parse_on(self, context: Context) -> Result[T]:
        res = self._delegate.parse_on(context)
        if res.is_failure:
            return context.success(None)
        else:
            return context.failure(self._message)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        res = self._delegate.fast_parse_on(buffer, position)
        return position if res < 0 else -1

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._message == other._message)

    def copy(self):
        return NotParser(self._delegate, self._message)

    def __str__(self):
        return super().__str__() + '[' + self._message + ']'


class OptionalParser(DelegateParser[Union[T, U]], Generic[T, U]):
    __slots__ = '_otherwise',

    def __init__(self, delegate: Parser[T], otherwise: U = None):
        super().__init__(delegate)
        self._otherwise = otherwise

    def parse_on(self, context: Context) -> Result[T]:
        res = self._delegate.parse_on(context)
        if res.is_success:
            return res
        else:
            return context.success(self._otherwise)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        res = self._delegate.fast_parse_on(buffer, position)
        return position if res < 0 else res

    def copy(self) -> Parser[T]:
        return OptionalParser(self._delegate, self._otherwise)


class SequenceParser(ListParser[List[T]], Generic[T]):
    __slots__ = ()

    def __init__(self, *parsers: Parser[T]):
        super().__init__(*parsers)

    def parse_on(self, context: Context) -> Result[List[T]]:
        cur = context
        elems = []
        for parser in self._parsers:
            res = parser.parse_on(cur)
            if res.is_failure:
                return res

            elems.append(res.value)
            cur = res

        return cur.success(elems)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        for parser in self._parsers:
            position = parser.fast_parse_on(buffer, position)
            if position < 0:
                return position
        return position

    def seq(self, *others: Parser[U]) -> Parser[List[Union[T, U]]]:
        return SequenceParser(*self._parsers, *others)

    def copy(self) -> Parser[T]:
        return SequenceParser(*self._parsers)


class SettableParser(DelegateParser[T], Generic[T]):
    __slots__ = ()

    @staticmethod
    def undefined(message: str = 'Undefined parser'):
        from .primitive import FailureParser
        return SettableParser(FailureParser(message))

    def fast_parse_on(self, buffer: str, position: int) -> int:
        return self._delegate.fast_parse_on(buffer, position)

    def get(self):
        return self._delegate

    def set(self, parser: Parser[T]):
        self._delegate = parser

    def copy(self) -> Parser[T]:
        return SettableParser(self._delegate)

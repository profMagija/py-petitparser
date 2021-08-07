
from ..context import Context, Result, Token
from . import Parser
from .combinators import DelegateParser
from typing import Callable, Generic, List, TypeVar


T = TypeVar('T', covariant=True)
R = TypeVar('R', covariant=True)


class ActionParser(DelegateParser[R], Generic[T, R]):
    __slots__ = '_function', '_has_side_effects'

    def __init__(self, delegate: Parser[T], func: Callable[[T], R], side_effects: bool = False):
        super().__init__(delegate)
        self._function = func
        self._has_side_effects = side_effects

    def parse_on(self, context: Context) -> Result[T]:
        res = self._delegate.parse_on(context)
        if res.is_success:
            return res.success(self._function(res.value))
        else:
            return res

    def fast_parse_on(self, buffer: str, position: int) -> int:
        if self._has_side_effects:
            return super().fast_parse_on(buffer, position)
        else:
            return self._delegate.fast_parse_on(buffer, position)

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._function == other._function
                and self._has_side_effects == other._has_side_effects)

    def copy(self) -> Parser[T]:
        return ActionParser(self._delegate, self._function, self._has_side_effects)


class ContinuationParser(DelegateParser[R], Generic[T, R]):
    __slots__ = '_handler',

    def __init__(self, delegate: Parser[T], handler: Callable[[Callable[[Context], Result[T]]], Result[R]]):
        super().__init__(delegate)
        self._handler = handler

    def parse_on(self, context: Context) -> Result[T]:
        return self._handler(super().parse_on, context)

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._handler == other._handler)

    def copy(self) -> Parser[T]:
        return ContinuationParser(self._delegate, self._handler)


class FlattenParser(DelegateParser[str]):
    __slots__ = '_message',

    def __init__(self, delegate: Parser[T], message: str = None):
        super().__init__(delegate)
        self._message = message

    def parse_on(self, context: Context) -> Result[T]:
        if self._message is None:
            result = self._delegate.parse_on(context)
            if result.is_success:
                flattened = context.buffer[context.position:result.position]
                return result.success(flattened)
            else:
                return result
        else:
            position = self._delegate.fast_parse_on(
                context.buffer, context.position)
            if position < 0:
                return context.failure(self._message)
            output = context.buffer[context.position:position]
            return context.success(output, position)

    def copy(self) -> Parser[T]:
        return FlattenParser(self._delegate, self._message)


class TokenParser(DelegateParser[Token]):
    __slots__ = ()

    def __init__(self, delegate: Parser[T]):
        super().__init__(delegate)

    def parse_on(self, context: Context) -> Result[T]:
        result = self._delegate.parse_on(context)
        if result.is_success:
            token = Token(context.buffer, context.position,
                          result.position, result.value)
            return result.success(token)
        else:
            return result

    def fast_parse_on(self, buffer: str, position: int) -> int:
        return self._delegate.fast_parse_on(buffer, position)

    def copy(self) -> Parser[T]:
        return TokenParser(self._delegate)


class TrimmingParser(DelegateParser[T], Generic[T]):
    __slots__ = '_left', '_right'

    def __init__(self, delegate: Parser[T], left: Parser, right: Parser):
        super().__init__(delegate)
        self._left = left
        self._right = right

    def parse_on(self, context: Context) -> Result[T]:
        buffer = context.buffer

        before = _consume(self._left, buffer, context.position)
        if before != context.position:
            context = Context(buffer, before)

        result = self._delegate.parse_on(context)
        if result.is_failure:
            return result

        after = _consume(self._right, buffer, result.position)
        if after == result.position:
            return result
        else:
            return result.success(result.value, after)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        result = self._delegate.fast_parse_on(
            buffer, _consume(self._left, buffer, position))
        if result < 0:
            return result
        else:
            return _consume(self._right, buffer, result)

    def replace(self, source: Parser[T], target: Parser[T]):
        super().replace(source, target)
        if self._left is source:
            self._left = target
        if self._right is source:
            self._right = target

    def get_children(self) -> List[Parser]:
        return [self._delegate, self._left, self._right]

    def copy(self) -> Parser[T]:
        return TrimmingParser(self._delegate, self._left, self._right)


def _consume(parser: Parser, buffer: str, position: int):
    while True:
        result = parser.fast_parse_on(buffer, position)
        if result < 0:
            return position
        position = result

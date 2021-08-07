from petitparser.context import Context, Result
from . import Parser
from typing import Generic, List, TypeVar
from .combinators import DelegateParser

T = TypeVar('T')


class RepeatingParser(DelegateParser[List[T]], Generic[T]):
    __slots__ = '_min', '_max'

    def __init__(self, delegate: Parser[T], min: int, max: int):
        super().__init__(delegate)
        self._min = min
        self._max = max

        if min < 0:
            raise ValueError(f'invalid min repetitions: {self.range}')

        if max != -1 and min > max:
            raise ValueError(f'invalid max repetitions: {self.range}')

    def has_equal_properties(self, other: Parser) -> bool:
        return (super().has_equal_properties(other)
                and self._min == other._min
                and self._max == other._max)

    @property
    def range(self):
        return str(self._min) + '..' + ('*' if self._max == -1 else str(self._max))


class LimitedRepeatingParser(RepeatingParser[T], Generic[T]):
    __slots__ = '_limit',

    def __init__(self, delegate: Parser[T], limit: Parser, min: int, max: int):
        super().__init__(delegate, min, max)
        self._limit = limit

    def get_children(self) -> List[Parser]:
        return [self._delegate, self._limit]

    def replace(self, source: Parser[T], target: Parser[T]):
        super().replace(source, target)
        if source is self._limit:
            self._limit = target


class GreedyRepeatingParser(LimitedRepeatingParser[T], Generic[T]):
    __slots__ = ()

    def parse_on(self, context: Context) -> Result[List[T]]:
        current = context
        elements = []

        while len(elements) < self._min:
            result = self._delegate.parse_on(current)
            if result.is_failure:
                return result

            elements.append(result.value)
            current = result

        contexts = [current]
        while self._max == -1 or len(elements) < self._max:
            result = self._delegate.parse_on(current)
            if result.is_failure:
                break
            elements.append(result.value)
            contexts.append(result)
            current = result

        while True:
            limiter = self._limit.parse_on(contexts[-1])
            if limiter.is_success:
                return contexts[-1].success(elements)
            if not elements:
                return limiter
            contexts.pop()
            elements.pop()
            if not contexts:
                return limiter

    def fast_parse_on(self, buffer: str, position: int) -> int:
        count = 0
        current = position
        while count < self._min:
            result = self._delegate.fast_parse_on(buffer, current)
            if result < 0:
                return -1
            current = result
            count += 1

        positions = [current]

        while self._max == -1 or count < self._max:
            result = self._delegate.fast_parse_on(buffer, current)
            if result < 0:
                break
            positions.append(result)
            current = result
            count += 1

        while True:
            limiter = self._limit.fast_parse_on(buffer, positions[-1])
            if limiter >= 0:
                return positions[-1]

            if count == 0:
                return -1

            positions.pop()
            count -= 1

            if not positions:
                return -1

    def copy(self) -> Parser[T]:
        return GreedyRepeatingParser(self._delegate, self._limit, self._min, self._max)


class LazyRepeatingParser(LimitedRepeatingParser[T], Generic[T]):
    __slots__ = ()

    def parse_on(self, context: Context) -> Result[T]:
        current = context
        elements = []

        while len(elements) < self._min:
            result = self._delegate.parse_on(current)
            if result.is_failure:
                return result

            elements.append(result.value)
            current = result

        while True:
            limiter = self._limit.parse_on(current)
            if limiter.is_success:
                return current.success(elements)

            if self._max != -1 and len(elements) >= self._max:
                return limiter

            result = self._delegate.parse_on(current)
            if result.is_failure:
                return limiter

            elements.append(result.value)
            current = result

    def fast_parse_on(self, buffer: str, position: int) -> int:
        count = 0
        current = position
        while count < self._min:
            result = self._delegate.fast_parse_on(buffer, current)
            if result < 0:
                return -1

            current = result
            count += 1

        while True:
            limiter = self._limit.fast_parse_on(buffer, current)
            if limiter >= 0:
                return current
            else:
                if self._max != -1 and count >= self._max:
                    return -1

                result = self._delegate.fast_parse_on(buffer, current)
                if result < 0:
                    return -1

                current = result
                count += 1

    def copy(self) -> Parser[T]:
        return LazyRepeatingParser(self._delegate, self._limit, self._min, self._max)


class PossesiveRepeatingParser(RepeatingParser[T], Generic[T]):
    __slots__ = ()

    def parse_on(self, context: Context) -> Result[T]:
        current = context
        elements = []

        while len(elements) < self._min:
            result = self._delegate.parse_on(current)
            if result.is_failure:
                return result

            elements.append(result.value)
            current = result

        while self._max == -1 or len(elements) < self._max:
            result = self._delegate.parse_on(current)
            if result.is_failure:
                return current.success(elements)

            elements.append(result.value)
            current = result

        return current.success(elements)

    def fast_parse_on(self, buffer: str, position: int) -> int:
        current = position
        count = 0

        while count < self._min:
            result = self._delegate.fast_parse_on(buffer, current)
            if result < 0:
                return result

            count += 1
            current = result

        while self._max == -1 or count < self._max:
            result = self._delegate.fast_parse_on(buffer, current)
            if result < 0:
                return current

            count += 1
            current = result

        return current

    def copy(self) -> Parser[T]:
        return PossesiveRepeatingParser(self._delegate, self._min, self._max)

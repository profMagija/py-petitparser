from __future__ import annotations
from functools import reduce
from typing import Callable, Generic, List, TypeVar
from petitparser.parser import Parser
from petitparser.parser.primitive import FailureParser
from ..parser.combinators import ChoiceParser, SequenceParser, SettableParser

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')


def _build_choice(parsers: List[Parser], otherwise: Parser = None):
    if not parsers:
        if otherwise is None:
            raise TypeError(otherwise)
        return otherwise
    elif len(parsers) == 1:
        return parsers[0]
    else:
        return ChoiceParser(*parsers)


class ExpressionBuilder(Generic[T]):
    __slots__ = '_loopback', '_groups'

    def __init__(self):
        self._loopback: SettableParser[T] = SettableParser.undefined()
        self._groups = []

    def group(self, defaultAction: Callable = None) -> ExpressionGroup:
        g = ExpressionGroup(self, defaultAction)
        self._groups.append(g)
        return g

    def build(self) -> Parser:
        parser = FailureParser(
            'Highest priority group should define a primitive parser.')

        for group in self._groups:
            parser = group._build(parser)

        self._loopback.set(parser)
        return parser


class ExpressionGroup(Generic[T]):
    __slots__ = '_builder', '_primitives', '_wrappers', '_prefix', '_postfix', '_left', '_right', '_defaultAction'

    def __init__(self, builder: ExpressionBuilder, defaultAction: Callable = None):
        self._builder = builder
        self._primitives = []
        self._wrappers = []
        self._prefix = []
        self._postfix = []
        self._left = []
        self._right = []
        self._defaultAction = defaultAction or (lambda *x: list(x))

    def primitive(self, parser: Parser[U], action: Callable[[U], T] = None) -> ExpressionGroup:
        self._primitives.append(parser if action is None
                                else parser.map(action))
        return self

    def _build_primitive(self, inner: Parser):
        return _build_choice(self._primitives, inner)

    def wrapper(self, left: Parser[U], right: Parser[V], action: Callable[[U, T, V], T] = None) -> ExpressionGroup:
        parser = SequenceParser(left, self._builder._loopback, right)
        self._wrappers.append(
            parser if action is None
            else parser.map(lambda x: action(*x)))
        return self

    def _build_wrapper(self, inner: Parser):
        choices = list(self._wrappers)
        choices.append(inner)
        return _build_choice(choices, inner)

    def prefix(self, parser: Parser[U], action: Callable[[U, T], T] = None) -> ExpressionGroup:
        return self._add_to(self._prefix, parser, action)

    def _build_prefix(self, inner: Parser):
        if not self._prefix:
            return inner

        sequence = SequenceParser(_build_choice(self._prefix).star(), inner)

        def _m(tup):
            tuples, value = tup
            for operator, action in reversed(tuples):
                value = action(operator, value)
            return value
        return sequence.map(_m)

    def postfix(self, parser: Parser[U], action: Callable[[T, U], T] = None) -> ExpressionGroup:
        return self._add_to(self._postfix, parser, action)

    def _build_postfix(self, inner: Parser):
        if not self._postfix:
            return inner

        sequence = SequenceParser(inner, _build_choice(self._postfix).star())

        def _m(tup):
            value = tup[0]
            for operator, action in tup[1]:
                value = action(value, operator)
            return value
        return sequence.map(_m)

    def right(self, parser: Parser[U], action: Callable[[T, U, T], T] = None) -> ExpressionGroup:
        return self._add_to(self._right, parser, action)

    def _build_right(self, inner: Parser):
        if not self._right:
            return inner

        sequence = inner.separated_by(_build_choice(self._right))

        def _m(seq):
            result = seq[-1]

            for i in range(len(seq) - 2, 0, -2):
                operator, action = seq[i]
                result = action(seq[i - 1], operator, result)
            return result
        return sequence.map(_m)

    def left(self, parser: Parser[U], action: Callable[[T, U, T], T] = None) -> ExpressionGroup:
        return self._add_to(self._left, parser, action)

    def _build_left(self, inner: Parser):
        if not self._left:
            return inner

        sequence = inner.separated_by(_build_choice(self._left))

        def _m(seq):
            result = seq[0]

            for i in range(1, len(seq), 2):
                operator, action = seq[i]
                result = action(result, operator, seq[i+1])
            return result

        return sequence.map(_m)

    def _add_to(self, l: List[Parser], parser: Parser, action: Callable) -> ExpressionGroup:
        if action is None:
            action = self._defaultAction

        l.append(parser.map(lambda op: (op, action)))
        return self

    def _build(self, inner: Parser) -> Parser:
        return self._build_left(self._build_right(self._build_postfix(self._build_prefix(self._build_wrapper(self._build_primitive(inner))))))

from __future__ import annotations
from petitparser.parser.combinators import DelegateParser
from petitparser.parser import Parser
from typing import Any, Callable, Dict, TypeVar, overload
import sys

META_DISABLE = True


class GD(dict):
    def __init__(self):
        self.tasks = []

    def __setitem__(self, key, value):
        if key.startswith("_"):
            super().__setitem__(key, value)
        else:
            self.tasks.append((key, value))


class GrammarDefinitionMeta(type):
    @classmethod
    def __prepare__(metacls, name, bases):
        if META_DISABLE:
            return dict()
        return GD()

    def __new__(cls, name, bases, classdict):
        if META_DISABLE:
            return type.__new__(cls, name, bases, classdict)
        result = type.__new__(cls, name, bases, {})
        result._parsers = {}
        tasks = []
        for base in bases:
            if hasattr(base, '_tasks'):
                tasks.extend(base._tasks)
        tasks.extend(classdict.tasks)
        defd = set()
        for k, v in tasks:
            if k in defd:
                result.redef(k, v)
            else:
                result.define(k, v)
                defd.add(k)
        result._tasks = tuple(tasks)
        result._parsers = {
            k: v.deep_copy()
            for k, v in result._parsers.items()}
        # pprint('-------------------------------')
        # pprint(name)
        # pprint(result._parsers)
        # pprint('-------------------------------')
        return result


class Reference(Parser):
    __slots__ = '_name',

    def __init__(self, name):
        self._name = name

    def _resolve(self, parsers):
        if self._name not in parsers:
            raise ValueError('Unknown parser reference: ' + self._name)
        return parsers[self._name]

    def parse(self, inp: str):
        return TypeError('References cannot be parsed.')

    def copy(self):
        return self

    def __eq__(self, other):
        if self is other:
            return True
        return type(self) is type(other) and self._name == other._name

    def __hash__(self):
        return hash(self._name)

    def __str__(self):
        return 'Reference[' + self._name + ']'


class GrammarDefinition(metaclass=GrammarDefinitionMeta):
    @classmethod
    def ref(cls, name: str):
        return Reference(name)

    @classmethod
    def define(cls, name: str, parser: Parser):
        if name in cls._parsers:
            raise ValueError('Duplicate production: ' + name)
        cls._parsers[name] = parser

    @classmethod
    def redef(cls, name: str, parser: Parser):
        if name not in cls._parsers:
            raise ValueError('Undefined production: ' + name)
        if callable(parser):
            parser = cls._parsers[name].map(parser)
        cls._parsers[name] = parser

    @classmethod
    def action(cls, name: str, action: Callable):
        cls.redef(name, lambda x: x.map(action))

    @classmethod
    def build(cls, name: str = 'start') -> Parser:
        return cls._resolve(Reference(name))

    @classmethod
    def _dereference(cls, mapping: Dict[Reference, Parser], reference: Reference):
        if reference in mapping:
            return mapping[reference]

        references = [reference]
        parser = reference._resolve(cls._parsers)

        while isinstance(parser, Reference):
            if parser in references:
                raise Exception(
                    'Recursive references detected: '
                    + ','.join(ref.name for ref in references))
            references.append(parser)
            parser = parser._resolve(cls._parsers)

        for ref in references:
            # print('resolved', ref, '->', parser)
            mapping[ref] = parser

        return parser

    @classmethod
    def _resolve(cls, ref: Reference):
        mapping = {}
        todo = [cls._dereference(mapping, ref)]
        seen = set(todo)
        while todo:
            parent = todo.pop()
            # print(parent, ' -> ', parent.get_children())
            for child in parent.get_children():
                if isinstance(child, Reference):
                    referenced = cls._dereference(mapping, child)
                    parent.replace(child, referenced)
                    child = referenced
                if child not in seen:
                    seen.add(child)
                    todo.append(child)
        return mapping[ref]


def ref(name) -> Parser:
    return Reference(name)


T = TypeVar('T')


def action(func: Callable[[Any], T]) -> Parser[T]:
    return func


META_DISABLE = False


class GrammarParser(DelegateParser):
    def __init__(self, definition: GrammarDefinition, name: str = 'start'):
        super().__init__(definition.build(name))

    def fast_parse_on(self, buffer: str, position: int) -> int:
        return self._delegate.fast_parse_on(buffer, position)

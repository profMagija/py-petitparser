from typing import Callable, Iterable, Iterator, List, Set
from .parser import Parser


class ParserIterator(Iterator[Parser]):
    def __init__(self, root):
        self._todo: List[Parser] = [root]
        self._seen: Set[Parser] = {root}

    def __next__(self):
        if not self._todo:
            raise StopIteration
        current = self._todo.pop()
        for p in current.get_children():
            if p not in self._seen:
                self._todo.append(p)
                self._seen.add(p)
        return current


class Mirror(Iterable[Parser]):
    def __init__(self, parser: Parser):
        self._parser = parser

    def __str__(self):
        return type(self).__name__ + ' of ' + str(self._parser)

    def __iter__(self):
        return ParserIterator(self._parser)

    def transform(self, transformer: Callable[[Parser], Parser]) -> Parser:
        mapping = {p: transformer(p.copy()) for p in self}

        seen = set(mapping.values())
        todo = list(mapping.values())

        while todo:
            parent = todo.pop()
            for child in parent.get_children():
                if child in mapping:
                    parent.replace(child, mapping[child])
                elif child not in seen:
                    seen.add(child)
                    todo.append(child)
        return mapping[self._parser]

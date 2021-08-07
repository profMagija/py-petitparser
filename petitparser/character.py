

from .parser.primitive import CharPredicate, CharacterParser
from typing import Callable, overload


@overload
def of(character: str, message: str = None) -> CharacterParser: ...
@overload
def of(predicate: CharPredicate, message: str) -> CharacterParser: ...


def of(pred, message=None):
    if isinstance(pred, str):
        def predicate(x):
            return x == pred
        if len(pred) != 1:
            raise ValueError('expectefd a single character string')
        if message is None:
            message = f'{pred!r} expected'
    elif callable(pred):
        predicate = pred
        if message is None:
            raise ValueError(
                'expected a message when sopplying a predicate')
    else:
        raise TypeError('expected a character or a predicate')

    return CharacterParser(predicate, message)


def any(message: str = 'any character expected'):
    return of(lambda x: True, message)


def any_of(characters: str, message: str = None):
    if message is None:
        message = f'any of {characters!r} expected'
    return of(lambda x: x in characters, message)


def none(message: str = 'no character expected'):
    return of(lambda x: False, message)


def none_of(characters: str, message: str = None):
    if message is None:
        message = f'none of {characters!r} expected'
    return of(lambda x: x not in characters, message)


def digit(message: str = 'digit expected'):
    return of(str.isdigit, message)


def letter(message: str = 'letter expected'):
    return of(str.isalpha, message)


def lowercase(message: str = 'lowercase letter expected'):
    return of(str.islower, message)


def range(start: str, end: str, message: str = None):
    if message is None:
        message = f'{start}..{end} expected'
    return of(lambda x: start <= x <= end, message)


def uppercase(message: str = 'uppercase letter expected'):
    return of(str.isupper, message)


def whitespace(message: str = 'whitespace expected'):
    return of(str.isspace, message)


def word(message: str = 'letter or digit expected'):
    return of(str.isalnum, message)

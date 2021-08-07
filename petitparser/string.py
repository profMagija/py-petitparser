from .parser.primitive import StringParser


def of(value: str, message: str = None):
    if message is None:
        message = f'{value!r} expected'

    return StringParser(len(value), value.__eq__, message)


def of_ignoring_case(value: str, message: str = None):
    if message is None:
        message = f'{value!r} expected'
    return StringParser(len(value), lambda x: value.casefold() == x.casefold(), message)

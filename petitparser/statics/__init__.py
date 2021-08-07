from ..parser.primitive import EpsilonParser, FailureParser
from ..parser import Parser


def epsilon() -> Parser[None]:
    return EpsilonParser()


def fail(message: str = 'impossible'):
    return FailureParser(message)

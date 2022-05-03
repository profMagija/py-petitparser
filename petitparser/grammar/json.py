from ctypes import FormatError
from petitparser.tools.grammar_definition import (
    GrammarDefinition,
    GrammarParser,
    ref,
    action,
)
from petitparser.string import of as s_of
from petitparser.character import any_of, digit, none_of, of as c_of

ESCAPE_TABLE = {
    "\\": "\\",
    "/": "/",
    '"': '"',
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}


class JsonGrammarDefinition(GrammarDefinition):
    "JSON grammar definition"

    start = ref("value").end()

    array = c_of("[").trim() & ref("elements").optional() & c_of("]").trim()
    elements = ref("value").separated_by(c_of(",").trim())
    members = ref("pair").separated_by(c_of(",").trim())
    object = c_of("{").trim() & ref("members").optional() & c_of("}").trim()
    pair = ref("stringToken") & c_of(":").trim() & ref("value")
    value = (
        ref("stringToken")
        | ref("numberToken")
        | ref("trueToken")
        | ref("falseToken")
        | ref("nullToken")
        | ref("object")
        | ref("array")
    )

    trueToken = s_of("true").flatten("Expected 'true'").trim()
    falseToken = s_of("false").flatten("Expected 'false'").trim()
    nullToken = s_of("null").flatten("Expected 'null'").trim()
    stringToken = ref("stringPrimitive").flatten("Expected string").trim()
    numberToken = ref("numberPrimitive").flatten("Expected number").trim()

    characterPrimitive = (
        ref("characterEscape") | ref("characterOctal") | ref("characterNormal")
    )
    characterEscape = c_of("\\") & any_of("".join(ESCAPE_TABLE.keys()))
    characterOctal = s_of("\\u") & any_of("0123456789abcdefABCDEF").times(4).flatten()
    characterNormal = none_of('"\\')

    numberPrimitive = (
        c_of("-").optional()
        & (c_of("0") | digit().plus())
        & (c_of(".") & digit().plus()).optional()
        & (any_of("eE") & any_of("+-").optional() & digit().plus()).optional()
    )
    stringPrimitive = c_of('"') & ref("characterPrimitive").star() & c_of('"')


class JsonParserDefinition(JsonGrammarDefinition):
    "JSON parser definition"

    # actions can be specified by reassigning a function to a rule
    elements = action(lambda data: data[::2])
    members = action(lambda data: data[::2])

    # alternatively, you can declare a function by the same name
    # and decorate it with @action (which in Python is identical
    # to the previous assignment)
    @action
    def array(data):
        return data[1] or []

    @action
    def object(data):
        return {e[0]: e[2] for e in data[1]} if data[1] else {}

    trueToken = action(lambda _: True)
    falseToken = action(lambda _: False)
    nullToken = action(lambda _: None)

    # redef is just a reassignment
    stringToken = ref("stringPrimitive").trim()

    @action
    def numberToken(data: str):
        if data.isnumeric():
            return int(data)
        else:
            return float(data)

    @action
    def stringPrimitive(data):
        return "".join(data[1])

    @action
    def characterEscape(data):
        return ESCAPE_TABLE[data[1]]

    @action
    def characterOctal(data):
        return chr(int(data[1], base=16))


class JsonParser(GrammarParser):
    def __init__(self):
        super().__init__(JsonParserDefinition())

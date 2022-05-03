import json
import unittest

from petitparser.grammar.json import JsonParser

EPSILON = 1e-6
PARSER = JsonParser()

EXAMPLES = [
    "[]",
    '["a"]',
    '["a" ]',
    '[["a"]]',
    "{}",
    '{"a":1}',
    ' { "a" : 1 , "b" : 2 } ',
    '{"object":{"1": 2}}',
    "true",
    "false",
    "null",
    "0.0",
    "0.12",
    "-0.12",
    "12.34",
    "-12.34",
    "1.2e0",
    "1.2e-1",
    "1.2E-1",
    "0",
    "1",
    "-1",
    "12",
    "-12",
    "1e2",
    "1e+2",
    '""',
    '"foo"',
    '"foo bar"',
    '"\\""',
    '"\\\\"',
    '"\\/"',
    '"\\b"',
    '"\\f"',
    '"\\n"',
    '"\\r"',
    '"\\t"',
    '"\\u20Ac"',
    '{"recordset": null, "type": "change", "fromElement": null, "toElement": null, '
    + '"altLeft": false, "keyCode": 0, "repeat": false, "reason": 0, '
    + '"behaviorCookie": 0, "contentOverflow": false, "behaviorPart": 0, '
    + '"dataTransfer": null, "ctrlKey": false, "shiftLeft": false, "dataFld": "",'
    + ' "qualifier": "", "wheelDelta": 0, "bookmarks": null, "button": 0, '
    + '"srcFilter": null, "nextPage": "", "cancelBubble": false, "x": 89, "y": '
    + '502, "screenX": 231, "screenY": 1694, "srcUrn": "", "boundElements": '
    + '{"length": 0}, "clientX": 89, "clientY": 502, "propertyName": "", '
    + '"shiftKey": false, "ctrlLeft": false, "offsetX": 25, "offsetY": 2, '
    + '"altKey": false}',
    '{"type": "change", "eventPhase": 2, "bubbles": true, "cancelable": true, '
    + '"timeStamp": 0, "CAPTURING_PHASE": 1, "AT_TARGET": 2, "BUBBLING_PHASE": 3, '
    + '"isTrusted": true, "MOUSEDOWN": 1, "MOUSEUP": 2, "MOUSEOVER": 4, '
    + '"MOUSEOUT": 8, "MOUSEMOVE": 16, "MOUSEDRAG": 32, "CLICK": 64, "DBLCLICK": '
    + '128, "KEYDOWN": 256, "KEYUP": 512, "KEYPRESS": 1024, "DRAGDROP": 2048, '
    + '"FOCUS": 4096, "BLUR": 8192, "SELECT": 16384, "CHANGE": 32768, "RESET": '
    + '65536, "SUBMIT": 131072, "SCROLL": 262144, "LOAD": 524288, "UNLOAD": '
    + '1048576, "XFER_DONE": 2097152, "ABORT": 4194304, "ERROR": 8388608, "LOCATE":'
    + ' 16777216, "MOVE": 33554432, "RESIZE": 67108864, "FORWARD": 134217728, '
    + '"HELP": 268435456, "BACK": 536870912, "TEXT": 1073741824, "ALT_MASK": 1, '
    + '"CONTROL_MASK": 2, "SHIFT_MASK": 4, "META_MASK": 8}',
    '{"returnValue": true, "timeStamp": 1226697417289, "eventPhase": 2, "type": '
    + '"change", "cancelable": false, "bubbles": true, "cancelBubble": false, '
    + '"MOUSEOUT": 8, "FOCUS": 4096, "CHANGE": 32768, "MOUSEMOVE": 16, '
    + '"AT_TARGET": 2, "SELECT": 16384, "BLUR": 8192, "KEYUP": 512, "MOUSEDOWN": '
    + '1, "MOUSEDRAG": 32, "BUBBLING_PHASE": 3, "MOUSEUP": 2, "CAPTURING_PHASE": 1,'
    + ' "MOUSEOVER": 4, "CLICK": 64, "DBLCLICK": 128, "KEYDOWN": 256, "KEYPRESS":'
    + ' 1024, "DRAGDROP": 2048}',
]

COUNTER_EXAMPLES = [
    "[",
    "[1",
    "[1,",
    "[1,]",
    "[1 2]",
    "[]]",
    "{",
    '{"a"',
    '{"a":',
    '{"a":"b"',
    '{"a":"b",',
    '{"a"}',
    '{"a":}',
    '{"a":"b",}',
    "{}}",
    '"',
    '"a',
    '"\\"',
    '"\\a"',
    '"\\u"',
    '"\\u1"',
    '"\\u12"',
    '"\\u123"',
    '"\\u123x"',
    "00",
    "01",
    "00.1",
    "tr",
    "trace",
    "truest",
    "fa",
    "falsely",
    "fabulous",
    "nu",
    "nuclear",
    "nullified",
]


class JsonParserTest(unittest.TestCase):
    def _test_valid(self, inp):
        res = PARSER.parse(inp)
        self.assertTrue(res.is_success)
        return res

    def test_examples(self):
        for example in EXAMPLES:
            result = PARSER.parse(example)
            self.assertTrue(result.is_success)

            ref_value = json.loads(example)
            our_value = result.value

            if isinstance(ref_value, float):
                self.assertAlmostEqual(
                    ref_value,
                    our_value,
                    delta=EPSILON,
                    msg="Mismatch on input: " + repr(example),
                )
            else:
                self.assertEqual(
                    json.loads(example),
                    result.value,
                    msg="Mismatch on input: " + repr(example),
                )

    def test_counter_examples(self):
        for counter_example in COUNTER_EXAMPLES:
            result = PARSER.parse(counter_example)
            self.assertTrue(
                result.is_failure,
                msg=f"expected failure on input: {counter_example!r}, got {result}",
            )

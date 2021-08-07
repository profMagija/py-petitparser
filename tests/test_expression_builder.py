import builtins
import unittest
from petitparser import ExpressionBuilder, string
from petitparser.character import *


class ExpressionBuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        builder = ExpressionBuilder()
        builder.group()\
            .primitive((digit().plus() & (of('.') & digit().plus()).optional()).flatten().trim())\
            .wrapper(of('(').trim(), of(')').trim())
        builder.group()\
            .prefix(of('-').trim())
        builder.group()\
            .postfix(string.of('++').trim())\
            .postfix(string.of('--').trim())
        builder.group()\
            .right(of('^').trim())
        builder.group()\
            .left(of('*').trim())\
            .left(of('/').trim())
        builder.group()\
            .left(of('+').trim())\
            .left(of('-').trim())
        self.parser = builder.build().end()

        builder = ExpressionBuilder()

        builder.group()\
            .primitive((digit().plus() & (of('.') & digit().plus()).optional()).flatten().trim().map(float))\
            .wrapper(of('(').trim(), of(')').trim(), lambda _x, y, _z: y)
        builder.group()\
            .prefix(of('-').trim(), lambda _x, y: -y)
        builder.group()\
            .postfix(string.of('++').trim(), lambda x, op: x+1)\
            .postfix(string.of('--').trim(), lambda x, op: x-1)
        builder.group()\
            .right(of('^').trim(), lambda x, _, y: x ** y)
        builder.group()\
            .left(of('*').trim(), lambda x, _, y: x * y)\
            .left(of('/').trim(), lambda x, _, y: x / y)
        builder.group()\
            .left(of('+').trim(), lambda x, _, y: x + y)\
            .left(of('-').trim(), lambda x, _, y: x - y)

        self.evaluator = builder.build().end()

    def assertParse(self, inp, expected):
        actual = self.parser.parse(inp).value
        self.assertEqual(expected, actual)

    def assertEvaluate(self, inp, expected):
        actual = self.evaluator.parse(inp).value
        self.assertAlmostEqual(expected, actual, delta=1e-5)

    def test_parse_number(self):
        self.assertParse('0', '0')
        self.assertParse('1.2', '1.2')
        self.assertParse('34.78', '34.78')

    def test_evaluete_number(self):
        self.assertEvaluate('0', 0)
        self.assertEvaluate('0.0', 0)
        self.assertEvaluate('1', 1)
        self.assertEvaluate('1.2', 1.2)
        self.assertEvaluate('34', 34)
        self.assertEvaluate('34.7', 34.7)
        self.assertEvaluate('56.78', 56.78)

    def test_parse_negative_number(self):
        self.assertParse('-1', ['-', '1'])
        self.assertParse('-1.2', ['-', '1.2'])

    def test_evaluate_negative_number(self):
        self.assertEvaluate('-1', -1)
        self.assertEvaluate('-1.2', -1.2)

    def testParseAdd(self):
        self.assertParse("1 + 2", asList("1", '+', "2"))
        self.assertParse("1 + 2 + 3", asList(asList("1", '+', "2"), '+', "3"))

    def testEvaluateAdd(self):
        self.assertEvaluate("1 + 2", 3)
        self.assertEvaluate("2 + 1", 3)
        self.assertEvaluate("1 + 2.3", 3.3)
        self.assertEvaluate("2.3 + 1", 3.3)
        self.assertEvaluate("1 + -2", -1)
        self.assertEvaluate("-2 + 1", -1)

    def testEvaluateAddMany(self):
        self.assertEvaluate("1", 1)
        self.assertEvaluate("1 + 2", 3)
        self.assertEvaluate("1 + 2 + 3", 6)
        self.assertEvaluate("1 + 2 + 3 + 4", 10)
        self.assertEvaluate("1 + 2 + 3 + 4 + 5", 15)

    def testParseSub(self):
        self.assertParse("1 - 2", asList("1", '-', "2"))
        self.assertParse("1 - 2 - 3", asList(asList("1", '-', "2"), '-', "3"))

    def testEvaluateSub(self):
        self.assertEvaluate("1 - 2", -1)
        self.assertEvaluate("1.2 - 1.2", 0)
        self.assertEvaluate("1 - -2", 3)
        self.assertEvaluate("-1 - -2", 1)

    def testEvaluateSubMany(self):
        self.assertEvaluate("1", 1)
        self.assertEvaluate("1 - 2", -1)
        self.assertEvaluate("1 - 2 - 3", -4)
        self.assertEvaluate("1 - 2 - 3 - 4", -8)
        self.assertEvaluate("1 - 2 - 3 - 4 - 5", -13)

    def testParseMul(self):
        self.assertParse("1 * 2", asList("1", '*', "2"))
        self.assertParse("1 * 2 * 3", asList(asList("1", '*', "2"), '*', "3"))

    def testEvaluateMul(self):
        self.assertEvaluate("2 * 3", 6)
        self.assertEvaluate("2 * -4", -8)

    def testEvaluateMulMany(self):
        self.assertEvaluate("1 * 2", 2)
        self.assertEvaluate("1 * 2 * 3", 6)
        self.assertEvaluate("1 * 2 * 3 * 4", 24)
        self.assertEvaluate("1 * 2 * 3 * 4 * 5", 120)

    def testParseDiv(self):
        self.assertParse("1 / 2", asList("1", '/', "2"))
        self.assertParse("1 / 2 / 3", asList(asList("1", '/', "2"), '/', "3"))

    def testEvaluateDiv(self):
        self.assertEvaluate("12 / 3", 4)
        self.assertEvaluate("-16 / -4", 4)

    def testEvaluateDivMany(self):
        self.assertEvaluate("100 / 2", 50)
        self.assertEvaluate("100 / 2 / 2", 25)
        self.assertEvaluate("100 / 2 / 2 / 5", 5)
        self.assertEvaluate("100 / 2 / 2 / 5 / 5", 1)

    def testParsePow(self):
        self.assertParse("1 ^ 2", asList("1", '^', "2"))
        self.assertParse("1 ^ 2 ^ 3", asList("1", '^', asList("2", '^', "3")))

    def testEvaluatePow(self):
        self.assertEvaluate("2 ^ 3", 8)
        self.assertEvaluate("-2 ^ 3", -8)
        self.assertEvaluate("-2 ^ -3", -0.125)

    def testEvaluatePowMany(self):
        self.assertEvaluate("4 ^ 3", 64)
        self.assertEvaluate("4 ^ 3 ^ 2", 262144)
        self.assertEvaluate("4 ^ 3 ^ 2 ^ 1", 262144)
        self.assertEvaluate("4 ^ 3 ^ 2 ^ 1 ^ 0", 262144)

    def testParseParenthesis(self):
        self.assertParse("(1)", asList('(', "1", ')'))
        self.assertParse("(1 + 2)", asList('(', asList("1", '+', "2"), ')'))
        self.assertParse("((1))", asList('(', asList('(', "1", ')'), ')'))
        self.assertParse("((1 + 2))",
                         asList('(', asList('(', asList("1", '+', "2"), ')'), ')'))
        self.assertParse("2 * (3 + 4)",
                         asList("2", '*', asList('(', asList("3", '+', "4"), ')')))
        self.assertParse("(2 + 3) * 4",
                         asList(asList('(', asList("2", '+', "3"), ')'), '*', "4"))

    def testEvaluateParenthesis(self):
        self.assertEvaluate("(1)", 1)
        self.assertEvaluate("(1 + 2)", 3)
        self.assertEvaluate("((1))", 1)
        self.assertEvaluate("((1 + 2))", 3)
        self.assertEvaluate("2 * (3 + 4)", 14)
        self.assertEvaluate("(2 + 3) * 4", 20)
        self.assertEvaluate("6 / (2 + 4)", 1)
        self.assertEvaluate("(2 + 6) / 2", 4)

    def testParsePriority(self):
        self.assertParse("1 * 2 + 3", asList(asList("1", '*', "2"), '+', "3"))
        self.assertParse("1 + 2 * 3", asList("1", '+', asList("2", '*', "3")))

    def testEvaluatePriority(self):
        self.assertEvaluate("2 * 3 + 4", 10)
        self.assertEvaluate("2 + 3 * 4", 14)
        self.assertEvaluate("6 / 3 + 4", 6)
        self.assertEvaluate("2 + 6 / 2", 5)

    def testParsePostfixAdd(self):
        self.assertParse("0++", asList("0", "++"))
        self.assertParse("0++++", asList(asList("0", "++"), "++"))

    def testEvaluatePostfixAdd(self):
        self.assertEvaluate("0++", 1)
        self.assertEvaluate("0++++", 2)
        self.assertEvaluate("0++++++", 3)
        self.assertEvaluate("0+++1", 2)
        self.assertEvaluate("0+++++1", 3)
        self.assertEvaluate("0+++++++1", 4)

    def testParsePostfixSub(self):
        self.assertParse("0--", asList("0", "--"))
        self.assertParse("0----", asList(asList("0", "--"), "--"))

    def testEvaluatePostfixSub(self):
        self.assertEvaluate("1--", 0)
        self.assertEvaluate("2----", 0)
        self.assertEvaluate("3------", 0)
        self.assertEvaluate("2---1", 0)
        self.assertEvaluate("3-----1", 0)
        self.assertEvaluate("4-------1", 0)

    def testParsePrefixNegate(self):
        self.assertParse("-0", asList('-', "0"))
        self.assertParse("--0", asList('-', asList('-', "0")))

    def testEvaluatePrefixNegate(self):
        self.assertEvaluate("1", 1)
        self.assertEvaluate("-1", -1)
        self.assertEvaluate("--1", 1)
        self.assertEvaluate("---1", -1)


def asList(*x): return list(x)

import unittest
from petitparser import character, Parser, string

of = character.of


class Assertions(unittest.TestCase):
    def assert_success(self, parser: Parser, input: str, expected, position=None):
        if position is None:
            position = len(input)

        result = parser.parse(input)
        self.assertTrue(result.is_success, 'Expected parse success')
        self.assertFalse(result.is_failure, 'Expected parse success')
        self.assertEqual(position, result.position, 'Position')
        self.assertEqual(expected, result.value, 'Result')
        self.assertIsNone(result.message, 'No message expected')
        self.assertEqual(
            position, parser.fast_parse_on(input, 0), 'Fast parse')
        self.assertTrue(parser.accept(input), 'Accept')

    def assert_failure(self, parser: Parser, input: str, position: int = 0, message: str = None):
        if isinstance(position, str):
            message = position
            position = 0
        result = parser.parse(input)
        self.assertFalse(result.is_success, 'Expected parse failure')
        self.assertTrue(result.is_failure, 'Expected parse failure')
        self.assertEqual(position, result.position, 'Position')
        if message is not None:
            self.assertEqual(message, result.message, 'Message')
        self.assertEqual(-1,
                         parser.fast_parse_on(input, 0), 'Fast parse')
        self.assertFalse(parser.accept(input), 'Accept')

        self.assertRaises(Exception, lambda: result.value)


class ParsingTest(unittest.TestCase):
    def test_parse(self):
        parser = character.of('a')
        self.assertTrue(parser.parse('a').is_success)
        self.assertFalse(parser.parse('b').is_success)

    def test_accepts(self):
        parser = character.of('a')
        self.assertTrue(parser.accept('a'))
        self.assertFalse(parser.accept('b'))

    def test_matches(self):
        parser = character.digit().seq(character.digit()).flatten()
        expected = ['12', '23', '45']
        actual = parser.matches('a123b45')
        self.assertEqual(expected, actual)

    def test_matches_skipping(self):
        parser = character.digit().seq(character.digit()).flatten()
        expected = ['12', '45']
        actual = parser.matches_skipping('a123b45')
        self.assertEqual(expected, actual)


class ParsersTest(Assertions):
    def test_and(self):
        parser = character.of('a').and_()
        self.assert_success(parser, 'a', 'a', 0)
        self.assert_failure(parser, 'b', message="'a' expected")
        self.assert_failure(parser, '')

    def test_choice2(self):
        parser = character.of('a').or_(character.of('b'))
        self.assert_success(parser, 'a', 'a')
        self.assert_success(parser, 'b', 'b')
        self.assert_failure(parser, 'c')
        self.assert_failure(parser, '')

    def test_choice3(self):
        parser = character.of('a').or_(
            character.of('b')).or_(character.of('c'))
        self.assert_success(parser, 'a', 'a')
        self.assert_success(parser, 'b', 'b')
        self.assert_success(parser, 'c', 'c')
        self.assert_failure(parser, 'd')
        self.assert_failure(parser, '')

    def test_end_of_input(self):
        parser = character.of('a').end()
        self.assert_failure(parser, '', 0)
        self.assert_success(parser, 'a', 'a')
        self.assert_failure(parser, 'aa', 1)

    def test_settable(self):
        parser = character.of('a').settable()
        self.assert_success(parser, 'a', 'a')
        self.assert_failure(parser, 'b', 0)
        parser.set(character.of('b'))
        self.assert_success(parser, 'b', 'b')
        self.assert_failure(parser, 'a', 0)

    def test_flatten1(self):
        parser = character.digit().repeat(2, -1).flatten('gimme a number')
        self.assert_failure(parser, '', 0, 'gimme a number')
        self.assert_failure(parser, 'a', 0, 'gimme a number')
        self.assert_failure(parser, '1', 0, 'gimme a number')
        self.assert_failure(parser, '1a', 0, 'gimme a number')
        self.assert_success(parser, '12', '12')
        self.assert_success(parser, '123', '123')
        self.assert_success(parser, '1234', '1234')

    def test_map(self):
        parser = character.digit().map(int)
        self.assert_success(parser, '1', 1)
        self.assert_success(parser, '4', 4)
        self.assert_success(parser, '9', 9)
        self.assert_failure(parser, '')
        self.assert_failure(parser, 'a')

    def testPick(self):
        parser = character.digit().seq(character.letter()).pick(1)
        self.assert_success(parser, "1a", 'a')
        self.assert_success(parser, "2b", 'b')
        self.assert_failure(parser, "")
        self.assert_failure(parser, "1", 1)
        self.assert_failure(parser, "12", 1)

    def testPickLast(self):
        parser = character.digit().seq(character.letter()).pick(-1)
        self.assert_success(parser, "1a", 'a')
        self.assert_success(parser, "2b", 'b')
        self.assert_failure(parser, "")
        self.assert_failure(parser, "1", 1)
        self.assert_failure(parser, "12", 1)

    def testPermute(self):
        parser = character.digit().seq(character.letter()).permute(1, 0)
        self.assert_success(parser, "1a", asList('a', '1'))
        self.assert_success(parser, "2b", asList('b', '2'))
        self.assert_failure(parser, "")
        self.assert_failure(parser, "1", 1)
        self.assert_failure(parser, "12", 1)

    def testPermuteLast(self):
        parser = character.digit().seq(character.letter()).permute(-1, 0)
        self.assert_success(parser, "1a", asList('a', '1'))
        self.assert_success(parser, "2b", asList('b', '2'))
        self.assert_failure(parser, "")
        self.assert_failure(parser, "1", 1)
        self.assert_failure(parser, "12", 1)

    def testNeg1(self):
        parser = character.digit().neg()
        self.assert_failure(parser, "1", 0)
        self.assert_failure(parser, "9", 0)
        self.assert_success(parser, "a", 'a')
        self.assert_success(parser, " ", ' ')
        self.assert_failure(parser, "", 0)

    def testNeg2(self):
        parser = character.digit().neg("no digit expected")
        self.assert_failure(parser, "1", 0, "no digit expected")
        self.assert_failure(parser, "9", 0, "no digit expected")
        self.assert_success(parser, "a", 'a')
        self.assert_success(parser, " ", ' ')
        self.assert_failure(parser, "", 0, "no digit expected")

    def testNeg3(self):
        parser = string.of("foo").neg("no foo expected")
        self.assert_failure(parser, "foo", 0, "no foo expected")
        self.assert_failure(parser, "foobar", 0, "no foo expected")
        self.assert_success(parser, "f", 'f')
        self.assert_success(parser, " ", ' ')

    def testNot(self):
        parser = of('a').not_("not a expected")
        self.assert_failure(parser, "a", "not a expected")
        self.assert_success(parser, "b", None, 0)
        self.assert_success(parser, "", None)

    def testOptional(self):
        parser = of('a').optional()
        self.assert_success(parser, "a", 'a')
        self.assert_success(parser, "b", None, 0)
        self.assert_success(parser, "", None)

    def testPlus(self):
        parser = of('a').plus()
        self.assert_failure(parser, "", "'a' expected")
        self.assert_success(parser, "a", asList('a'))
        self.assert_success(parser, "aa", asList('a', 'a'))
        self.assert_success(parser, "aaa", asList('a', 'a', 'a'))

    def testPlusGreedy(self):
        parser = character.word().plus_greedy(character.digit())
        self.assert_failure(parser, "", 0, "letter or digit expected")
        self.assert_failure(parser, "a", 1, "digit expected")
        self.assert_failure(parser, "ab", 1, "digit expected")
        self.assert_failure(parser, "1", 1, "digit expected")
        self.assert_success(parser, "a1", asList('a'), 1)
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "12", asList('1'), 1)
        self.assert_success(parser, "a12", asList('a', '1'), 2)
        self.assert_success(parser, "ab12", asList('a', 'b', '1'), 3)
        self.assert_success(
            parser, "abc12", asList('a', 'b', 'c', '1'), 4)
        self.assert_success(parser, "123", asList('1', '2'), 2)
        self.assert_success(parser, "a123", asList('a', '1', '2'), 3)
        self.assert_success(
            parser, "ab123", asList('a', 'b', '1', '2'), 4)
        self.assert_success(parser, "abc123", asList(
            'a', 'b', 'c', '1', '2'), 5)

    def testPlusLazy(self):
        parser = character.word().plus_lazy(character.digit())
        self.assert_failure(parser, "")
        self.assert_failure(parser, "a", 1, "digit expected")
        self.assert_failure(parser, "ab", 2, "digit expected")
        self.assert_failure(parser, "1", 1, "digit expected")
        self.assert_success(parser, "a1", asList('a'), 1)
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "12", asList('1'), 1)
        self.assert_success(parser, "a12", asList('a'), 1)
        self.assert_success(parser, "ab12", asList('a', 'b'), 2)
        self.assert_success(parser, "abc12", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "123", asList('1'), 1)
        self.assert_success(parser, "a123", asList('a'), 1)
        self.assert_success(parser, "ab123", asList('a', 'b'), 2)
        self.assert_success(parser, "abc123", asList('a', 'b', 'c'), 3)

    def testTimes(self):
        parser = of('a').times(2)
        self.assert_failure(parser, "", 0, "'a' expected")
        self.assert_failure(parser, "a", 1, "'a' expected")
        self.assert_success(parser, "aa", asList('a', 'a'))
        self.assert_success(parser, "aaa", asList('a', 'a'), 2)

    def testRepeat(self):
        parser = of('a').repeat(2, 3)
        self.assert_failure(parser, "", "'a' expected")
        self.assert_failure(parser, "a", 1, "'a' expected")
        self.assert_success(parser, "aa", asList('a', 'a'))
        self.assert_success(parser, "aaa", asList('a', 'a', 'a'))
        self.assert_success(parser, "aaaa", asList('a', 'a', 'a'), 3)

    def testRepeatMinError1(self):
        self.assertRaises(ValueError, lambda: of('a').repeat(-2, 5))

    def testRepeatMinError2(self):
        self.assertRaises(ValueError, lambda: of('a').repeat(3, 2))

    def testRepeatUnbounded(self):
        parser = of('a').repeat(2, -1)
        self.assert_success(parser, 'a' * 100000, ['a'] * 100000)

    def testRepeatGreedy(self):
        parser = character.word().repeat_greedy(character.digit(), 2, 4)
        self.assert_failure(parser, "", 0, "letter or digit expected")
        self.assert_failure(parser, "a", 1, "letter or digit expected")
        self.assert_failure(parser, "ab", 2, "digit expected")
        self.assert_failure(parser, "abc", 2, "digit expected")
        self.assert_failure(parser, "abcd", 2, "digit expected")
        self.assert_failure(parser, "abcde", 2, "digit expected")
        self.assert_failure(parser, "1", 1, "letter or digit expected")
        self.assert_failure(parser, "a1", 2, "digit expected")
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(
            parser, "abcd1", asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde1", 2, "digit expected")
        self.assert_failure(parser, "12", 2, "digit expected")
        self.assert_success(parser, "a12", asList('a', '1'), 2)
        self.assert_success(parser, "ab12", asList('a', 'b', '1'), 3)
        self.assert_success(
            parser, "abc12", asList('a', 'b', 'c', '1'), 4)
        self.assert_success(
            parser, "abcd12", asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde12", 2, "digit expected")
        self.assert_success(parser, "123", asList('1', '2'), 2)
        self.assert_success(parser, "a123", asList('a', '1', '2'), 3)
        self.assert_success(
            parser, "ab123", asList('a', 'b', '1', '2'), 4)
        self.assert_success(
            parser, "abc123", asList('a', 'b', 'c', '1'), 4)
        self.assert_success(parser, "abcd123",
                            asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde123", 2, "digit expected")

    def testRepeatGreedyUnbounded(self):
        builderLetter = 'a' * 100000 + '1'
        builderDigit = '1' * 100000 + '1'
        listLetter = ['a'] * 100000
        listDigit = ['1'] * 100000

        parser = character.word().repeat_greedy(character.digit(), 2, -1)
        self.assert_success(parser, builderLetter, listLetter, len(listLetter))
        self.assert_success(parser, builderDigit, listDigit, len(listDigit))

    def testRepeatLazy(self):
        parser = character.word().repeat_lazy(character.digit(), 2, 4)
        self.assert_failure(parser, "", 0, "letter or digit expected")
        self.assert_failure(parser, "a", 1, "letter or digit expected")
        self.assert_failure(parser, "ab", 2, "digit expected")
        self.assert_failure(parser, "abc", 3, "digit expected")
        self.assert_failure(parser, "abcd", 4, "digit expected")
        self.assert_failure(parser, "abcde", 4, "digit expected")
        self.assert_failure(parser, "1", 1, "letter or digit expected")
        self.assert_failure(parser, "a1", 2, "digit expected")
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(
            parser, "abcd1", asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde1", 4, "digit expected")
        self.assert_failure(parser, "12", 2, "digit expected")
        self.assert_success(parser, "a12", asList('a', '1'), 2)
        self.assert_success(parser, "ab12", asList('a', 'b'), 2)
        self.assert_success(parser, "abc12", asList('a', 'b', 'c'), 3)
        self.assert_success(
            parser, "abcd12", asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde12", 4, "digit expected")
        self.assert_success(parser, "123", asList('1', '2'), 2)
        self.assert_success(parser, "a123", asList('a', '1'), 2)
        self.assert_success(parser, "ab123", asList('a', 'b'), 2)
        self.assert_success(parser, "abc123", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "abcd123",
                            asList('a', 'b', 'c', 'd'), 4)
        self.assert_failure(parser, "abcde123", 4, "digit expected")

    def testRepeatLazyUnbounded(self):
        builder = 'a' * 100000 + '1111'
        l = ['a'] * 100000
        parser = character.word().repeat_lazy(character.digit(), 2, -1)
        self.assert_success(parser, builder, l, len(l))

    def testSequence2(self):
        parser = of('a').seq(of('b'))
        self.assert_success(parser, "ab", asList('a', 'b'))
        self.assert_failure(parser, "")
        self.assert_failure(parser, "x")
        self.assert_failure(parser, "a", 1)
        self.assert_failure(parser, "ax", 1)

    def testSequence3(self):
        parser = of('a').seq(of('b')).seq(of('c'))
        self.assert_success(parser, "abc", asList('a', 'b', 'c'))
        self.assert_failure(parser, "")
        self.assert_failure(parser, "x")
        self.assert_failure(parser, "a", 1)
        self.assert_failure(parser, "ax", 1)
        self.assert_failure(parser, "ab", 2)
        self.assert_failure(parser, "abx", 2)

    def testStar(self):
        parser = of('a').star()
        self.assert_success(parser, "", asList())
        self.assert_success(parser, "a", asList('a'))
        self.assert_success(parser, "aa", asList('a', 'a'))
        self.assert_success(parser, "aaa", asList('a', 'a', 'a'))

    def testStarGreedy(self):
        parser = character.word().star_greedy(character.digit())
        self.assert_failure(parser, "", 0, "digit expected")
        self.assert_failure(parser, "a", 0, "digit expected")
        self.assert_failure(parser, "ab", 0, "digit expected")
        self.assert_success(parser, "1", asList(), 0)
        self.assert_success(parser, "a1", asList('a'), 1)
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "12", asList('1'), 1)
        self.assert_success(parser, "a12", asList('a', '1'), 2)
        self.assert_success(parser, "ab12", asList('a', 'b', '1'), 3)
        self.assert_success(
            parser, "abc12", asList('a', 'b', 'c', '1'), 4)
        self.assert_success(parser, "123", asList('1', '2'), 2)
        self.assert_success(parser, "a123", asList('a', '1', '2'), 3)
        self.assert_success(
            parser, "ab123", asList('a', 'b', '1', '2'), 4)
        self.assert_success(parser, "abc123", asList(
            'a', 'b', 'c', '1', '2'), 5)

    def testStarLazy(self):
        parser = character.word().star_lazy(character.digit())
        self.assert_failure(parser, "")
        self.assert_failure(parser, "a", 1, "digit expected")
        self.assert_failure(parser, "ab", 2, "digit expected")
        self.assert_success(parser, "1", asList(), 0)
        self.assert_success(parser, "a1", asList('a'), 1)
        self.assert_success(parser, "ab1", asList('a', 'b'), 2)
        self.assert_success(parser, "abc1", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "12", asList(), 0)
        self.assert_success(parser, "a12", asList('a'), 1)
        self.assert_success(parser, "ab12", asList('a', 'b'), 2)
        self.assert_success(parser, "abc12", asList('a', 'b', 'c'), 3)
        self.assert_success(parser, "123", asList(), 0)
        self.assert_success(parser, "a123", asList('a'), 1)
        self.assert_success(parser, "ab123", asList('a', 'b'), 2)
        self.assert_success(parser, "abc123", asList('a', 'b', 'c'), 3)

    def testToken(self):
        parser = of('a').star().token().trim()
        token = parser.parse(" aa ").value
        self.assertEqual(1, token.start)
        self.assertEqual(3, token.stop)
        self.assertEqual(asList('a', 'a'), token.value)

    def testTrim(self):
        parser = of('a').trim()
        self.assert_success(parser, "a", 'a')
        self.assert_success(parser, " a", 'a')
        self.assert_success(parser, "a ", 'a')
        self.assert_success(parser, " a ", 'a')
        self.assert_success(parser, "  a", 'a')
        self.assert_success(parser, "a  ", 'a')
        self.assert_success(parser, "  a  ", 'a')
        self.assert_failure(parser, "", "'a' expected")
        self.assert_failure(parser, "b", "'a' expected")
        self.assert_failure(parser, " b", 1, "'a' expected")
        self.assert_failure(parser, "  b", 2, "'a' expected")

    def testTrimCustom(self):
        parser = of('a').trim(of('*'))
        self.assert_success(parser, "a", 'a')
        self.assert_success(parser, "*a", 'a')
        self.assert_success(parser, "a*", 'a')
        self.assert_success(parser, "*a*", 'a')
        self.assert_success(parser, "**a", 'a')
        self.assert_success(parser, "a**", 'a')
        self.assert_success(parser, "**a**", 'a')
        self.assert_failure(parser, "", "'a' expected")
        self.assert_failure(parser, "b", "'a' expected")
        self.assert_failure(parser, "*b", 1, "'a' expected")
        self.assert_failure(parser, "**b", 2, "'a' expected")

    def testSeparatedBy(self):
        parser = of('a').separated_by(of('b'))
        self.assert_failure(parser, "", "'a' expected")
        self.assert_success(parser, "a", asList('a'))
        self.assert_success(parser, "ab", asList('a'), 1)
        self.assert_success(parser, "aba", asList('a', 'b', 'a'))
        self.assert_success(parser, "abab", asList('a', 'b', 'a'), 3)
        self.assert_success(
            parser, "ababa", asList('a', 'b', 'a', 'b', 'a'))
        self.assert_success(parser, "ababab", asList(
            'a', 'b', 'a', 'b', 'a'), 5)

    def testDelimitedBy(self):
        parser = of('a').delimited_by(of('b'))
        self.assert_failure(parser, "")
        self.assert_success(parser, "a", asList('a'))
        self.assert_success(parser, "ab", asList('a', 'b'))
        self.assert_success(parser, "aba", asList('a', 'b', 'a'))
        self.assert_success(parser, "abab", asList('a', 'b', 'a', 'b'))
        self.assert_success(parser, "ababa", asList('a', 'b', 'a', 'b', 'a'))
        self.assert_success(parser, "ababab", asList(
            'a', 'b', 'a', 'b', 'a', 'b'))


def asList(*args):
    return list(args)

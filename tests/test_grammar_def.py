from petitparser.tools.grammar_definition import GrammarParser
from petitparser.parser.primitive import EpsilonParser
import unittest

from petitparser import GrammarDefinition, ref, action, character, epsilon


class GrammarDefinitionTest(unittest.TestCase):

    class ListGrammarDefinition(GrammarDefinition):
        start = ref('list').end()
        list = (ref('element')
                & character.of(',')
                & ref('list')) | ref('element')
        element = character.digit().plus().flatten()

    class ListParserDefinition(ListGrammarDefinition):
        element = action(int)

    class BuggedGrammarDefinition(GrammarDefinition):
        start = epsilon()

        directRecursion1 = ref('directRecursion1')

        indirectRecursion1 = ref('indirectRecursion2')
        indirectRecursion2 = ref('indirectRecursion3')
        indirectRecursion3 = ref('indirectRecursion1')

        delegation1 = ref('delegation2')
        delegation2 = ref('delegation3')
        delegation3 = epsilon()

        unknownReference = ref('unknown')

    class LambdaGrammar(GrammarDefinition):
        start = ref('expression').end()
        expression = ref('variable') | ref('abstraction') | ref('application')
        variable = (
            character.letter()
            & character.word().star()).flatten().trim()
        abstraction = (
            character.of('\\').trim()
            & ref('variable')
            & character.of('.').trim()
            & ref('expression'))
        application = (
            character.of('(').trim()
            & ref('expression')
            & ref('expression')
            & character.of(')').trim()
        )

    class HelperGrammar(GrammarDefinition):

        x = character.digit()

        def _helper():
            return ref('x') & ref('x')

        y = _helper()

    grammarDefinition = ListGrammarDefinition()
    parserDefinition = ListParserDefinition()
    buggedDefinition = BuggedGrammarDefinition()

    def test_grammar(self):
        parser = self.grammarDefinition.build()
        self.assertEqual(
            ['1', ',', '2'],
            parser.parse('1,2').value)
        self.assertEqual(
            ['1', ',', ['2', ',', '3']],
            parser.parse('1,2,3').value)

    def test_parser(self):
        parser = self.parserDefinition.build()
        self.assertEqual([1, ',', 2], parser.parse('1,2').value)
        self.assertEqual([1, ',', [2, ',', 3]], parser.parse('1,2,3').value)

    def test_direct_recursion(self):
        self.assertRaises(
            Exception,
            self.buggedDefinition.build,
            'directRecursion1'
        )

    def test_indirect_recursion1(self):
        self.assertRaises(
            Exception,
            self.buggedDefinition.build,
            'indirectRecursion2'
        )

    def test_indirect_recursion3(self):
        self.assertRaises(
            Exception,
            self.buggedDefinition.build,
            'indirectRecursion3'
        )

    def test_unknown_reference_outside(self):
        self.assertRaises(
            Exception,
            self.buggedDefinition.build,
            'unknown'
        )

    def test_unknown_reference_inside(self):
        self.assertRaises(
            Exception,
            self.buggedDefinition.build,
            'unknownReference'
        )

    def test_delegation(self):
        self.assertIsInstance(
            self.buggedDefinition.build('delegation1'),
            EpsilonParser
        )
        self.assertIsInstance(
            self.buggedDefinition.build('delegation2'),
            EpsilonParser
        )
        self.assertIsInstance(
            self.buggedDefinition.build('delegation3'),
            EpsilonParser
        )

    def test_lambda_grammar(self):
        parser = GrammarParser(self.LambdaGrammar)
        self.assertTrue(parser.accept('x'))
        self.assertTrue(parser.accept('xy'))
        self.assertTrue(parser.accept('x12'))
        self.assertTrue(parser.accept('\\x.y'))
        self.assertTrue(parser.accept('\\x.\\y.z'))
        self.assertTrue(parser.accept('(x x)'))
        self.assertTrue(parser.accept('(x y)'))
        self.assertTrue(parser.accept('(x (y z))'))
        self.assertTrue(parser.accept('((x y) z)'))

    def test_helper_method(self):
        parser = GrammarParser(self.HelperGrammar, 'y')
        self.assertTrue(parser.accept('12'))
        self.assertFalse(parser.accept('1x'))

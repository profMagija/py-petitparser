# PetitParser for Python

Grammars for programming languages are traditionally specified statically. They are hard to compose and reuse due to ambiguities that inevitably arise. PetitParser combines ideas from scannnerless parsing, parser combinators, parsing expression grammars (PEG) and packrat parsers to model grammars and parsers as objects that can be reconfigured dynamically.

PetitParser was originally implemented in Smalltalk. This Python implementation (and parts of the README as well) is mostly a direct translation of the [Java version](https://github.com/petitparser/java-petitparser).

## Tutorial

### Writing a simple grammar

Writing grammars with PetitParser is as simple as writing python code. For example to write a grammar that can parse identifiers that start with a letter followed by zero or more letters or digits is defined as follows:

```python
from petitparser import character as c
ident = c.letter() & (c.letter() | c.digit()).star()
```

### Parsing some input

To parse a string we can use the `Parser.parse` method:

```python
id1 = ident.parse('yeah')
id2 = ident.parse('f12')
```

The method returns a `Result` which is either a `Success` or a `Failure` (can be checked with `Result.is_success` / `Result.is_failure` properties). If it's a success (like above) we can get the result with `Result.value` property:

```python
print(id1.value) # ['y', ['e', 'a', 'h']]
print(id2.value) # ['f', ['1', '2']]
```

If we try to parse somehing invalid, we get an instance of `Failure`

```python
id3 = ident.parse('123')
print(id3.message)  # letter expected
print(id3.position) # 0
```

If you are only interested if a string matches or not, you can use `Parser.accept()` method:

```python
print(ident.accept('foo')) # True
print(ident.accept('123')) # False
```

### Diferent kinds of parsers



PetitParser provide a large set of ready-made parser that you can compose to consume and transform arbitrarily complex languages. The terminal parsers are the most simple ones. We've already seen a few of those:

* `petitparser.character.of('a')` parses a single character `a`.
* `petitparser.string.of('abc')` parses the string `abc`.
* `petitparser.character.any()` parses any character 
* `petitparser.character.digit()` parses any digit (using `str.isdigit`)
* `petitparser.character.letter()` parses any leter (using `str.isalpha`) 
* `petitparser.character.word()` parses any letter or figit (using `str.isalnum`) 

Other parsers are available in `petitparser.character` and `petitparser.string` modules.

So instead of using the letter and digit predicate, we could have written our identifier parser like this:

```python
ident = c.letter() & c.word().star()
```

Next set of parsers are used to combine other persers together:

* `p1.seq(p2)` or `p1 & p2`: parses `p1` followed by `p2`
* `p1.or_(p2)` or `p1 | p2`: pasres `p1`, and if that fails parses `p2` (ordered choice)
* `p.star()` parses `p` zero or more times
* `p.plus()` parses `p` one or more times
* `p.optional()` parses `p` if possible
* `p[m:n]` parses `p` between `m` (default 0) and `n` (default unlimited) times
* `p.and_()` or `+p` parses `p`, but does not consume input
* `p.not_()` or `-p` parses `p` and succeeds if that fails, but does not consume input.
* `p.end()` parses `p` and succeeds at the end of input.

> _Note:_ some methods are suffixe with an underscore to keep their original names, and to not conflict with the Python keywords

To attach an action or transformation to a parser we can use the following methods:

* `p.map(lambda x: ...)` performs the transformation given by the function.
* `p.pick(n)` returns the `n`-th element of the list `p` returns.
* `p.flatten()` creates a string from the result of `p`.
* `p.token()` creates a `Token` from the result of `p`.
* `p.trim()` trims whitespace before and after `p`.

To return the string of the parsed identifier, we can modify our parser like this:

```python
ident = (c.letter() & c.word().star()).flatten()
```

To conveniently find all matches in a given input string you can use `Parser.matches_skipping()`:

```python
print(ident.matches_skipping('foo 123 bar4')) # ['foo', 'bar4']
```

### Writing more complicated grammar

Now we are able to write a more complicated grammar for evaluating simple arithmetic expressions. Within a file we start with the grammar for a number (actually an integer):

```python
number = c.digit().plus().flatten().trim().map(int)
```

Then we define the productions for addition and multiplication in order of precedence. Note that we instantiate the productions with undefined parsers upfront, because they recursively refer to each other. Later on we can resolve this recursion by setting their reference:

```python
from petitparser import SettableParser
term = SettableParser.undefined()
prod = SettableParser.undefined()
prim = SettableParser.undefined()

term.set(
    (prod & c.of('+').trim() & term).map(lambda x: x[0] + x[2])
    | prod
)

prod.set(
    (prim & c.of('*').trim() & prod).map(lambda x: x[0] * x[2])
    | prim
)

prim.set(
    (c.of('(').trim() & term & c.of(')').trim())
        .map(lambda x: x[1])
    | number
)
```

To make sure that our parser consumes all input we wrap it with the `end()` parser into the start production:

```python
start = term.end()
```

That's it, now we can test our parser and evaluator:

```python
print(start.parse('1 + 2 * 3').value)   # 7
print(start.parse('(1 + 2) * 3').value) # 9
```

As an exercise we could extend the parser to also accept negative numbers and floating point numbers, not only integers. Furthermore it would be useful to support subtraction and division as well. All these features can be added with a few lines of PetitParser code.

### Using the Expression Builder

Writing such expression parsers is pretty common and can be quite tricky to get right. To simplify things, PetitParser comes with a builder that can help you to define such grammars easily. It supports the definition of operator precedence; and prefix, postfix, left- and right-associative operators.

```python
from petitparser import ExpressionBuilder
builder = ExpressionBuilder()
```

Then we define the operator-groups in descending precedence. The highest precedence are the literal numbers themselves. This time we accept floating point numbers, not just integers. In the same group we add support for parenthesis (note that the wrapper action receives 3 arguments, including both wrapper parts):

```python
builder.group()\
    .primitive((
            c.digit().plus()
            & (c.of('.') & c.digit().plus()).optional()
        ).flatten().trim().map(float))\
    .wrapper(
        c.of('(').trim(),
        c.of(')').trim(),
        lambda _l, x, _r: x
    )
```

Then come the normal arithmetic operators. Note, that the action blocks receive both of the terms and the parsed operator in the order they appear in the parsed input, and the operator:

```python
# negation is a prefix operator
builder.group()\
    .prefix(c.of('-'), lambda _op, x: -x)

# power is right-associative
builder.group()\
    .right(c.of('^'), lambda lhs, _op, rhs: lhs ** rhs)

# multiplication and addition are left-assicoative
builder.group()\
    .left(c.of('*'), lambda lhs, _op, rhs: lhs * rhs)\
    .left(c.of('/'), lambda lhs, _op, rhs: lhs / rhs)
builder.group()\
    .left(c.of('+'), lambda lhs, _op, rhs: lhs + rhs)\
    .left(c.of('-'), lambda lhs, _op, rhs: lhs - rhs)
```

Finally we can build the parser:

```python
parser = builder.build().end()
```

After executing the above code we get an efficient parser that correctly evaluates expressions like:

```python
print(parser.parse('-8').value)     # -8.0
print(parser.parse('1+2*3').value)  # 7
print(parser.parse('1*2+3').value)  # 5
print(parser.parse('8/4/2').value)  # 1
print(parser.parse('2^2^3').value)  # 256
```

### Using Grammar Definition

Using the `GrammarDefinition` class is a bit different than in other PetitParser implementations, and is done so to make it simpler to write grammars. It uses some metaclass trickery to allow simple definitions of complex grammars.

Here is a lambda expression grammar in PEG syntax:

```
expression  ::= variable / abstraction / application
variable    ::= letter word*
abstraction ::= '\' variable '.' expression
application ::= '(' expression expression ')'

start       ::= expression EOF
```

And here it is translated into PetitParser Grammar Definition

```python
from petitparser import GrammarDefinition, ref
from petitparser import character as c

class LambdaGrammar(GrammarDefinition):
    start = ref('expression').end()
    
    expression = (
        ref('variable')
        | ref('abstraction')
        | ref('application')
    )
    
    variable = (
        c.letter()
        & c.word().star()
    ).flatten().trim()
    
    abstraction = (
        c.of('\\').trim()
        & ref('variable')
        & c.of('.').trim()
        & ref('expression'))

    application = (
        c.of('(').trim()
        & ref('expression')
        & ref('expression')
        & c.of(')').trim()
    )
```

## License

The MIT License, see [LICENSE](./LICENSE)
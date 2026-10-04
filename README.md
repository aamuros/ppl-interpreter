# HLInt

HLInt is a small educational interpreter for the hypothetical language **HL**,
written in Python 3.10 or newer using only the standard library. An interpreter
reads a program, checks it, and directly carries out its instructions. HLInt does
not generate machine code or execute HL by translating it into Python `eval`.

## Run HLInt

From this directory:

```sh
python3 hlint.py PROG1.HL
python3 hlint.py PROG2.HL
python3 hlint.py PROG3.HL
```

Pass any source-file path as the single argument. Each run writes `NOSPACES.TXT`
and `RES_SYM.TXT` **beside the source file**, replacing the previous artifacts in
that directory. Successful validation prints `NO ERROR(S) FOUND`, then each HL
output statement prints one line. Errors print `ERROR` followed by a diagnostic
with the source line and column. The process returns 0 for success and 1 for an
error. File-reading/writing errors also produce `ERROR` and a diagnostic.

## HL syntax

```text
x: integer;
y: double;
x := 3 + 2;
y = 1.25;
output << "Hello world";
output << x;
output << x + y;
if (x != 0)
    output << x - 1;
```

- Declare variables using `name: integer;` or `name: double;` before use.
- Assign using either `:=` or `=`. Integer values can be assigned to doubles;
  double expressions cannot be assigned to integers, even when mathematically whole.
- Use `+` and `-` with numeric literals and variables. Both operators have equal
  precedence and associate left to right: `8-3-2` evaluates to `3`.
- Output a double-quoted string, variable, or arithmetic expression.
- An `if` uses `<`, `>`, `==`, or `!=` between numeric expressions and controls
  exactly one following statement. A nested `if` is also a statement.
- Keywords and identifiers are case-insensitive: `If`, `if`, `X`, and `x` are
  normalized internally to lowercase. String content retains its original case.
- Whitespace between tokens is allowed. Statements end with semicolons; an `if`
  has no additional semicolon beyond the one ending its body.

Numbers are whole digits (`5`) or digits with a fractional part (`2.35`). A
negative result can be written as subtraction, such as `0-5`. Following the
requested grammar, unary minus, parentheses around arithmetic, multiplication,
division, exponent notation, comments, string escapes, multiline strings, braces,
and `else` are not supported. Strings are only standalone output operands.

## Interpreter phases

```text
HL source → preprocessing → lexer → parser → AST → semantic checking → evaluator
```

| File | Responsibility |
| --- | --- |
| `hlint.py` | Read a file, write artifacts, coordinate validation and execution |
| `hl/preprocess.py` | Produce the space-removal artifact |
| `hl/lexer.py` | Recognize tokens and record their source positions |
| `hl/parser.py` | Check grammar and build the AST with recursive descent |
| `hl/ast.py` | Small data classes representing statements and expressions |
| `hl/semantic.py` | Check declarations/types and build the symbol table |
| `hl/evaluator.py` | Evaluate expressions and execute statements |
| `hl/errors.py` | Common source diagnostic exception |
| `tests/test_hlint.py` | Language and file/artifact tests |

### Preprocessing and NOSPACES.TXT

Preprocessing removes whitespace outside strings, except line breaks. It preserves
spaces inside strings so `"Hello world"` retains its meaning. Original casing is
also preserved. For example:

```text
x: integer;
output << "Hello world";
```

becomes:

```text
x:integer;
output<<"Hello world";
```

The lexer reads the **original source**, not `NOSPACES.TXT`. Removing all spaces
could join tokens and change the program; keeping this artifact separate also
preserves useful original line/column locations for diagnostics.

### Lexer and tokens

A lexer groups characters into tokens. Each token contains a kind, lexeme
(recognized text), value, and one-based line/column. For `x:=5;`, the kinds are
`IDENTIFIER`, `ASSIGN`, `INTEGER_LITERAL`, and `SEMICOLON`.

HLInt recognizes identifier, integer/double/string literal, keyword, punctuation,
arithmetic, assignment, output, comparison, and parenthesis tokens. An `EOF`
token marks the end. Two-character symbols are recognized first, so `<<` is one
output operator and `==` is one comparison rather than two assignments. Unknown
characters, malformed numbers, and unmatched quotes raise lexical errors.

### RES_SYM.TXT

This is a tab-separated list with **no header**, one keyword or symbol per line:

```text
line:column<TAB>TOKEN_KIND<TAB>lexeme
```

For `x: integer;`:

```text
1:2	COLON	:
1:4	INTEGER	integer
1:11	SEMICOLON	;
```

Actual separators are tab characters. Keywords are lowercase; symbols retain
their spelling, including the distinction between `=` and `:=`. Entries retain
source order and repetitions. Identifiers, literals, and `EOF` are omitted;
keyword-looking text inside a string is not listed. On a lexical error, the file
contains the reserved tokens detected before that error. On syntax or semantic
errors, it contains all lexically detected reserved tokens.

### Parser and AST

The parser uses manually written recursive-descent functions: each handles a
grammar rule, consumes tokens, and reports unexpected tokens or missing
punctuation. No parser generator is involved.

The abstract syntax tree (AST) describes the program's meaning without retaining
all its punctuation. Its node classes are `Program`, `VariableDeclaration`,
`Assignment`, `OutputStatement`, `IfStatement`, `BinaryExpression`,
`ComparisonExpression`, `NumberLiteral`, `StringLiteral`, and `Identifier`.
For `output<<3+2;`, an `OutputStatement` contains a `BinaryExpression` with two
`NumberLiteral` children. Each node retains a token for diagnostic locations.

### Symbol table and semantic checking

The symbol table is a Python dictionary keyed by normalized variable names. Each
entry stores the declared type and current value. Declarations initially create
integer zero or decimal zero.

Semantic checking visits the entire AST **before execution**, rejecting
undeclared variables, redeclarations, and double-to-integer assignments. It also
checks the body of a false `if`; an invalid program produces no HL output.
Types are inferred from expressions: an expression with a double operand has
type `double`; otherwise numeric expressions have type `integer`.

### Evaluation/execution

The evaluator walks statements in order, computes expression values, updates
symbol-table entries on assignment, prints outputs, and executes an `if` body
only when its comparison is true. Python integers represent HL integers;
standard-library `Decimal` values represent HL doubles, avoiding binary
floating-point surprises such as `0.1+0.2`. Decimal addition/subtraction uses
enough precision for the operand digits. Stored values and comparisons retain
their precision; rounding happens only when displaying output.

## Decisions where the assignment was unspecified

- Variables start at zero, allowing a declared variable to be read before an
  assignment. Duplicate declarations are errors.
- There is one global symbol table. Declarations are processed statically in
  source order, including declarations inside `if` bodies. Such a declaration
  exists even if the condition is false; it still cannot be used before its
  source declaration. Executing a declaration requires no additional action.
- A double expression assigned to an integer is rejected rather than truncated.
- Double output rounds half away from zero to at most two fractional digits,
  dropping trailing zeros: `1.235` prints `1.24`, `2.00` prints `2`, and
  `0.1+0.2` prints `0.3`. Rounded negative zero prints `0`.
- Each output statement prints a newline.
- Space removal preserves string whitespace and line breaks. Reserved-symbol
  output includes every occurrence with its original location.
- Artifacts are written beside the source file, and later runs replace them.
  Both are produced before syntax/semantic validation; lexical errors leave a
  partial reserved-symbol list. An unreadable source cannot produce artifacts.

## Supplied examples

| Source | Behavior | Output after success message |
| --- | --- | --- |
| `PROG1.HL` | Declare and assign an integer, then output it | `5` |
| `PROG2.HL` | Add an integer and a double | `4.25` |
| `PROG3.HL` | Output an integer when `x<5` is true | `3` |

## Tests

```sh
python3 -m unittest discover -s tests -v
```

The tests cover all supplied programs, declarations, both assignment spellings,
numeric arithmetic and precision, strings/variables/expressions, case-insensitive
names, all comparisons with true/false conditions, nested statements, source
locations, AST construction, lexical/syntax/semantic errors, and artifact
contents on successful and failing runs. File tests use temporary directories.

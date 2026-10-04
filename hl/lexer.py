from dataclasses import dataclass
from decimal import Decimal

from .errors import HLError


KEYWORDS = {word: word.upper() for word in ("integer", "double", "if", "output")}
SYMBOLS = {
    ":=": "ASSIGN", "=": "ASSIGN", "<<": "OUTPUT_OPERATOR",
    "==": "EQUAL", "!=": "NOT_EQUAL", ":": "COLON", ";": "SEMICOLON",
    "+": "PLUS", "-": "MINUS", "<": "LESS", ">": "GREATER",
    "(": "LPAREN", ")": "RPAREN",
}
RESERVED_KINDS = set(KEYWORDS.values()) | set(SYMBOLS.values())


@dataclass
class Token:
    kind: str
    lexeme: str
    value: str | int | Decimal | None
    line: int
    column: int


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def advance(self) -> str:
        character = self.source[self.position]
        self.position += 1
        if character == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return character

    def peek(self) -> str:
        return self.source[self.position:self.position + 1]

    def tokenize(self) -> list[Token]:
        while self.position < len(self.source):
            if self.peek().isspace():
                self.advance()
                continue
            start, line, column = self.position, self.line, self.column
            character = self.peek()
            if character.isalpha() or character == "_":
                while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
                    self.advance()
                lexeme = self.source[start:self.position].lower()
                kind, value = KEYWORDS.get(lexeme, "IDENTIFIER"), lexeme
            elif character.isdecimal():
                while self.peek() and self.peek().isdecimal():
                    self.advance()
                kind = "INTEGER_LITERAL"
                if self.peek() == ".":
                    kind = "DOUBLE_LITERAL"
                    self.advance()
                    if not self.peek() or not self.peek().isdecimal():
                        raise HLError("invalid number: expected digits after '.'", line, column)
                    while self.peek() and self.peek().isdecimal():
                        self.advance()
                if self.peek() and (self.peek().isalpha() or self.peek() in "._"):
                    raise HLError("invalid number", line, column)
                lexeme = self.source[start:self.position]
                value = int(lexeme) if kind == "INTEGER_LITERAL" else Decimal(lexeme)
            elif character == '"':
                self.advance()
                while self.peek() and self.peek() not in ('"', "\n", "\r"):
                    self.advance()
                if self.peek() != '"':
                    raise HLError("unmatched string literal", line, column)
                self.advance()
                lexeme = self.source[start:self.position]
                kind, value = "STRING_LITERAL", lexeme[1:-1]
            else:
                # Check two-character symbols first so '<' never consumes '<<'.
                lexeme = self.source[start:start + 2]
                if lexeme not in SYMBOLS:
                    lexeme = character
                if lexeme not in SYMBOLS:
                    raise HLError(f"invalid token {character!r}", line, column)
                for _ in lexeme:
                    self.advance()
                kind, value = SYMBOLS[lexeme], lexeme
            self.tokens.append(Token(kind, lexeme, value, line, column))
        self.tokens.append(Token("EOF", "", None, self.line, self.column))
        return self.tokens


def reserved_symbols(tokens: list[Token]) -> str:
    """Retain repetitions and source order; omit ordinary identifiers/literals."""
    return "".join(
        f"{token.line}:{token.column}\t{token.kind}\t{token.lexeme}\n"
        for token in tokens if token.kind in RESERVED_KINDS
    )

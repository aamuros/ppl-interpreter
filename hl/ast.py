from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .lexer import Token


@dataclass
class Node:
    # Keep one token for diagnostics; the AST does not retain punctuation.
    token: Token


@dataclass
class Program(Node):
    statements: list[Statement]


@dataclass
class VariableDeclaration(Node):
    name: str
    type_name: str


@dataclass
class Assignment(Node):
    name: str
    expression: Expression


@dataclass
class OutputStatement(Node):
    expression: Expression


@dataclass
class IfStatement(Node):
    condition: ComparisonExpression
    body: Statement


@dataclass
class BinaryExpression(Node):
    left: Expression
    operator: str
    right: Expression


@dataclass
class ComparisonExpression(Node):
    left: Expression
    operator: str
    right: Expression


@dataclass
class NumberLiteral(Node):
    value: int | Decimal


@dataclass
class StringLiteral(Node):
    value: str


@dataclass
class Identifier(Node):
    name: str


Statement = VariableDeclaration | Assignment | OutputStatement | IfStatement
Expression = BinaryExpression | NumberLiteral | StringLiteral | Identifier

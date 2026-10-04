class HLError(Exception):
    """A source error shared by the lexer, parser, and semantic checker."""

    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"line {line}, column {column}: {message}")

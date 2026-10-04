"""HLInt command-line entry point; all language phases live in hl/."""

import argparse
from pathlib import Path
from typing import Callable

from hl.errors import HLError
from hl.evaluator import Evaluator
from hl.lexer import Lexer, reserved_symbols
from hl.parser import Parser
from hl.preprocess import remove_spaces
from hl.semantic import SemanticChecker


def run_file(path: Path, emit: Callable[[str], None] = print) -> int:
    try:
        source = path.read_text(encoding="utf-8")
        (path.parent / "NOSPACES.TXT").write_text(remove_spaces(source), encoding="utf-8")
        lexer = Lexer(source)
        try:
            tokens = lexer.tokenize()
        finally:
            # On lexical failure, record the tokens detected before the error.
            (path.parent / "RES_SYM.TXT").write_text(reserved_symbols(lexer.tokens), encoding="utf-8")
        program = Parser(tokens).parse()
        symbols = SemanticChecker().check(program)
        emit("NO ERROR(S) FOUND")
        Evaluator(symbols, emit).execute(program)
        return 0
    except (HLError, OSError, UnicodeError, ValueError) as error:
        emit("ERROR")
        emit(str(error))
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute an HL source file.")
    parser.add_argument("source", type=Path, help="path to the .HL program")
    return run_file(parser.parse_args().source)


if __name__ == "__main__":
    raise SystemExit(main())

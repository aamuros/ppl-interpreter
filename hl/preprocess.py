def remove_spaces(source: str) -> str:
    """Produce an artifact without changing the source used by the lexer."""
    result = []
    in_string = False
    for character in source:
        if character == '"':
            in_string = not in_string
        if in_string or not character.isspace() or character in "\n\r":
            result.append(character)
    return "".join(result)

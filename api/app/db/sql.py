"""数据库 SQL 脚本解析工具。"""

from __future__ import annotations


def split_statements(script: str) -> list[str]:
    """按顶层分号拆分 SQL，保留字符串和 dollar quote 内的分号。"""
    statements: list[str] = []
    current: list[str] = []
    quote: str | None = None
    dollar_tag: str | None = None
    index = 0

    while index < len(script):
        char = script[index]
        following = script[index + 1] if index + 1 < len(script) else ""

        if quote is None and dollar_tag is None and char == "-" and following == "-":
            newline = script.find("\n", index)
            index = len(script) if newline == -1 else newline + 1
            current.append("\n")
            continue

        if quote is None and dollar_tag is None and char == "$":
            tag_end = script.find("$", index + 1)
            if tag_end != -1:
                candidate = script[index : tag_end + 1]
                tag_name = candidate[1:-1]
                if not tag_name or (
                    (tag_name[0].isalpha() or tag_name[0] == "_")
                    and all(char.isalnum() or char == "_" for char in tag_name[1:])
                ):
                    dollar_tag = candidate
                    current.append(candidate)
                    index = tag_end + 1
                    continue

        if dollar_tag is not None:
            if script.startswith(dollar_tag, index):
                current.append(dollar_tag)
                index += len(dollar_tag)
                dollar_tag = None
            else:
                current.append(char)
                index += 1
            continue

        if quote is not None:
            current.append(char)
            if char == quote:
                if following == quote:
                    current.append(following)
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        index += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return statements

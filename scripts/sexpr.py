"""Minimal S-expression reader/writer for KiCad files.

Representation: lists are Python lists, bare atoms are Sym, quoted strings are plain str.
"""


class Sym(str):
    """A bare (unquoted) atom such as a keyword or a number."""


def parse(text):
    """Parse a KiCad S-expression string and return the top-level list."""
    pos = 0
    n = len(text)
    stack = [[]]
    while pos < n:
        c = text[pos]
        if c in " \t\r\n":
            pos += 1
        elif c == "(":
            stack.append([])
            pos += 1
        elif c == ")":
            node = stack.pop()
            stack[-1].append(node)
            pos += 1
        elif c == '"':
            pos += 1
            buf = []
            while True:
                c = text[pos]
                if c == "\\":
                    nxt = text[pos + 1]
                    buf.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                    pos += 2
                elif c == '"':
                    pos += 1
                    break
                else:
                    buf.append(c)
                    pos += 1
            stack[-1].append("".join(buf))
        else:
            start = pos
            while pos < n and text[pos] not in ' \t\r\n()"':
                pos += 1
            stack[-1].append(Sym(text[start:pos]))
    return stack[0][0]


def _quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dumps(node, indent=0):
    """Serialize a node back to text (one list per line, tab indented)."""
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, str):
        return _quote(node)
    if isinstance(node, (int, float)):
        return fmt_num(node)
    if not any(isinstance(child, list) for child in node):
        return "(" + " ".join(dumps(child) for child in node) + ")"
    pad = "\t" * (indent + 1)
    parts = []
    head = []
    for child in node:
        if isinstance(child, list):
            parts.append(pad + dumps(child, indent + 1))
        elif not parts:
            head.append(dumps(child))
        else:
            parts.append(pad + dumps(child, indent + 1))
    return "(" + " ".join(head) + "\n" + "\n".join(parts) + "\n" + "\t" * indent + ")"


def fmt_num(value):
    """Format a number the way KiCad does (no trailing zeros, max 4 decimals)."""
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def find(node, key):
    """Return the first child list whose head is `key`, or None."""
    for child in node:
        if isinstance(child, list) and child and child[0] == key:
            return child
    return None


def find_all(node, key):
    """Return all child lists whose head is `key`."""
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

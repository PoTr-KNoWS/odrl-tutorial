#!/usr/bin/env python3
"""
Validate that ./robots.txt conforms to the ABNF grammar from RFC 9309
(Robots Exclusion Protocol).

Usage:
    python validate_robots.py [path]      # default: ./robots.txt

Exit codes:
    0  valid
    1  invalid
    2  could not read file / missing dependency

Requires the `abnf` package:  pip install abnf
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from abnf.parser import Rule as _Rule, ParseError, GrammarError
except ImportError:
    sys.stderr.write("This script requires the 'abnf' package: pip install abnf\n")
    sys.exit(2)


# RFC 9309 ABNF grammar for robots.txt.
ROBOTS_ABNF = r"""
robotstxt = *(group / emptyline)
group = startgroupline *(startgroupline / emptyline) *(rule / emptyline)
startgroupline = *WS "user-agent" *WS ":" *WS product-token EOL
rule = *WS ("allow" / "disallow") *WS ":" *WS (path-pattern / empty-pattern) EOL
product-token = identifier / "*"
path-pattern = "/" *UTF8-char-noctl
empty-pattern = *WS
identifier = 1*(%x2D / %x41-5A / %x5F / %x61-7A)
comment = "#" *(UTF8-char-noctl / WS / "#")
emptyline = EOL
EOL = *WS [comment] NL
NL = %x0D / %x0A / %x0D.0A
WS = %x20 / %x09
UTF8-char-noctl = UTF8-1-noctl / UTF8-2 / UTF8-3 / UTF8-4
UTF8-1-noctl = %x21 / %x22 / %x24-7F
UTF8-2 = %xC2-DF UTF8-tail
UTF8-3 = %xE0 %xA0-BF UTF8-tail / %xE1-EC 2UTF8-tail / %xED %x80-9F UTF8-tail / %xEE-EF 2UTF8-tail
UTF8-4 = %xF0 %x90-BF 2UTF8-tail / %xF1-F3 3UTF8-tail / %xF4 %x80-8F 2UTF8-tail
UTF8-tail = %x80-BF
"""


class RobotsRule(_Rule):
    """Private rule namespace so the grammar doesn't clash with anything else."""


def _load_grammar() -> None:
    """Register every rule definition from ROBOTS_ABNF on RobotsRule."""
    if RobotsRule.get("robotstxt") is not None:
        return  # already loaded
    for line in ROBOTS_ABNF.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        RobotsRule.create(line)


def validate(path: str | Path) -> tuple[bool, str]:
    """
    Check whether the file at `path` is syntactically valid robots.txt.

    Returns (is_valid, message). The message is human-readable and, on
    failure, points at the offset / line / column where parsing stopped.
    """
    _load_grammar()

    p = Path(path)
    try:
        # Read as latin-1 so each byte maps 1:1 to a Unicode code point;
        # the grammar uses byte-level numeric ranges (e.g. %xC2-DF) and we
        # want them matched against actual byte values, not UTF-8 chars.
        data = p.read_bytes().decode("latin-1")
    except OSError as e:
        return False, f"could not read {p}: {e}"

    try:
        RobotsRule("robotstxt").parse_all(data)
    except ParseError as e:
        # ParseError carries the offset it stopped at.
        offset = getattr(e, "start", None)
        if offset is None:
            return False, f"parse error: {e}"
        line = data.count("\n", 0, offset) + 1
        col = offset - (data.rfind("\n", 0, offset) + 1) + 1
        snippet = data[offset:offset + 40].replace("\r", "\\r").replace("\n", "\\n")
        return False, (
            f"parse error at byte {offset} (line {line}, col {col}); "
            f"next chars: {snippet!r}"
        )
    except GrammarError as e:
        return False, f"grammar error (bug in this script): {e}"

    return True, "valid"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "./robots.txt"
    ok, msg = validate(path)
    print(("VALID" if ok else "INVALID") + f": {msg}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""check-filenames.py - reject tracked files with hostile/malformed names.

Follows AUDIT-HY4-REPO §1.1: a tracked file named
`ystem and scroll reveal placeholder` (mangled shell quoting plus a
Private Use Area glyph, containing a captured `less` help screen) sat in the
repo undetected because nothing gates on filename shape. This script rejects
any tracked filename containing a quote/angle/pipe/star/question character or
a C0 control / Private Use Area codepoint.

Run: python3 scripts/check-filenames.py
Exit 0 clean, 1 on any offending tracked filename.
"""
import subprocess
import sys

BANNED_CHARS = set('"\'<>|*?')


def is_banned_codepoint(ch):
    cp = ord(ch)
    if cp < 0x20:  # C0 control
        return True
    if 0xE000 <= cp <= 0xF8FF:  # Private Use Area
        return True
    return False


def main():
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    offenders = []
    for name in out.splitlines():
        if not name:
            continue
        if any(ch in BANNED_CHARS for ch in name) or any(
            is_banned_codepoint(ch) for ch in name
        ):
            offenders.append(name)

    if offenders:
        print("::error::filename-hygiene gate found offending tracked file(s):")
        for f in offenders:
            print(f"  {f!r}")
        print(
            "\nTracked filenames must not contain quote/angle/pipe/star/question "
            "characters, or C0 control / Private Use Area glyphs."
        )
        return 1

    print(f"  filenames clean ({len(out.splitlines())} tracked files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

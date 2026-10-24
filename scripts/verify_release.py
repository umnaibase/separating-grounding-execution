#!/usr/bin/env python3
"""Check the public distribution's SHA-256 manifest using the standard library."""

from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest = root / "SHA256SUMS"
    failures: list[str] = []
    checked = 0
    seen: set[str] = set()
    try:
        records = manifest.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(records, 1):
            if not line:
                continue
            digest, separator, name = line.partition("  ")
            relative = PurePosixPath(name)
            if (
                not separator
                or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
                or not name
                or name in seen
                or relative.is_absolute()
                or ".." in relative.parts
                or "\\" in name
            ):
                raise ValueError(f"Invalid manifest entry on line {line_number}")
            seen.add(name)
            path = root.joinpath(*relative.parts)
            if path.is_symlink() or not path.is_file():
                failures.append(f"Missing or non-regular file: {name}")
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                failures.append(f"Checksum mismatch: {name}")
            checked += 1
        if checked == 0:
            raise ValueError("The manifest contains no files")
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Verified {checked} files against SHA256SUMS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

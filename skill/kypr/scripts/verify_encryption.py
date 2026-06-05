#!/usr/bin/env python3
"""Verify git-crypt is installed and configured for this repo.

Placeholder: implemented in WORK-0008. Exits non-zero (fail closed) so
the scaffold can never be mistaken for a passing encryption check.
"""

import sys


def main() -> int:
    print(
        "kypr verify_encryption.py is not implemented yet (WORK-0008); "
        "failing closed.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

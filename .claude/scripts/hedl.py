#!/usr/bin/env python3
"""Thin wrapper for consumer repos: delegates to install.py via __file__ resolution.

install.py and this file are siblings in skill/hedl/scripts/. When this file is
projected (symlinked) to .claude/scripts/hedl.py, Path(__file__).resolve() follows
the symlink back to the real scripts/ directory, making install.py discoverable
without the caller knowing the absolute path of the skill.
"""
import subprocess
import sys
from pathlib import Path

_install = Path(__file__).resolve().parent / "install.py"
sys.exit(subprocess.run([sys.executable, str(_install)] + sys.argv[1:]).returncode)

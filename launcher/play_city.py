"""Owner-facing one-command entry point:

    python -m launcher.play_city

Bare invocation runs the reversible Play City flow (``launcher.city_launch``).
Subcommands: ``plan`` (read-only), ``install`` (build/install only),
``doctor`` (read-only readiness), ``rollback --receipt <path>``.
"""
from __future__ import annotations

import sys

from .city_launch import main


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))

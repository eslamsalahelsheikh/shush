"""Allow running with `python -m shush`."""

import sys

from .app import run

sys.exit(run())

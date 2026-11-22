#!/usr/bin/env python3
"""Run the live coding engine CLI from the enhancement system."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from coding_master.cli import main


if __name__ == "__main__":
    sys.exit(main())

"""Allow ``python -m coding_master``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())

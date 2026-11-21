"""
LogLens command line interface entry point.
Allows running LogLens with `python -m loglens`.
"""

import sys
from loglens.cli import main

if __name__ == "__main__":
    sys.exit(main())

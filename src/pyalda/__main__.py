"""Allow running pyalda as a module: python -m pyalda"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

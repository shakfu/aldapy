"""Allow running aldakit as a module: python -m aldakit"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())

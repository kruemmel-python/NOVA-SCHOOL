from __future__ import annotations

import sys
import unittest
from pathlib import Path

from nova_bootstrap import bootstrap_package


def main() -> int:
    bootstrap_package()
    root = Path(__file__).resolve(strict=False).parent
    suite = unittest.defaultTestLoader.discover(str(root / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

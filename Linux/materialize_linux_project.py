from __future__ import annotations

import sys
from pathlib import Path


LINUX_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = LINUX_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nova_bootstrap import bootstrap_package

bootstrap_package()

from nova_school_server.distribution_builder import materialize_distribution_directory


def main() -> None:
    target_root = LINUX_ROOT / "project"
    result = materialize_distribution_directory(
        PROJECT_ROOT,
        target_root,
        flavor="linux-server-package",
    )
    print(result.target_root)


if __name__ == "__main__":
    main()

from __future__ import annotations

import sys
from pathlib import Path


LINUX_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = LINUX_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nova_bootstrap import bootstrap_package


def main() -> None:
    bootstrap_package()
    from nova_school_server.worker_agent import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()

from __future__ import annotations

import os
import sys
from pathlib import Path


LINUX_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = LINUX_ROOT.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nova_bootstrap import bootstrap_package


def main() -> None:
    bootstrap_package()
    os.environ.setdefault("NOVA_SCHOOL_BASE_PATH", str(LINUX_ROOT))
    from nova_school_server.config import ServerConfig
    from nova_school_server.server import create_application, run_server

    config = ServerConfig.from_base_path(LINUX_ROOT)
    application = create_application(config)
    run_server(application)


if __name__ == "__main__":
    main()

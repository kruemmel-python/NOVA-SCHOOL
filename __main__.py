from __future__ import annotations

import os
from pathlib import Path

from .config import ServerConfig
from .server import create_application, run_server


def main() -> None:
    override = str(os.environ.get("NOVA_SCHOOL_BASE_PATH") or "").strip()
    base_path = Path(override).expanduser().resolve(strict=False) if override else Path(__file__).resolve().parents[1]
    config = ServerConfig.from_base_path(base_path)
    application = create_application(config)
    run_server(application)


if __name__ == "__main__":
    main()

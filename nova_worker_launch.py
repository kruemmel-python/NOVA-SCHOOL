from __future__ import annotations

from nova_bootstrap import bootstrap_package


def main() -> None:
    bootstrap_package()
    from nova_school_server.worker_agent import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()

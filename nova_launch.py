from __future__ import annotations

from nova_bootstrap import bootstrap_package


def main() -> None:
    bootstrap_package()
    from nova_school_server.__main__ import main as package_main

    package_main()


if __name__ == "__main__":
    main()

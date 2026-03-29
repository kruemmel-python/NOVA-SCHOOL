from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_NAME = "nova_school_server"
PACKAGE_ROOT = Path(__file__).resolve(strict=False).parent


def bootstrap_package() -> None:
    if PACKAGE_NAME in sys.modules:
        return
    init_path = PACKAGE_ROOT / "__init__.py"
    if not init_path.exists():
        raise FileNotFoundError(f"Package bootstrap missing: {init_path}")
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME,
        init_path,
        submodule_search_locations=[str(PACKAGE_ROOT)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not create import spec for nova_school_server.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = module
    spec.loader.exec_module(module)

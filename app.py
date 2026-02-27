from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Callable


def _load_run() -> Callable[[], None]:
    try:
        from streamlit_app.app import run

        return run
    except Exception:
        module_name = "streamlit_app.app"
        module_path = Path(__file__).resolve().parent / "streamlit_app" / "app.py"

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load {module_name} from {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        run = getattr(module, "run", None)
        if run is None:
            raise ImportError("Loaded module has no 'run' function")

        return run


if __name__ == "__main__":
    _load_run()()

from __future__ import annotations

import compileall
import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    compile_src = compileall.compile_dir(str(ROOT / "src"), force=True, quiet=1)
    compile_run = compileall.compile_file(str(ROOT / "run.py"), force=True, quiet=1)

    modules = [
        "src.app",
        "src.routes.setup",
        "src.routes.firewall",
        "src.routes.system",
        "src.services.system",
        "src.services.firewall",
        "src.services.platform",
    ]
    for name in modules:
        importlib.import_module(name)

    print(
        {
            "compile_src": compile_src,
            "compile_run": compile_run,
            "imports": modules,
        }
    )
    return 0 if compile_src and compile_run else 1


if __name__ == "__main__":
    sys.exit(main())

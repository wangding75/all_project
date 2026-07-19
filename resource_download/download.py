#!/usr/bin/env python3
"""兼容入口：转发到 tools/cli_fanqie.py（逻辑已迁至 server/platforms/fanqie）。"""

from __future__ import annotations

import runpy
from pathlib import Path

if __name__ == "__main__":
    cli = Path(__file__).resolve().parent / "tools" / "cli_fanqie.py"
    runpy.run_path(str(cli), run_name="__main__")

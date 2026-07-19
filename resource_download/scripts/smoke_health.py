#!/usr/bin/env python3
"""冒烟：GET /health（无需鉴权）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import api_base, client, die, pretty  # noqa: E402


def main() -> None:
    print(f"API_BASE={api_base()}")
    with client() as c:
        r = c.get("/health")
        if r.status_code != 200:
            die(f"health failed: {r.status_code} {r.text}")
        print(pretty(r.json()))
    print("OK")


if __name__ == "__main__":
    main()

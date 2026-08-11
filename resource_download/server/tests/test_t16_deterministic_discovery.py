from __future__ import annotations

import asyncio
import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from t16_deterministic_discovery import (  # noqa: E402
    DETERMINISTIC_ITEM_ID,
    DeterministicHongguoPlatform,
)


def test_t16_deterministic_discovery_returns_one_candidate() -> None:
    async def _run():
        platform = DeterministicHongguoPlatform()
        rows = await platform.discover("new", limit=50)
        assert len(rows) == 1
        assert rows[0].id == DETERMINISTIC_ITEM_ID
        assert rows[0].platform.value == "hongguo"
        assert rows[0].extra["fixture"] == "deterministic"

    asyncio.run(_run())

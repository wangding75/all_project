"""Deterministic Hongguo discovery adapter for the T16 E2E process only.

This module is intentionally not imported by the production application.  The
T16 server launcher installs it in its own process so the real monitor,
LicenseGateway, quota checks, and JobManager path remain under test without a
live Hongguo runtime or public-network dependency.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models import DiscoverItem, PlatformName


DETERMINISTIC_ITEM_ID = "t16-deterministic-hongguo-candidate-001"


def deterministic_item() -> DiscoverItem:
    return DiscoverItem(
        id=DETERMINISTIC_ITEM_ID,
        title="T16 deterministic Hongguo candidate",
        desc="Local E2E fixture; not a production discovery result.",
        platform=PlatformName.hongguo,
        source_label="T16-E2E",
        badge="new",
        extra={
            "episode_count": 24,
            "category": "t16-e2e",
            "fixture": "deterministic",
        },
    )


class DeterministicHongguoPlatform:
    """Small platform surface used only by the T16 server subprocess."""

    name = PlatformName.hongguo.value

    async def discover(
        self,
        kind: str,
        *,
        limit: int = 50,
        **_kwargs: Any,
    ) -> list[DiscoverItem]:
        if kind != "new":
            return []
        return [deterministic_item()][: max(0, int(limit))]

    async def download(
        self,
        item_id: str,
        output_dir: Path,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        progress: Any = None,
    ) -> list[Path]:
        del range_spec, options
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"{item_id}.mp4"
        output.write_bytes(b"T16 deterministic E2E fixture")
        if progress:
            progress(100.0, "T16 deterministic fixture complete")
        return [output]

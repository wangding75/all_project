"""平台抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from app.models import DetailResponse, SearchItem

ProgressCallback = Callable[[float, str], None]


class BasePlatform(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        ...

    @abstractmethod
    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
        ...

    @abstractmethod
    async def download(
        self,
        item_id: str,
        output_dir: Path,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
        progress: ProgressCallback | None = None,
    ) -> list[Path]:
        """下载并导出到 output_dir，返回产物路径列表。"""
        ...

"""平台抽象接口。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from app.models import DetailResponse, DiscoverItem, SearchItem

ProgressCallback = Callable[[float, str], None]


class BasePlatform(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, page: int = 1, **kwargs: Any) -> list[SearchItem]:
        ...

    @abstractmethod
    async def get_detail(self, item_id: str, **kwargs: Any) -> DetailResponse:
        ...

    async def discover(
        self,
        kind: str,
        *,
        limit: int = 24,
        **kwargs: Any,
    ) -> list[DiscoverItem]:
        """返回平台真实发现内容；未支持的平台显式抛出，供聚合层降级。"""
        raise NotImplementedError(f"{self.name} 暂未提供 {kind} 发现数据")

    async def resolve_download(
        self,
        resource_id: str,
        *,
        title: str = "",
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Resolve platform-private media into stable server-side descriptors.

        Implementations must not write to ``output_dir`` here.  The legacy
        ``download`` method remains available until the migration reaches the
        removal phase.
        """
        raise NotImplementedError(f"{self.name} 暂未提供 Download Resolve")

    async def stream_download(
        self,
        resource_id: str,
        *,
        range_spec: str = "all",
        options: dict[str, Any] | None = None,
    ):
        """Yield proxy bytes without materializing a server-side file."""
        raise NotImplementedError(f"{self.name} 暂未提供 Streaming Proxy")

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

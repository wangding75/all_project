"""平台注册表。"""

from __future__ import annotations

from app.models import PlatformName
from platforms.base import BasePlatform


def get_platform(name: PlatformName | str) -> BasePlatform:
    key = name.value if isinstance(name, PlatformName) else str(name)
    if key == PlatformName.hongguo.value:
        from platforms.hongguo.platform import HongguoPlatform

        return HongguoPlatform()
    if key == PlatformName.fanqie.value:
        # 产品方向已改为 App 会话；现有 Web 实现仅作遗留，默认仍可 import
        from platforms.fanqie.platform import FanqiePlatform

        return FanqiePlatform()
    raise KeyError(f"unknown platform: {key}")


def list_platforms() -> list[str]:
    # 当前主攻红果；番茄注册保留但非主路径
    return [PlatformName.hongguo.value, PlatformName.fanqie.value]

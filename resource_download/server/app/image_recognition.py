"""Cover/poster recognition using perceptual image similarity."""

from __future__ import annotations

import asyncio
import base64
import binascii
import math
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.media_cache import materialize_cover, register_cover_url
from app.models import (
    DiscoverItem,
    ImageRecognizeCandidate,
    ImageRecognizeResponse,
    PlatformName,
)
from platforms.registry import get_platform

_MAX_IMAGE_BYTES = 8 * 1024 * 1024
_MAX_IMAGE_PIXELS = 24_000_000


def decode_image_base64(value: str) -> bytes:
    payload = str(value or "").strip()
    if payload.startswith("data:"):
        header, separator, payload = payload.partition(",")
        if not separator or ";base64" not in header.lower():
            raise ValueError("图片 data URL 必须使用 base64 编码")
    try:
        data = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("图片 base64 格式无效") from exc
    if not data:
        raise ValueError("图片内容为空")
    if len(data) > _MAX_IMAGE_BYTES:
        raise ValueError("图片不能超过 8 MB")
    return data


def _fingerprint(source: bytes | Any) -> tuple[int, tuple[float, float, float], float]:
    try:
        with Image.open(BytesIO(source) if isinstance(source, bytes) else source) as image:
            width, height = image.size
            if width <= 0 or height <= 0 or width * height > _MAX_IMAGE_PIXELS:
                raise ValueError("图片尺寸无效或像素数超过限制")
            rgb = image.convert("RGB")
            grayscale = rgb.resize((9, 8), Image.Resampling.LANCZOS).convert("L")
            pixels = list(grayscale.get_flattened_data())
            difference_hash = 0
            bit = 0
            for row in range(8):
                offset = row * 9
                for column in range(8):
                    if pixels[offset + column] > pixels[offset + column + 1]:
                        difference_hash |= 1 << bit
                    bit += 1
            color = rgb.resize((1, 1), Image.Resampling.BOX).getpixel((0, 0))
            aspect_ratio = width / height
            return difference_hash, tuple(float(value) for value in color), aspect_ratio
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("无法解析图片，请使用 JPEG、PNG 或 WEBP") from exc


def _similarity(
    source: tuple[int, tuple[float, float, float], float],
    target: tuple[int, tuple[float, float, float], float],
) -> float:
    hash_similarity = 1.0 - ((source[0] ^ target[0]).bit_count() / 64.0)
    color_distance = math.sqrt(
        sum((left - right) ** 2 for left, right in zip(source[1], target[1], strict=True))
    )
    color_similarity = max(0.0, 1.0 - color_distance / math.sqrt(3 * 255**2))
    aspect_similarity = max(
        0.0,
        1.0 - abs(math.log(max(source[2], 0.01) / max(target[2], 0.01))) / 2.5,
    )
    return max(0.0, min(1.0, 0.72 * hash_similarity + 0.18 * color_similarity + 0.10 * aspect_similarity))


def _confidence(score: float) -> str:
    if score >= 0.88:
        return "high"
    if score >= 0.72:
        return "medium"
    return "low"


async def recognize_cover(
    image_data: bytes,
    *,
    platform_hint: str = "all",
    max_candidates: int = 5,
) -> ImageRecognizeResponse:
    source_fingerprint = await asyncio.to_thread(_fingerprint, image_data)
    targets = (
        [PlatformName.hongguo, PlatformName.fanqie]
        if platform_hint == "all"
        else [PlatformName(platform_hint)]
    )

    async def _discover(platform_name: PlatformName):
        try:
            platform = get_platform(platform_name)
            hot, new = await asyncio.gather(
                platform.discover("hot", limit=24),
                platform.discover("new", limit=24),
            )
            return platform_name, [*(hot or []), *(new or [])], None
        except Exception as exc:  # noqa: BLE001
            return platform_name, [], str(exc)

    discovered = await asyncio.gather(*[_discover(platform) for platform in targets])
    errors: dict[str, str] = {}
    unique: dict[tuple[str, str], DiscoverItem] = {}
    for platform_name, items, error in discovered:
        if error:
            errors[platform_name.value] = error
            continue
        for item in items:
            unique.setdefault((item.platform.value, str(item.id)), item)

    semaphore = asyncio.Semaphore(6)

    async def _compare(item: DiscoverItem):
        proxy_url = register_cover_url(item.cover)
        if not proxy_url:
            return None
        cover_id = proxy_url.rsplit("/", 1)[-1].removesuffix(".jpg")
        async with semaphore:
            try:
                path = await asyncio.to_thread(materialize_cover, cover_id)
                if path is None:
                    return None
                fingerprint = await asyncio.to_thread(_fingerprint, path)
                score = _similarity(source_fingerprint, fingerprint)
                item.cover = proxy_url
                return ImageRecognizeCandidate(
                    score=round(score, 4),
                    confidence=_confidence(score),
                    content=item,
                )
            except Exception:
                return None

    compared = await asyncio.gather(*[_compare(item) for item in unique.values()])
    candidates = sorted(
        (candidate for candidate in compared if candidate is not None),
        key=lambda candidate: candidate.score,
        reverse=True,
    )
    return ImageRecognizeResponse(
        candidates=candidates[: max(1, min(max_candidates, 10))],
        compared_count=len(candidates),
        platform_errors=errors,
    )

"""Validation and lifetime handling for job options.

Job options arrive from an untrusted HTTP client.  Keep the accepted surface
small and split credentials from the persisted job record.  A job may still
use a per-request cookie/token while it is running, but those values live only
in memory and are deliberately omitted from ``jobs/*.json``.
"""

from __future__ import annotations

import re
from typing import Any

from app.models import PlatformName


_SENSITIVE_KEY = re.compile(
    r"(?:cookie|token|authorization|password|passwd|secret|private[_-]?key|"
    r"credential|proxy|access[_-]?key|api[_-]?key)",
    re.IGNORECASE,
)

_COMMON = {
    "title",
    "source",
    "original_input",
    "download_cover",
    "download_desc",
    "naming",
}
_PLATFORM_OPTIONS = {
    PlatformName.fanqie: _COMMON | {"delay", "mode", "cookie"},
    PlatformName.hongguo: _COMMON | {"concurrency", "retry", "quality", "allow_raw"},
}


def _validate_naming(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or len(value) > 16:
        raise ValueError("naming must be a small object")
    result: dict[str, Any] = {}
    for key, item in value.items():
        if not isinstance(key, str) or len(key) > 64:
            raise ValueError("naming keys are too long")
        if isinstance(item, str):
            if len(item) > 128:
                raise ValueError("naming values are too long")
            result[key] = item
        elif isinstance(item, (int, float, bool)) or item is None:
            result[key] = item
        else:
            raise ValueError("naming values must be scalar")
    return result


def _validate_scalar(key: str, value: Any) -> Any:
    if key in {"title", "source", "original_input"}:
        if not isinstance(value, str) or len(value) > 512:
            raise ValueError(f"{key} must be a short string")
        return value
    if key in {"download_cover", "download_desc", "allow_raw"}:
        if not isinstance(value, bool):
            raise ValueError(f"{key} must be boolean")
        return value
    if key == "delay":
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("delay must be a number") from exc
        if not 0 <= number <= 60:
            raise ValueError("delay must be between 0 and 60 seconds")
        return number
    if key == "concurrency":
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("concurrency must be an integer") from exc
        if not 1 <= number <= 12:
            raise ValueError("concurrency must be between 1 and 12")
        return number
    if key == "retry":
        try:
            number = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("retry must be an integer") from exc
        if not 0 <= number <= 10:
            raise ValueError("retry must be between 0 and 10")
        return number
    if key == "quality":
        quality = str(value).strip().lower()
        if quality not in {"best", "1080p", "720p", "480p", "360p"}:
            raise ValueError("quality is unsupported")
        return quality
    if key == "mode":
        mode = str(value).strip().lower()
        if mode not in {"web", "app"}:
            raise ValueError("mode must be web or app")
        return mode
    if key == "naming":
        return _validate_naming(value)
    raise ValueError(f"unsupported job option: {key}")


def split_job_options(
    platform: PlatformName | str,
    options: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(persisted, runtime_only)`` validated options.

    Unknown options are rejected rather than passed through to vendor code.
    This prevents an accidental unbounded option tree from becoming a resource
    or command injection surface.
    """

    if options is None:
        return {}, {}
    if not isinstance(options, dict) or len(options) > 32:
        raise ValueError("options must be an object with at most 32 fields")
    try:
        platform_name = PlatformName(platform)
    except ValueError as exc:
        raise ValueError("unsupported platform") from exc
    allowed = _PLATFORM_OPTIONS[platform_name]
    unknown = sorted(set(options) - allowed)
    if unknown:
        raise ValueError(f"unsupported job option(s): {', '.join(unknown[:8])}")

    persisted: dict[str, Any] = {}
    runtime: dict[str, Any] = {}
    for key, value in options.items():
        normalized = _validate_scalar(key, value)
        if _SENSITIVE_KEY.search(key):
            runtime[key] = normalized
        else:
            persisted[key] = normalized
    return persisted, runtime


def sanitize_persisted_options(options: Any) -> dict[str, Any]:
    """Defence-in-depth scrub for legacy records loaded from disk."""

    if not isinstance(options, dict):
        return {}
    result: dict[str, Any] = {}
    for key, value in options.items():
        if not isinstance(key, str) or _SENSITIVE_KEY.search(key):
            continue
        if isinstance(value, dict):
            nested = sanitize_persisted_options(value)
            result[key] = nested
        elif isinstance(value, list):
            result[key] = [item for item in value[:100] if not isinstance(item, (dict, list))]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            result[key] = value
    return result


def validate_range_spec(value: Any) -> str:
    """Validate the compact chapter/episode range before vendor code sees it."""
    if not isinstance(value, str):
        raise ValueError("range must be a string")
    raw = value.strip().lower() or "all"
    if len(raw) > 256:
        raise ValueError("range is too long")
    if raw in {"all", "*"}:
        return "all"
    selected = 0
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            if "-" in token:
                left, right = token.split("-", 1)
                start, end = int(left), int(right)
                if start > end:
                    start, end = end, start
                width = end - start + 1
            else:
                start = end = int(token)
                width = 1
        except (TypeError, ValueError) as exc:
            raise ValueError("range must contain positive integers") from exc
        if start < 1 or end > 1_000_000 or width > 100_000:
            raise ValueError("range exceeds the supported bounds")
        selected += width
        if selected > 100_000:
            raise ValueError("range selects too many items")
    if selected == 0:
        raise ValueError("range must not be empty")
    return raw

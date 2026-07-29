"""Download one real Hongguo episode in every advertised quality.

This is an integration test. It requires MuMu, the Hongguo App, a root Frida
agent, and a valid data/config/hongguo_config.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))

from platforms.hongguo.bridge import (  # noqa: E402
    call_with_session_recovery,
    load_hongguo_api,
    load_offline_dl,
)
from platforms.hongguo.platform import HongguoPlatform  # noqa: E402


QUALITIES = ("360p", "480p", "540p", "720p", "1080p")


def _ffmpeg() -> str | None:
    configured = os.environ.get("FFMPEG_BINARY")
    if configured:
        return configured
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _is_playable(path: Path) -> tuple[bool, str]:
    ffmpeg = _ffmpeg()
    if not ffmpeg:
        return False, "ffmpeg unavailable"
    result = subprocess.run(
        [ffmpeg, "-v", "error", "-t", "3", "-i", str(path), "-f", "null", "-"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    message = (result.stderr or "").strip().replace("\r", " ").replace("\n", " ")
    return result.returncode == 0, message[:300]


def _quality_metadata(series_id: str) -> tuple[str, dict[str, dict]]:
    def load():
        api = load_hongguo_api()
        _meta, episodes = api.get_episodes(series_id)
        first = episodes[0]
        video_id = str(first.get("vid") or first.get("video_id") or first.get("id"))
        tracks = api.get_video_tracks([video_id]).get(video_id) or []
        offline = load_offline_dl()
        rows = offline.list_quals({"video_list": tracks})
        return video_id, {
            str(definition): {
                "advertised_bytes": int(size or 0),
                "resolution": resolution,
                "codec": codec,
                "encrypted": bool(encrypted),
            }
            for definition, size, resolution, codec, encrypted in rows
        }

    return call_with_session_recovery(load)


async def run(series_id: str, output_root: Path) -> list[dict]:
    video_id, metadata = await asyncio.to_thread(_quality_metadata, series_id)
    platform = HongguoPlatform()
    results: list[dict] = []
    for quality in QUALITIES:
        output_dir = output_root / quality
        output_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "quality": quality,
            "series_id": series_id,
            "video_id": video_id,
            **metadata.get(quality, {}),
        }
        try:
            files = await platform.download(
                series_id,
                output_dir,
                range_spec="1",
                options={
                    "quality": quality,
                    "concurrency": 1,
                    "retry": 1,
                    "allow_raw": True,
                },
            )
            candidates = [path for path in files if path.is_file() and path.stat().st_size > 0]
            output = max(candidates, key=lambda path: path.stat().st_size)
            playable, error = _is_playable(output)
            row.update(
                {
                    "download_ok": True,
                    "output": str(output.resolve()),
                    "output_bytes": output.stat().st_size,
                    "container": "raw-decrypted" if output.name.endswith(".raw.mp4") else "mp4",
                    "playable": playable,
                    "playback_error": error or None,
                }
            )
        except Exception as exc:  # noqa: BLE001 - matrix must continue after one quality fails
            row.update(
                {
                    "download_ok": False,
                    "playable": False,
                    "error": str(exc),
                }
            )
        results.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--series-id",
        default="7660841866979445784",
        help="Hongguo series ID used for the one-episode matrix",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "tmp" / "hongguo-quality-matrix",
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = asyncio.run(run(args.series_id, args.output))
    result_path = args.output / "results.json"
    result_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"results={result_path.resolve()}")
    return 0 if all(row.get("download_ok") for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

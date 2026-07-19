"""Gunzip all pulled fq_crypt *_out.bin to HTML."""
from __future__ import annotations

import gzip
from pathlib import Path

DIR = Path(__file__).resolve().parents[2] / "tmp" / "fanqie_probe" / "crypt_dump" / "device"


def main() -> int:
    ok = 0
    for p in sorted(DIR.glob("*_out.bin")):
        raw = p.read_bytes()
        if raw[:2] != b"\x1f\x8b":
            print("skip not gzip", p.name)
            continue
        text = gzip.decompress(raw).decode("utf-8", "replace")
        out = p.with_name(p.name.replace("_out.bin", "_out.html"))
        out.write_text(text, encoding="utf-8")
        print(f"OK {p.name} -> {out.name} ({len(text)} chars)")
        ok += 1
    print(f"done {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

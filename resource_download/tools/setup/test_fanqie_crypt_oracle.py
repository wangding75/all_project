"""Regression: dump samples + live Frida RPC CryptManager.decrypt."""
from __future__ import annotations

import gzip
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))

DUMP = ROOT / "tmp" / "fanqie_probe" / "crypt_dump" / "device"
OUT = ROOT / "tmp" / "fanqie_probe" / "oracle_reg"
OUT.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
os.environ.setdefault("ADB_DEVICE", "127.0.0.1:16384")
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")
os.environ.setdefault("AGENT_BIN", "/data/local/tmp/sys_hlpd")


def load_sample(mid: str = "0001") -> tuple[str, str, int, bytes]:
    meta = json.loads((DUMP / f"{mid}_meta.json").read_text(encoding="utf-8"))
    cipher = (DUMP / f"{mid}_arg0.txt").read_text(encoding="utf-8").strip()
    key = None
    ver = 1001
    for a in meta.get("args") or []:
        if a.get("i") == 1:
            key = a.get("value")
        if a.get("i") == 2:
            ver = int(a.get("value") or 1001)
    expected = (DUMP / f"{mid}_out.bin").read_bytes()
    if not key:
        raise SystemExit("no key in meta")
    return cipher, key, ver, expected


def test_local_gunzip() -> None:
    print("=== local gunzip dumps ===")
    n = 0
    for p in sorted(DUMP.glob("*_out.bin"))[:10]:
        raw = p.read_bytes()
        assert raw[:2] == b"\x1f\x8b", p
        text = gzip.decompress(raw).decode("utf-8")
        assert "chapterTitle" in text or "article" in text, p
        n += 1
    print(f"OK gunzip {n} samples")


def test_oracle() -> int:
    print("=== live oracle ===")
    from platforms.fanqie.crypt_oracle import FanqieCryptOracle  # noqa: WPS433

    cipher, key, ver, expected = load_sample("0001")
    print(f"sample cipher_len={len(cipher)} key_len={len(key)} ver={ver} expected={len(expected)}")
    o = FanqieCryptOracle()
    try:
        o.attach()
        print("maxKeyVersion", o.max_key_version())
        r = o.decrypt_raw(cipher, key, ver)
        print("result", r.as_dict())
        if not r.ok or not r.out_bytes:
            print("FAIL decrypt", r.error)
            return 1
        if r.out_bytes != expected:
            print(
                f"WARN bytes mismatch len {len(r.out_bytes)} vs {len(expected)} "
                f"head {r.out_bytes[:8].hex()} vs {expected[:8].hex()}"
            )
            # still OK if gunzip text matches expected gunzip
            exp_text = gzip.decompress(expected).decode("utf-8", "replace")
            if r.text and r.text == exp_text:
                print("OK text matches expected gunzip")
            elif r.text:
                print("text head", r.text[:200])
                (OUT / "oracle_0001.html").write_text(r.text, encoding="utf-8")
            else:
                return 1
        else:
            print("OK exact out.bin match")
            if r.text:
                (OUT / "oracle_0001.html").write_text(r.text, encoding="utf-8")
                print("text head", r.text[:200].replace("\n", " "))
        return 0
    finally:
        o.close()


def main() -> int:
    if not DUMP.is_dir() or not list(DUMP.glob("*_meta.json")):
        print("no dumps at", DUMP)
        return 1
    test_local_gunzip()
    return test_oracle()


if __name__ == "__main__":
    raise SystemExit(main())

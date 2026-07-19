"""Parse CryptManager.decrypt hits and gunzip return bytes."""
from __future__ import annotations

import gzip
import json
import re
import zlib
from collections import Counter
from pathlib import Path

HITS = Path(__file__).resolve().parents[2] / "tmp" / "fanqie_probe" / "hook_hits"
# latest hits file with decrypt
files = sorted(HITS.glob("hits_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
if not files:
    raise SystemExit("no hits")
p = files[0]
print("file", p)

c: Counter[str] = Counter()
decrypt_samples = []
for line in p.open(encoding="utf-8"):
    o = json.loads(line)
    if o.get("t") != "hit":
        continue
    tag = o.get("tag") or ""
    c[tag] += 1
    if "CryptManager.decrypt" in tag and len(decrypt_samples) < 5:
        decrypt_samples.append(o)

print("top tags:", c.most_common(12))
print("decrypt count:", c.get("com.dragon.read.crypt.CryptManager.decrypt", 0))

plain_out = HITS / "decrypt_gunzip_sample.txt"
parts = []

for i, o in enumerate(decrypt_samples):
    ret = (o.get("p") or {}).get("ret") or ""
    args = (o.get("p") or {}).get("args") or []
    key = args[1][:48] if len(args) > 1 else "?"
    ver = args[2] if len(args) > 2 else "?"
    cipher_head = (args[0][:40] + "...") if args and isinstance(args[0], str) else "?"
    print(f"\n=== sample {i} key={key}... ver={ver} cipher={cipher_head} ===")
    body = re.sub(r"\.\.\.\(\d+\)$", "", ret)
    nums = []
    for part in body.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            nums.append(int(part))
        except ValueError:
            break
    raw = bytes((n + 256) % 256 for n in nums)
    print("raw head", raw[:8].hex(), "parsed_len", len(raw))
    if raw[:2] != b"\x1f\x8b":
        print("not gzip")
        continue
    text = None
    try:
        text = gzip.decompress(raw).decode("utf-8", "replace")
        print("gzip full OK len", len(text))
    except Exception as e:
        print("gzip full fail:", type(e).__name__, e)
        try:
            text = zlib.decompress(raw, 16 + zlib.MAX_WBITS).decode("utf-8", "replace")
            print("zlib OK len", len(text))
        except Exception as e2:
            print("zlib fail:", e2)
            # truncated log: try inflate object
            try:
                d = zlib.decompressobj(16 + zlib.MAX_WBITS)
                partial = d.decompress(raw)
                text = partial.decode("utf-8", "replace")
                print("partial inflate len", len(text))
            except Exception as e3:
                print("partial fail", e3)
    if text:
        print(text[:400].replace("\n", "\\n"))
        parts.append(f"===== sample {i} ver={ver} =====\n{text}\n")

if parts:
    plain_out.write_text("\n".join(parts), encoding="utf-8")
    print("\nwrote", plain_out)
else:
    print("\nno plaintext recovered (ret may be truncated in jsonl)")

# also show plain_*.txt if any
for pf in sorted(HITS.glob("plain_*.txt"), key=lambda x: x.stat().st_mtime, reverse=True)[:2]:
    print("\n---", pf.name, "---")
    print(pf.read_text(encoding="utf-8", errors="replace")[:600])

"""Web SSR vs App reader/full 对比验证：5 书 × 前 10 章。

Web: platforms.fanqie.web_ssr（无 Cookie 试跑）
App: hongguo 签名拉 directory + reader/full，再 CryptManager 预言机解密

用法:
  python compare_web_vs_app.py
  python compare_web_vs_app.py --web-only
  python compare_web_vs_app.py --app-only
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
os.environ.setdefault("ADB_DEVICE", "127.0.0.1:16384")
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")
os.environ.setdefault("AGENT_BIN", "/data/local/tmp/sys_hlpd")

from platforms.fanqie import web_ssr  # noqa: E402
from platforms.fanqie import client as H  # noqa: E402
from platforms.fanqie.app_content import html_to_text, resolve_key, resolve_version  # noqa: E402
from platforms.fanqie.crypt_oracle import FanqieCryptOracle  # noqa: E402

BOOKS = [
    {"name": "十日终焉", "book_id": "7143038691944959011"},
    {"name": "这个游戏不对劲，我挖矿成神！", "book_id": "7590221243043826712"},
    {"name": "我在精神病院学斩神", "book_id": "6982529841564224526"},
    {"name": "时停起手，邪神也得给我跪下！", "book_id": "7504849932138859545"},
    {"name": "天眼风水师", "book_id": "7326876174989134910"},
]
N_CH = 10

OUT = ROOT / "tmp" / "fanqie_probe" / f"compare_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
OUT.mkdir(parents=True, exist_ok=True)


def norm_text(s: str) -> str:
    s = s or ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\s+", "", s)
    # 去掉常见 HTML 实体残留
    s = s.replace("\u3000", "")
    return s


def sim_ratio(a: str, b: str) -> float:
    """简单重合：取较短长度前缀的字符级 Jaccard-ish。"""
    a, b = norm_text(a), norm_text(b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    # 用滑动窗口最长公共子串太慢；用 hash 块
    n = min(len(a), len(b), 4000)
    a, b = a[:n], b[:n]
    same = sum(1 for x, y in zip(a, b) if x == y)
    return same / n


def sha(s: str) -> str:
    return hashlib.sha256(norm_text(s).encode("utf-8", "replace")).hexdigest()[:16]


def run_web(book: dict) -> dict:
    book_id = book["book_id"]
    name = book["name"]
    book_dir = OUT / "web" / book_id
    book_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "book_id": book_id,
        "name": name,
        "ok": False,
        "title": "",
        "chapters": [],
        "error": None,
    }
    try:
        web_ssr.set_cookie(os.environ.get("FANQIE_COOKIE"))
        book_name, chapters, font_mapping = web_ssr.get_chapter_list(book_id)
        result["title"] = book_name
        (book_dir / "meta.json").write_text(
            json.dumps(
                {
                    "book_name": book_name,
                    "chapter_count": len(chapters),
                    "font_keys": len(font_mapping or {}),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        sample = chapters[:N_CH]
        for i, ch in enumerate(sample, start=1):
            item_id = str(ch.get("item_id") or ch.get("group_id") or "")
            title = str(ch.get("title") or f"ch{i}")
            locked = bool(ch.get("is_locked"))
            rec = {
                "index": i,
                "item_id": item_id,
                "title": title,
                "locked": locked,
                "ok": False,
                "text": "",
                "error": None,
                "chars": 0,
            }
            if locked or not item_id:
                rec["error"] = "locked_or_no_id"
                result["chapters"].append(rec)
                continue
            try:
                t, content = web_ssr.download_chapter(item_id, font_mapping)
                rec["title"] = t or title
                rec["text"] = content or ""
                rec["chars"] = len(norm_text(rec["text"]))
                rec["ok"] = rec["chars"] > 50
                (book_dir / f"{i:02d}_{item_id}.txt").write_text(
                    f"# {rec['title']}\n\n{rec['text']}", encoding="utf-8"
                )
                time.sleep(0.4)
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {e}"
            result["chapters"].append(rec)
            print(
                f"  [web] {name[:12]} #{i} ok={rec['ok']} chars={rec['chars']} "
                f"err={rec['error']}",
                flush=True,
            )
        result["ok"] = any(c["ok"] for c in result["chapters"])
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        print(f"  [web] BOOK FAIL {name}: {e}", flush=True)
    return result


def fetch_directory(book_id: str) -> tuple[list[str], dict]:
    return H.get_directory(book_id)


def fetch_full(book_id: str, item_id: str) -> dict:
    return H.fetch_full(book_id, item_id)


def run_app(
    book: dict,
    oracle: FanqieCryptOracle | None,
    preferred_ids: list[str] | None = None,
) -> dict:
    """preferred_ids: 优先用 Web 侧已解析的 item_id，避免再打 directory。"""
    book_id = book["book_id"]
    name = book["name"]
    book_dir = OUT / "app" / book_id
    book_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "book_id": book_id,
        "name": name,
        "ok": False,
        "chapters": [],
        "error": None,
    }
    try:
        if preferred_ids:
            sample_ids = [x for x in preferred_ids if x][:N_CH]
            print(f"  [app] use web item_ids n={len(sample_ids)}", flush=True)
        else:
            item_ids, raw_dir = fetch_directory(book_id)
            (book_dir / "directory.json").write_text(
                json.dumps(raw_dir, ensure_ascii=False)[:500000],
                encoding="utf-8",
            )
            sample_ids = item_ids[:N_CH]
        if not sample_ids:
            result["error"] = "no_item_ids"
            print(f"  [app] {name} no item_ids", flush=True)
            return result
        key = resolve_key()
        ver = resolve_version()
        for i, item_id in enumerate(sample_ids, start=1):
            rec = {
                "index": i,
                "item_id": item_id,
                "ok": False,
                "title": "",
                "text": "",
                "chars": 0,
                "crypt_status": None,
                "compress_status": None,
                "key_version_api": None,
                "error": None,
            }
            try:
                j = fetch_full(book_id, item_id)
                data = j.get("data") or {}
                if not isinstance(data, dict):
                    rec["error"] = f"bad_data code={j.get('code')}"
                    result["chapters"].append(rec)
                    continue
                content = data.get("content") or ""
                rec["title"] = str(data.get("title") or "")
                rec["crypt_status"] = data.get("crypt_status")
                rec["compress_status"] = data.get("compress_status")
                rec["key_version_api"] = data.get("key_version")
                (book_dir / f"{i:02d}_{item_id}_full.json").write_text(
                    json.dumps(
                        {
                            "code": j.get("code"),
                            "title": rec["title"],
                            "crypt_status": rec["crypt_status"],
                            "compress_status": rec["compress_status"],
                            "key_version": rec["key_version_api"],
                            "content_len": len(content),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                (book_dir / f"{i:02d}_{item_id}_content.b64").write_text(
                    content, encoding="utf-8"
                )
                if not content:
                    rec["error"] = (
                        f"empty_content code={j.get('code')} msg={j.get('message')}"
                    )
                elif oracle is None:
                    rec["error"] = "no_oracle"
                else:
                    r = oracle.decrypt_raw(content, key, ver)
                    if (not r.ok or not r.text) and rec["key_version_api"]:
                        try:
                            alt = int(rec["key_version_api"])
                            if alt != ver:
                                r = oracle.decrypt_raw(content, key, alt)
                        except Exception:
                            pass
                    if not r.ok or not r.text:
                        rec["error"] = r.error or "decrypt_fail"
                    else:
                        plain = html_to_text(r.text)
                        rec["text"] = plain
                        rec["chars"] = len(norm_text(plain))
                        rec["ok"] = rec["chars"] > 50
                        (book_dir / f"{i:02d}_{item_id}.html").write_text(
                            r.text, encoding="utf-8"
                        )
                        (book_dir / f"{i:02d}_{item_id}.txt").write_text(
                            f"# {rec['title']}\n\n{plain}", encoding="utf-8"
                        )
                time.sleep(0.35)
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {e}"
            result["chapters"].append(rec)
            print(
                f"  [app] {name[:12]} #{i} ok={rec['ok']} chars={rec['chars']} "
                f"err={rec['error']}",
                flush=True,
            )
        result["ok"] = any(c["ok"] for c in result["chapters"])
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
        print(f"  [app] BOOK FAIL {name}: {e}", flush=True)
    return result


def compare_book(web: dict, app: dict) -> dict:
    rows = []
    web_chs = {c["index"]: c for c in web.get("chapters") or []}
    app_chs = {c["index"]: c for c in app.get("chapters") or []}
    for i in range(1, N_CH + 1):
        w, a = web_chs.get(i, {}), app_chs.get(i, {})
        wt, at = w.get("text") or "", a.get("text") or ""
        ratio = sim_ratio(wt, at) if (wt and at) else 0.0
        # 标题粗比
        title_sim = sim_ratio(w.get("title") or "", a.get("title") or "")
        rows.append(
            {
                "index": i,
                "web_ok": bool(w.get("ok")),
                "app_ok": bool(a.get("ok")),
                "web_chars": w.get("chars") or 0,
                "app_chars": a.get("chars") or 0,
                "web_title": w.get("title"),
                "app_title": a.get("title"),
                "web_item": w.get("item_id"),
                "app_item": a.get("item_id"),
                "item_match": (w.get("item_id") and w.get("item_id") == a.get("item_id")),
                "text_sim": round(ratio, 4),
                "title_sim": round(title_sim, 4),
                "web_err": w.get("error"),
                "app_err": a.get("error"),
                "same_sha": bool(wt and at and sha(wt) == sha(at)),
            }
        )
    ok_both = [r for r in rows if r["web_ok"] and r["app_ok"]]
    avg_sim = (
        sum(r["text_sim"] for r in ok_both) / len(ok_both) if ok_both else None
    )
    return {
        "book_id": web.get("book_id") or app.get("book_id"),
        "name": web.get("name") or app.get("name"),
        "web_book_ok": web.get("ok"),
        "app_book_ok": app.get("ok"),
        "web_error": web.get("error"),
        "app_error": app.get("error"),
        "chapters_compared": rows,
        "both_ok_count": len(ok_both),
        "avg_text_sim_when_both_ok": avg_sim,
    }


def ensure_dragon_for_oracle() -> FanqieCryptOracle | None:
    """解密挂番茄；不杀红果、不杀签名 agent（共用 27042，分 pid attach）。"""
    adb = os.environ["ADB"]
    dev = os.environ["ADB_DEVICE"]
    subprocess.run([adb, "connect", dev], capture_output=True)
    pid = subprocess.run(
        [adb, "-s", dev, "shell", "pidof", "com.dragon.read"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not pid:
        print("[app] launching 番茄 for decrypt...", flush=True)
        subprocess.run(
            [
                adb,
                "-s",
                dev,
                "shell",
                "am",
                "start",
                "-n",
                "com.dragon.read/.pages.splash.SplashActivity",
            ],
            capture_output=True,
        )
        time.sleep(12)
        pid = subprocess.run(
            [adb, "-s", dev, "shell", "pidof", "com.dragon.read"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    if not pid:
        print("[app] 番茄未运行，解密关闭", flush=True)
        return None
    print(f"[app] 番茄 pid={pid}", flush=True)
    # 保证 27042 上有 agent（签名用的那个即可，不必改名杀进程）
    agent = subprocess.run(
        [adb, "-s", dev, "shell", "pidof", "frida-server"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not agent:
        subprocess.Popen(
            [adb, "-s", dev, "shell", "/data/local/tmp/frida-server", "-D"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)
    subprocess.run([adb, "-s", dev, "forward", "tcp:27042", "tcp:27042"], capture_output=True)
    try:
        # 解密 attach 不走 crypt_oracle.ensure_agent 的 pkill，直接 attach
        import frida  # type: ignore

        from platforms.fanqie import crypt_oracle as co

        o = co.FanqieCryptOracle()
        js = o.js_path.read_text(encoding="utf-8")
        device = frida.get_device_manager().add_remote_device(os.environ.get("FRIDA_HOST", "127.0.0.1:27042"))
        session = device.attach(int(pid.split()[0]))
        script = session.create_script(js)
        script.load()
        o._session = session
        o._script = script
        o._app_pid = pid.split()[0]
        print("[app] decrypt oracle attached (no kill sign-agent)", flush=True)
        return o
    except Exception as e:
        print(f"[app] decrypt attach fail: {e}", flush=True)
        return None


def load_web_from_dir(web_dir: Path) -> dict[str, dict]:
    """从已有 compare_*/web_results.json 或 web/<id>/*.txt 恢复 web 结果。"""
    wr_path = web_dir / "web_results.json"
    if wr_path.is_file():
        return json.loads(wr_path.read_text(encoding="utf-8"))
    # 从 txt 重建
    web_root = web_dir / "web"
    out: dict[str, dict] = {}
    if not web_root.is_dir():
        # 允许直接传 compare 根目录
        if (web_dir / "web").is_dir():
            web_root = web_dir / "web"
        else:
            return out
    name_by_id = {b["book_id"]: b["name"] for b in BOOKS}
    for d in sorted(web_root.iterdir()):
        if not d.is_dir():
            continue
        bid = d.name
        chs = []
        for i in range(1, N_CH + 1):
            files = list(d.glob(f"{i:02d}_*.txt"))
            rec = {
                "index": i,
                "item_id": "",
                "title": "",
                "locked": False,
                "ok": False,
                "text": "",
                "error": None,
                "chars": 0,
            }
            if files:
                raw = files[0].read_text(encoding="utf-8", errors="replace")
                rec["item_id"] = files[0].stem.split("_", 1)[-1]
                if raw.startswith("#"):
                    line0, _, body = raw.partition("\n")
                    rec["title"] = line0.lstrip("# ").strip()
                    rec["text"] = body.strip()
                else:
                    rec["text"] = raw
                rec["chars"] = len(norm_text(rec["text"]))
                rec["ok"] = rec["chars"] > 50
            else:
                rec["error"] = "missing_file"
            chs.append(rec)
        out[bid] = {
            "book_id": bid,
            "name": name_by_id.get(bid, bid),
            "ok": any(c["ok"] for c in chs),
            "title": "",
            "chapters": chs,
            "error": None,
        }
    return out


def main() -> int:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--web-only", action="store_true")
    ap.add_argument("--app-only", action="store_true")
    ap.add_argument(
        "--merge-web",
        type=str,
        default="",
        help="已有 compare 目录或 web_results.json 所在目录，与本次 app 合并对比",
    )
    ap.add_argument(
        "--out",
        type=str,
        default="",
        help="输出目录（默认 tmp/fanqie_probe/compare_时间戳）",
    )
    args = ap.parse_args()
    if args.out:
        OUT = Path(args.out)
        OUT.mkdir(parents=True, exist_ok=True)
    do_web = not args.app_only
    do_app = not args.web_only

    print(f"[*] OUT={OUT}", flush=True)
    summary = {
        "out": str(OUT),
        "books": [],
        "n_chapters": N_CH,
        "note": "web no-cookie unless FANQIE_COOKIE; app uses 番茄 sign + 番茄 decrypt",
    }

    web_results: dict[str, dict] = {}
    app_results: dict[str, dict] = {}

    if args.merge_web:
        merge_path = Path(args.merge_web)
        print(f"[*] load web from {merge_path}", flush=True)
        web_results = load_web_from_dir(merge_path)
        print(f"[*] loaded web books: {list(web_results.keys())}", flush=True)
        do_web = False

    if do_web:
        print("\n======== WEB ========", flush=True)
        for book in BOOKS:
            print(f"\n[web] {book['name']} {book['book_id']}", flush=True)
            web_results[book["book_id"]] = run_web(book)

    if do_app:
        print("\n======== APP API ========", flush=True)
        oracle = ensure_dragon_for_oracle()
        for book in BOOKS:
            print(f"\n[app] {book['name']} {book['book_id']}", flush=True)
            pref = None
            wr = web_results.get(book["book_id"]) or {}
            if wr.get("chapters"):
                pref = [str(c.get("item_id") or "") for c in wr["chapters"]]
            app_results[book["book_id"]] = run_app(book, oracle, preferred_ids=pref)
        if oracle:
            try:
                oracle.close()
            except Exception:
                pass
        try:
            H.get_oracle().close()
        except Exception:
            pass

    print("\n======== COMPARE ========", flush=True)
    compares = []
    for book in BOOKS:
        bid = book["book_id"]
        w = web_results.get(bid) or {"book_id": bid, "name": book["name"], "chapters": []}
        a = app_results.get(bid) or {"book_id": bid, "name": book["name"], "chapters": []}
        c = compare_book(w, a)
        compares.append(c)
        print(
            f"{book['name']}: web_ok={c['web_book_ok']} app_ok={c['app_book_ok']} "
            f"both={c['both_ok_count']} avg_sim={c['avg_text_sim_when_both_ok']}",
            flush=True,
        )
        for row in c["chapters_compared"]:
            print(
                f"  #{row['index']}: web={row['web_ok']}/{row['web_chars']} "
                f"app={row['app_ok']}/{row['app_chars']} sim={row['text_sim']} "
                f"werr={row['web_err']} aerr={row['app_err']}",
                flush=True,
            )

    summary["web"] = web_results
    summary["app"] = app_results
    summary["compare"] = compares
    # 写精简报告（不含全文）
    slim = {
        "out": str(OUT),
        "n_chapters": N_CH,
        "compare": compares,
        "web_errors": {
            k: {"ok": v.get("ok"), "error": v.get("error"), "title": v.get("title")}
            for k, v in web_results.items()
        },
        "app_errors": {
            k: {"ok": v.get("ok"), "error": v.get("error")}
            for k, v in app_results.items()
        },
    }
    (OUT / "report.json").write_text(
        json.dumps(slim, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 全文结果较大，分文件
    (OUT / "web_results.json").write_text(
        json.dumps(web_results, ensure_ascii=False, indent=2)[:2_000_000],
        encoding="utf-8",
    )
    # app 结果去掉大 text 保留摘要
    app_slim = {}
    for k, v in app_results.items():
        chs = []
        for c in v.get("chapters") or []:
            cc = dict(c)
            if len(cc.get("text") or "") > 500:
                cc["text_preview"] = (cc.pop("text") or "")[:500]
            chs.append(cc)
        app_slim[k] = {**v, "chapters": chs}
    (OUT / "app_results.json").write_text(
        json.dumps(app_slim, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n[*] report: {OUT / 'report.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

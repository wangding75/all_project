"""测试番茄小说独立的签名、拉章以及联合解密流程（不依赖红果模块）"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / ".venv" / "Lib" / "site-packages"))

os.environ.setdefault("ADB", r"D:\install\Netease\MuMu\nx_main\adb.exe")
os.environ.setdefault("ADB_DEVICE", "127.0.0.1:16384")
os.environ.setdefault("FRIDA_HOST", "127.0.0.1:27042")

from platforms.fanqie import client
from platforms.fanqie.app_content import resolve_key, resolve_version
from platforms.fanqie.crypt_oracle import FanqieCryptOracle


def main() -> int:
    print("=== 1. 测试搜索 ===")
    query = "这个游戏不对劲"
    try:
        results = client.search(query, max_items=3)
        print(f"搜索 '{query}'，获得 {len(results)} 条结果:")
        for idx, item in enumerate(results, 1):
            print(f"  [{idx}] {item['title']} - {item['author']} (ID: {item['book_id']})")
    except Exception as e:
        print(f"搜索失败: {e}")
        return 1

    if not results:
        print("未找到书籍")
        return 1

    book_id = results[0]["book_id"]
    book_title = results[0]["title"]

    print(f"\n=== 2. 测试获取目录 (书籍: {book_title}, ID: {book_id}) ===")
    try:
        item_ids, raw_dir = client.get_directory(book_id)
        print(f"获得章节数量: {len(item_ids)}")
        if item_ids:
            print(f"前5章 IDs: {item_ids[:5]}")
    except Exception as e:
        print(f"获取目录失败: {e}")
        return 1

    if not item_ids:
        print("目录为空")
        return 1

    item_id = item_ids[0]
    print(f"\n=== 3. 测试拉取加密章节数据 (章节 ID: {item_id}) ===")
    try:
        j = client.fetch_full(book_id, item_id)
        print("拉取接口响应 code:", j.get("code"))
        data = j.get("data") or {}
        print("data 包含字段:", list(data.keys()))
        cipher = data.get("content")
        if not cipher:
            print("未在响应中找到 content 密文")
            return 1
        print("密文长度:", len(cipher), "头部样本:", cipher[:100])
    except Exception as e:
        print(f"拉取密文失败: {e}")
        return 1

    print("\n=== 4. 测试解密 ===")
    try:
        # 获取会话密钥与密钥版本
        key = resolve_key()
        ver = resolve_version()
        print(f"解密密钥 (resolve_key): {key[:40]}...")
        print(f"解密密钥版本 (resolve_version): {ver}")

        o = FanqieCryptOracle()
        o.attach()
        try:
            r = o.decrypt_raw(cipher, key, ver)
            print("解密结果 ok:", r.ok)
            if not r.ok or not r.text:
                print("解密失败 error:", r.error)
                return 1
            print("解密文本字数:", len(r.text))
            print("解密正文片段 (前200字):")
            print(r.text[:200].replace("\n", " "))
        finally:
            o.close()
    except Exception as e:
        print(f"解密验证发生异常: {e}")
        return 1

    print("\n=== 测试全部成功 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

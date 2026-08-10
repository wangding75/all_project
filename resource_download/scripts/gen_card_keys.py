#!/usr/bin/env python3
"""历史本地 CardKey 迁移工具（不生成新的生产 License）。

运行说明：
在仓库根目录下设置 PYTHONPATH=server 后运行：
$env:PYTHONPATH="server"
python scripts/gen_card_keys.py --legacy-migration-only --days 30 --count 10 --batch B20260720

新生产 License Key 必须由 License Service 管理面生成；本脚本默认禁用。
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

# 将 server 目录添加到 sys.path 以便导入 app 模块
server_dir = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(server_dir))

from app.db import SessionLocal
from app.models_orm import CardKey


def main() -> None:
    parser = argparse.ArgumentParser(description="仅用于历史 RD CardKey 迁移数据的本地工具。")
    parser.add_argument(
        "--legacy-migration-only",
        action="store_true",
        help="明确确认只生成 legacy/migration 数据；不能用于新生产 License",
    )
    parser.add_argument("--days", type=int, default=30, help="卡密可延期的 VIP 天数 (默认 30)")
    parser.add_argument("--count", type=int, default=10, help="要生成的卡密数量 (默认 10)")
    parser.add_argument("--batch", type=str, default=None, help="批次 ID (可选)")

    args = parser.parse_args()

    if not args.legacy_migration_only:
        print("LEGACY_LOCAL_CARD_KEYS_DISABLED", file=sys.stderr)
        print(
            "本地 CardKey 不能生成新的生产 License；如确需历史迁移，请显式使用 --legacy-migration-only。",
            file=sys.stderr,
        )
        raise SystemExit(2)

    db = SessionLocal()
    try:
        codes = []
        for _ in range(args.count):
            # 生成高熵随机卡密 RD-XXXXXX (24个十六进制字符)
            code = f"RD-{secrets.token_hex(12).upper()}"
            card = CardKey(
                code=code,
                duration_days=args.days,
                batch_id=args.batch,
            )
            db.add(card)
            codes.append(code)

        db.commit()

        print(
            f"成功生成并保存 {len(codes)} 张卡密 (批次: {args.batch or '无'}，天数: {args.days})："
        )
        for code in codes:
            print(code)
        print("\n* 提醒：请勿提交生成的卡密到 Git 仓库！")

    except Exception as exc:
        db.rollback()
        print(f"生成卡密时遇到错误: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""SQLite 数据库与配置文件在线热备份/恢复工具 (Stage E5)。

特性：
使用 Python 原生 sqlite3.backup() API 实现无锁在线热备份，可以在 FastAPI 服务持续运行过程中安全备份。

运行说明：
在仓库根目录下设置 PYTHONPATH=server 后运行：
$env:PYTHONPATH="server"
python scripts/backup_db.py backup
python scripts/backup_db.py list
python scripts/backup_db.py restore --file data/backups/app_backup_20260723_160000.db
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# 将 server 目录添加到 sys.path
server_dir = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(server_dir))

from app.config import get_settings


def get_db_path() -> Path:
    settings = get_settings()
    return (settings.data_dir / "app.db").resolve()


def get_backup_dir() -> Path:
    settings = get_settings()
    backup_dir = (settings.data_dir / "backups").resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def cmd_backup(args) -> None:
    db_path = get_db_path()
    if not db_path.exists():
        print(f"错误: 数据库文件不存在 '{db_path}'", file=sys.stderr)
        sys.exit(1)

    backup_dir = get_backup_dir()
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file_name = f"app_backup_{timestamp_str}.db"
    target_path = backup_dir / backup_file_name

    print(f"正在进行 SQLite 在线热备份...")
    print(f"源数据库: {db_path}")
    print(f"备份目标: {target_path}")

    try:
        source_conn = sqlite3.connect(str(db_path))
        target_conn = sqlite3.connect(str(target_path))

        with target_conn:
            source_conn.backup(target_conn, pages=100, progress=None)

        target_conn.close()
        source_conn.close()

        size_kb = target_path.stat().st_size / 1024
        print(f"✅ 在线热备份成功完成! 备份文件大小: {size_kb:.2f} KB")

        # 提示备份 .env 配置文件（提示勿泄露敏感密钥）
        env_file = Path(__file__).resolve().parents[1] / ".env"
        if env_file.exists():
            env_backup_path = backup_dir / f"env_backup_{timestamp_str}.env.txt"
            shutil.copy2(env_file, env_backup_path)
            print(f"✅ 已同时安全备份配置文件到: {env_backup_path}")
            print("* 提醒：备份目录 `data/backups/` 请务必妥善保管，勿提交 Git。")

    except Exception as exc:
        print(f"备份过程中发生异常: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args) -> None:
    backup_dir = get_backup_dir()
    backups = sorted(backup_dir.glob("app_backup_*.db"), reverse=True)

    if not backups:
        print(f"备份目录中未找到任何历史备份文件 ('{backup_dir}')。")
        return

    print(f"=== 数据库历史备份列表 ('{backup_dir}') ===")
    print(f"{'文件名':<35} {'文件大小 (KB)':<15} {'修改时间':<25}")
    print("-" * 75)
    for b in backups:
        st = b.stat()
        size_kb = st.st_size / 1024
        mtime_str = datetime.fromtimestamp(st.mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"{b.name:<35} {size_kb:<15.2f} {mtime_str:<25}")


def cmd_restore(args) -> None:
    restore_file = Path(args.file).resolve()
    if not restore_file.exists() or not restore_file.is_file():
        print(f"错误: 还原备份文件不存在 '{restore_file}'", file=sys.stderr)
        sys.exit(1)

    db_path = get_db_path()
    print(f"⚠️ 警告: 正在将数据库从备份还原！此操作将覆盖现有数据库。")
    print(f"备份文件: {restore_file}")
    print(f"目标数据库: {db_path}")

    try:
        source_conn = sqlite3.connect(str(restore_file))
        target_conn = sqlite3.connect(str(db_path))

        with target_conn:
            source_conn.backup(target_conn)

        target_conn.close()
        source_conn.close()

        print(f"✅ 数据库已被成功从备份文件还原！")

    except Exception as exc:
        print(f"数据库还原失败: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="SQLite 数据库在线热备份与还原工具 (Stage E5)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup
    p_backup = subparsers.add_parser("backup", help="在线热备份当前 app.db 数据库")
    p_backup.set_defaults(func=cmd_backup)

    # list
    p_list = subparsers.add_parser("list", help="列出本地所有可用的备份文件")
    p_list.set_defaults(func=cmd_list)

    # restore
    p_restore = subparsers.add_parser("restore", help="从指定备份文件还原数据库")
    p_restore.add_argument("--file", type=str, required=True, help="备份 DB 文件路径")
    p_restore.set_defaults(func=cmd_restore)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

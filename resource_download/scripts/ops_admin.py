#!/usr/bin/env python3
"""运维与客服管理 CLI 工具 (Stage E4)。

运行说明：
在仓库根目录下设置 PYTHONPATH=server 后运行：
$env:PYTHONPATH="server"
python scripts/ops_admin.py ban-user --username test_user
python scripts/ops_admin.py unban-user --username test_user
python scripts/ops_admin.py invalidate-batch --batch-id B20260720
python scripts/ops_admin.py inspect-user --username test_user
python scripts/ops_admin.py list-users
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# 将 server 目录添加到 sys.path
server_dir = Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(server_dir))

from app.db import SessionLocal
from app.models_orm import CardKey, UsageDaily, User


def get_user_by_id_or_name(db, user_id: int | None, username: str | None) -> User | None:
    if user_id is not None:
        return db.query(User).filter(User.id == user_id).first()
    if username:
        return db.query(User).filter(User.username == username).first()
    return None


def cmd_ban_user(args) -> None:
    db = SessionLocal()
    try:
        user = get_user_by_id_or_name(db, args.user_id, args.username)
        if not user:
            print(f"错误: 未找到对应用户 (user_id={args.user_id}, username={args.username})", file=sys.stderr)
            sys.exit(1)
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        print(f"✅ 成功封禁用户: ID={user.id}, Username={user.username}, is_active=False")
    finally:
        db.close()


def cmd_unban_user(args) -> None:
    db = SessionLocal()
    try:
        user = get_user_by_id_or_name(db, args.user_id, args.username)
        if not user:
            print(f"错误: 未找到对应用户 (user_id={args.user_id}, username={args.username})", file=sys.stderr)
            sys.exit(1)
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        print(f"✅ 成功解封用户: ID={user.id}, Username={user.username}, is_active=True")
    finally:
        db.close()


def cmd_invalidate_batch(args) -> None:
    db = SessionLocal()
    try:
        query = db.query(CardKey).filter(
            CardKey.batch_id == args.batch_id,
            CardKey.is_used == False,
        )
        count = query.count()
        if count == 0:
            print(f"⚠️ 批次 '{args.batch_id}' 无可作废的未使用卡密。")
            return
        query.update({CardKey.is_used: True}, synchronize_session=False)
        db.commit()
        print(f"✅ 成功作废批次 '{args.batch_id}' 下的 {count} 张未兑换卡密。")
    finally:
        db.close()


def cmd_inspect_user(args) -> None:
    db = SessionLocal()
    try:
        user = get_user_by_id_or_name(db, args.user_id, args.username)
        if not user:
            print(f"错误: 未找到对应用户 (user_id={args.user_id}, username={args.username})", file=sys.stderr)
            sys.exit(1)

        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        is_vip = bool(user.vip_expires_at and user.vip_expires_at > now_utc)

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        usage = (
            db.query(UsageDaily)
            .filter(UsageDaily.user_id == user.id, UsageDaily.day == today_str)
            .first()
        )
        job_count_today = usage.job_count if usage else 0

        print(f"--- 用户状态明细 ---")
        print(f"用户 ID:        {user.id}")
        print(f"用户名:         {user.username}")
        print(f"账号启用状态:   {'启用' if user.is_active else '禁用 (Banned)'}")
        print(f"注册时间:       {user.created_at}")
        print(f"VIP 到期时间:   {user.vip_expires_at or '未生效/非 VIP'}")
        print(f"VIP 状态:       {'VIP 会员' if is_vip else '普通用户'}")
        print(f"今日创建任务数: {job_count_today}")
    finally:
        db.close()


def cmd_list_users(args) -> None:
    db = SessionLocal()
    try:
        users = (
            db.query(User)
            .order_by(User.id.asc())
            .offset(args.skip)
            .limit(args.limit)
            .all()
        )
        total = db.query(User).count()
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

        print(f"=== 用户列表 (共 {total} 名用户，显示 {len(users)} 名) ===")
        print(f"{'ID':<5} {'用户名':<18} {'状态':<8} {'VIP 状态':<12} {'VIP 到期时间':<24}")
        print("-" * 70)
        for u in users:
            is_vip = bool(u.vip_expires_at and u.vip_expires_at > now_utc)
            vip_str = "VIP" if is_vip else "普通"
            status_str = "正常" if u.is_active else "禁用"
            exp_str = str(u.vip_expires_at) if u.vip_expires_at else "无"
            print(f"{u.id:<5} {u.username:<18} {status_str:<8} {vip_str:<12} {exp_str:<24}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="运维与客服管理 CLI 工具 (Stage E4)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ban-user
    p_ban = subparsers.add_parser("ban-user", help="封禁/禁用指定用户")
    p_ban.add_argument("--user-id", type=int, help="用户 ID")
    p_ban.add_argument("--username", type=str, help="用户名")
    p_ban.set_defaults(func=cmd_ban_user)

    # unban-user
    p_unban = subparsers.add_parser("unban-user", help="解封/启用指定用户")
    p_unban.add_argument("--user-id", type=int, help="用户 ID")
    p_unban.add_argument("--username", type=str, help="用户名")
    p_unban.set_defaults(func=cmd_unban_user)

    # invalidate-batch
    p_inv = subparsers.add_parser("invalidate-batch", help="按批次作废未兑换卡密")
    p_inv.add_argument("--batch-id", type=str, required=True, help="卡密批次 ID")
    p_inv.set_defaults(func=cmd_invalidate_batch)

    # inspect-user
    p_insp = subparsers.add_parser("inspect-user", help="查询用户 VIP 状态与限流指标")
    p_insp.add_argument("--user-id", type=int, help="用户 ID")
    p_insp.add_argument("--username", type=str, help="用户名")
    p_insp.set_defaults(func=cmd_inspect_user)

    # list-users
    p_list = subparsers.add_parser("list-users", help="分页列出系统所有用户")
    p_list.add_argument("--skip", type=int, default=0, help="跳过数量")
    p_list.add_argument("--limit", type=int, default=50, help="拉取限制数量")
    p_list.set_defaults(func=cmd_list_users)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

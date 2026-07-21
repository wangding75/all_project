"""签名池 HTTP 客户端（与节点 契约 POST /sign 交互，具备自动故障重试与节点摘除能力）。"""

from __future__ import annotations

import logging
from typing import Any

import requests

from app.config import get_settings
from app.sign_pool.errors import SignPoolUnavailableError
from app.sign_pool.models import SignRequest, SignResponse

logger = logging.getLogger(__name__)


def sign_via_pool(
    label: str,
    url: str,
    headers: dict[str, str],
    max_retries: int = 1,
    timeout_sec: float = 12.0,
    pool: Any | None = None,
) -> dict[str, str]:
    """通过签名节点池获取 App 接口签名。

    契约:
      POST {node.base_url}/sign
      Request Body:  {"url": url, "headers": headers}
      Response Body: {"headers": {"x-argus": "...", ...}}

    - 节点失败时自动 report_failure 并 release lease。
    - 最多换 1 个节点重试 1 次（共 2 次尝试）。
    - 若全挂或无可用节点，抛出 SignPoolUnavailableError。
    """
    if pool is None:
        from app.sign_pool import get_sign_pool

        pool = get_sign_pool()

    settings = get_settings()
    last_exc: Exception | None = None

    attempts = max(1, 1 + max_retries)

    for attempt in range(attempts):
        try:
            node_state, lease_id = pool.acquire(label=label, lease_sec=settings.sign_pool_lease_sec)
        except SignPoolUnavailableError as exc:
            raise exc from exc

        node_id = node_state.config.id
        sign_url = f"{node_state.config.base_url.rstrip('/')}/sign"
        req_body = SignRequest(url=url, headers=headers).model_dump()

        try:
            resp = requests.post(sign_url, json=req_body, timeout=timeout_sec)
            resp.raise_for_status()
            data = resp.json()

            # 解析符合规范的 {"headers": {...}} 结构
            sign_resp = SignResponse.model_validate(data)
            signed_headers = sign_resp.headers

            # 签名成功：上报 success 并在锁内释放租约
            pool.report_success(node_id)
            pool.release(node_id, lease_id)

            return signed_headers

        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            logger.warning(
                f"Sign attempt {attempt + 1}/{attempts} failed on node {node_id} ({sign_url}): {exc}"
            )
            # 失败：上报 failure 并释放租约
            pool.report_failure(node_id, max_fails=settings.sign_pool_max_fails)
            pool.release(node_id, lease_id)

    raise SignPoolUnavailableError("签名节点繁忙或不可用，请稍后重试") from last_exc

"""签名节点池的核心池管理实现（线程安全、锁保护、容量控制、租约与健康检查）。"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import requests

from app.sign_pool.errors import SignPoolUnavailableError
from app.sign_pool.models import NodeConfig, NodeState, PoolConfig

logger = logging.getLogger(__name__)


class SignPool:
    """签名节点池管理类（全局锁 protection）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.nodes: dict[str, NodeState] = {}
        self._rr_counter: int = 0

    def load_from_config(
        self,
        config_path: Path | str | None = None,
        urls: str = "",
        default_labels: list[str] | None = None,
    ) -> None:
        """从 JSON 配置文件或 URL 列表初始化节点池。"""
        if default_labels is None:
            default_labels = ["fanqie_sign"]

        node_configs: list[NodeConfig] = []

        # 优先读取配置文件
        if config_path:
            p = Path(config_path)
            if p.is_file():
                try:
                    content = p.read_text(encoding="utf-8")
                    parsed = json.loads(content)
                    pool_cfg = PoolConfig.model_validate(parsed)
                    node_configs = pool_cfg.nodes
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Failed to load sign pool config from {p}: {exc}")

        # 若文件未找到或配置为空，解析 URL 字符串
        if not node_configs and urls:
            url_list = [u.strip() for u in urls.split(",") if u.strip()]
            for idx, u in enumerate(url_list, start=1):
                node_configs.append(
                    NodeConfig(
                        id=f"node-{idx}",
                        base_url=u.rstrip("/"),
                        labels=list(default_labels),
                        capacity=2,
                        enabled=True,
                    )
                )

        with self._lock:
            self.nodes.clear()
            for n_cfg in node_configs:
                self.nodes[n_cfg.id] = NodeState(config=n_cfg)

    def add_node(self, node_cfg: NodeConfig) -> NodeState:
        """动态添加节点。"""
        with self._lock:
            state = NodeState(config=node_cfg)
            self.nodes[node_cfg.id] = state
            return state

    def clean_leases(self) -> int:
        """清理所有节点的超期租约。"""
        now = time.time()
        total_cleaned = 0
        with self._lock:
            for state in self.nodes.values():
                total_cleaned += state.clean_expired_leases(now)
        return total_cleaned

    def acquire(self, label: str | None = None, lease_sec: int = 120) -> tuple[NodeState, str]:
        """按 label、健康状态与容量配额 租用/轮询 可用节点。

        Returns:
            (NodeState, lease_id)

        Raises:
            SignPoolUnavailableError: 当没有任何可用健康节点时抛出。
        """
        now = time.time()
        with self._lock:
            self.clean_leases()

            candidates: list[NodeState] = []
            for state in self.nodes.values():
                if not state.config.enabled or not state.healthy:
                    continue
                if label and label not in state.config.labels:
                    continue
                if state.in_use >= state.config.capacity:
                    continue
                candidates.append(state)

            if not candidates:
                raise SignPoolUnavailableError("签名节点繁忙或不可用，请稍后重试")

            # 排序策略：优先选择 in_use 最小的；若相同则按轮询次序调度
            candidates.sort(key=lambda s: s.in_use)
            min_in_use = candidates[0].in_use
            best_candidates = [s for s in candidates if s.in_use == min_in_use]

            selected = best_candidates[self._rr_counter % len(best_candidates)]
            self._rr_counter += 1

            lease_id = uuid.uuid4().hex
            selected.leases[lease_id] = now + lease_sec
            selected.in_use = len(selected.leases)

            return selected, lease_id

    def release(self, node_id: str, lease_id: str | None = None) -> None:
        """归还/释放节点的租约。"""
        with self._lock:
            state = self.nodes.get(node_id)
            if not state:
                return
            if lease_id and lease_id in state.leases:
                del state.leases[lease_id]
            state.in_use = max(0, len(state.leases))

    def report_failure(self, node_id: str, max_fails: int = 3) -> None:
        """记录节点失败。当连续失败次数达到 max_fails 时摘除（标记 unhealthy）。"""
        with self._lock:
            state = self.nodes.get(node_id)
            if not state:
                return
            state.fail_count += 1
            if state.fail_count >= max_fails:
                state.healthy = False
                logger.warning(f"Sign node {node_id} marked UNHEALTHY (fail_count={state.fail_count})")

    def report_success(self, node_id: str) -> None:
        """记录节点成功。恢复健康状态并重置 fail_count。"""
        with self._lock:
            state = self.nodes.get(node_id)
            if not state:
                return
            state.fail_count = 0
            state.healthy = True

    def health_check(self, timeout_sec: float = 3.0, max_fails: int = 3) -> dict[str, bool]:
        """对池内所有启用的节点执行 HTTP GET /health 探针。"""
        with self._lock:
            nodes_snapshot = list(self.nodes.values())

        results: dict[str, bool] = {}
        now = time.time()

        for state in nodes_snapshot:
            if not state.config.enabled:
                continue

            health_url = f"{state.config.base_url.rstrip('/')}/health"
            is_ok = False
            try:
                resp = requests.get(health_url, timeout=timeout_sec)
                if resp.status_code == 200:
                    is_ok = True
            except Exception as exc:  # noqa: BLE001
                logger.debug(f"Health check probe failed for {state.config.id} ({health_url}): {exc}")

            state.last_check = now
            if is_ok:
                self.report_success(state.config.id)
            else:
                self.report_failure(state.config.id, max_fails=max_fails)
            results[state.config.id] = is_ok

        return results

    def get_summary(self) -> dict[str, Any]:
        """获取 Ops 摘要数据。"""
        with self._lock:
            self.clean_leases()
            total = len(self.nodes)
            enabled = sum(1 for s in self.nodes.values() if s.config.enabled)
            healthy = sum(1 for s in self.nodes.values() if s.config.enabled and s.healthy)
            in_use_sum = sum(s.in_use for s in self.nodes.values())

            nodes_list = [s.to_dict() for s in self.nodes.values()]

            return {
                "total_nodes": total,
                "enabled_nodes": enabled,
                "healthy_nodes": healthy,
                "total_in_use": in_use_sum,
                "nodes": nodes_list,
            }

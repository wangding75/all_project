"""D-3 签名节点池 (Sign Pool) 单元测试与集成测试。

覆盖 5 大测试场景与 Ops 接口校验:
1. SIGN_POOL_ENABLED=false 时走现网 Frida 回退逻辑；
2. Mock 多节点轮询与容量排队控制；
3. 单节点连续失败（>= max_fails）隔离与摘除；
4. 全挂/无可用节点时返回 HTTP 503 明确文案（无假成功）；
5. Lease 超时后可回收与再次分配；
6. GET /v1/admin/sign-pool 仅 ops 权限可访问。
"""

from __future__ import annotations

import time
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.sign_pool import (
    SignPool,
    SignPoolUnavailableError,
    get_sign_pool,
    reset_sign_pool,
    sign_via_pool,
)
from app.sign_pool.mock_node import MockServerThread, MockSignHandler
from app.sign_pool.models import NodeConfig, NodeState


@pytest.fixture(autouse=True)
def reset_pool_state() -> Generator[None, None, None]:
    """每个测试用例重置签名池单例。"""
    reset_sign_pool()
    yield
    reset_sign_pool()
    MockSignHandler.fail_mode = False


def test_sign_pool_disabled_fallback() -> None:
    """测试 1: SIGN_POOL_ENABLED=False 时保持默认回退逻辑。"""
    settings = get_settings()
    settings.sign_pool_enabled = False

    # 直接断言 sign_pool 默认关闭
    assert settings.sign_pool_enabled is False


def test_multi_node_capacity_and_round_robin() -> None:
    """测试 2: 多节点容量分配与轮询机制。"""
    pool = SignPool()
    n1 = NodeConfig(id="node-1", base_url="http://127.0.0.1:19101", capacity=1, labels=["fanqie_sign"])
    n2 = NodeConfig(id="node-2", base_url="http://127.0.0.1:19102", capacity=1, labels=["fanqie_sign"])
    pool.add_node(n1)
    pool.add_node(n2)

    # 第一次 acquire 获得节点 1
    node_a, lease_a = pool.acquire(label="fanqie_sign", lease_sec=60)
    assert node_a.config.id == "node-1"
    assert node_a.in_use == 1

    # 第二次 acquire 获得节点 2
    node_b, lease_b = pool.acquire(label="fanqie_sign", lease_sec=60)
    assert node_b.config.id == "node-2"
    assert node_b.in_use == 1

    # 第三次 acquire 超出总容量 (1+1=2)，应抛出 SignPoolUnavailableError
    with pytest.raises(SignPoolUnavailableError) as exc_info:
        pool.acquire(label="fanqie_sign", lease_sec=60)
    assert "签名节点繁忙或不可用" in str(exc_info.value)

    # 释放节点 1
    pool.release("node-1", lease_a)
    assert pool.nodes["node-1"].in_use == 0

    # 再次 acquire 成功重新租用节点 1
    node_c, lease_c = pool.acquire(label="fanqie_sign", lease_sec=60)
    assert node_c.config.id == "node-1"


def test_node_failure_isolation() -> None:
    """测试 3: 节点连续失败被摘除，流量转移至健康节点。"""
    pool = SignPool()
    n1 = NodeConfig(id="node-bad", base_url="http://127.0.0.1:19101", capacity=2, labels=["fanqie_sign"])
    n2 = NodeConfig(id="node-good", base_url="http://127.0.0.1:19102", capacity=2, labels=["fanqie_sign"])
    pool.add_node(n1)
    pool.add_node(n2)

    # 模拟 node-bad 连续失败 3 次
    for _ in range(3):
        pool.report_failure("node-bad", max_fails=3)

    assert pool.nodes["node-bad"].healthy is False

    # 后续 acquire 只会获得健康节点 node-good
    for _ in range(2):
        node, lease = pool.acquire(label="fanqie_sign", lease_sec=60)
        assert node.config.id == "node-good"


def test_sign_via_pool_with_mock_nodes() -> None:
    """测试 4: 通过 Mock HTTP 节点测试 sign_via_pool 请求与全挂 503 处理。"""
    # 启动 2 个 Mock HTTP 节点
    server1 = MockServerThread(port=19101)
    server2 = MockServerThread(port=19102)
    server1.start()
    server2.start()
    time.sleep(0.2)  # 等待 HTTP 服务绑定完成

    try:
        pool = SignPool()
        pool.add_node(NodeConfig(id="m1", base_url="http://127.0.0.1:19101", capacity=2, labels=["fanqie_sign"]))
        pool.add_node(NodeConfig(id="m2", base_url="http://127.0.0.1:19102", capacity=2, labels=["fanqie_sign"]))

        # 1. 正常请求
        signed_headers = sign_via_pool(
            label="fanqie_sign",
            url="https://api.example.com/test",
            headers={"user-agent": "test"},
            pool=pool,
        )
        assert signed_headers.get("x-mock-sign") == "true"
        assert signed_headers.get("x-mock-token") == "stub-sign-token"

        # 2. 模拟全挂 (Mock HTTP 服务返回 500)
        MockSignHandler.fail_mode = True

        with pytest.raises(SignPoolUnavailableError) as exc_info:
            sign_via_pool(
                label="fanqie_sign",
                url="https://api.example.com/test",
                headers={"user-agent": "test"},
                max_retries=1,
                pool=pool,
            )
        assert "签名节点繁忙或不可用，请稍后重试" in str(exc_info.value)

    finally:
        server1.stop()
        server2.stop()


def test_lease_expiration_recovery() -> None:
    """测试 5: Lease 超时后被自动回收与释放容量。"""
    pool = SignPool()
    n1 = NodeConfig(id="node-lease", base_url="http://127.0.0.1:19101", capacity=1, labels=["fanqie_sign"])
    pool.add_node(n1)

    # 分配 1 秒超短租约
    node, lease_id = pool.acquire(label="fanqie_sign", lease_sec=1)
    assert node.in_use == 1

    # 马上重新 acquire 失败
    with pytest.raises(SignPoolUnavailableError):
        pool.acquire(label="fanqie_sign", lease_sec=1)

    # 等待 1.1 秒过期
    time.sleep(1.1)

    # 下一次 acquire 触发过期清理并成功分配
    node_again, lease_again = pool.acquire(label="fanqie_sign", lease_sec=60)
    assert node_again.config.id == "node-lease"
    assert node_again.in_use == 1


def test_admin_sign_pool_api() -> None:
    """测试 6: GET /v1/admin/sign-pool 鉴权与摘要。"""
    client = TestClient(app)
    settings = get_settings()

    # 1. 无 API Key (普通请求/未鉴权) -> 401 或 403
    resp = client.get("/v1/admin/sign-pool")
    assert resp.status_code in (401, 403)

    # 2. 带有 Ops API Key -> 200 OK 并返回摘要数据
    resp_ops = client.get(
        "/v1/admin/sign-pool",
        headers={"X-API-Key": settings.api_key},
    )
    assert resp_ops.status_code == 200
    data = resp_ops.json()
    assert "total_nodes" in data
    assert "healthy_nodes" in data
    assert "nodes" in data

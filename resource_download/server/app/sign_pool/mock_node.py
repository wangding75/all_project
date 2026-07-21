"""Mock 签名节点服务实现（提供测试与 CLI 模拟服务）。

用法:
    python -m app.sign_pool.mock_node --port 19101
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from typing import Any


class MockSignHandler(BaseHTTPRequestHandler):
    """Mock 签名 HTTP 处理器，支持 GET /health 与 POST /sign。"""

    fail_mode: bool = False  # 若为 True，则返回 500 服务器错误

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # 禁用标准输出日志，避免单元测试输出刷屏
        pass

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            if MockSignHandler.fail_mode:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"status": "error"}')
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/sign":
            if MockSignHandler.fail_mode:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"error": "node internal error"}')
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
                req_headers = data.get("headers", {})
            except Exception:  # noqa: BLE001
                req_headers = {}

            # 返回符合死契约的 {"headers": {...}} 结构
            resp_data = {
                "headers": {
                    "x-mock-sign": "true",
                    "x-mock-token": "stub-sign-token",
                    "x-req-headers-cnt": str(len(req_headers)),
                }
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def create_mock_server(host: str = "127.0.0.1", port: int = 19101) -> HTTPServer:
    return HTTPServer((host, port), MockSignHandler)


class MockServerThread(threading.Thread):
    def __init__(self, host: str = "127.0.0.1", port: int = 19101) -> None:
        super().__init__(daemon=True)
        self.server = create_mock_server(host, port)
        self.port = port

    def run(self) -> None:
        self.server.serve_forever()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock Sign Node Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=19101, help="Port to listen on")
    args = parser.parse_args()

    server = create_mock_server(args.host, args.port)
    print(f"Mock sign node running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down mock sign node...")
        server.shutdown()


if __name__ == "__main__":
    main()

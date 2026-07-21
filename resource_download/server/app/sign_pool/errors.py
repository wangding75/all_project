"""签名节点池异常类型定义。"""

from __future__ import annotations


class SignPoolError(Exception):
    """签名池基础异常。"""


class SignPoolUnavailableError(SignPoolError):
    """签名池无可用节点或全挂异常。"""

    def __init__(self, message: str = "签名节点繁忙或不可用，请稍后重试") -> None:
        super().__init__(message)
        self.message = message

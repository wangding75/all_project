"""服务端自动化任务。"""

from app.automation.hongguo_monitor import (
    HongguoMonitorService,
    get_hongguo_monitor_service,
)

__all__ = ["HongguoMonitorService", "get_hongguo_monitor_service"]

"""Run the real RD app with a process-local deterministic discovery fixture.

The production server has no T16-specific switch.  This launcher patches only
the already-imported platform lookups in the monitor and JobManager modules,
then starts the normal FastAPI application and lifespan.  It is therefore a
test/E2E harness, not a production discovery implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
SCRIPTS = ROOT / "scripts"
if str(SERVER) not in sys.path:
    sys.path.insert(0, str(SERVER))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from app.automation import hongguo_monitor  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.jobs import manager as jobs_manager  # noqa: E402
from app.main import app  # noqa: E402
from app.models import PlatformName  # noqa: E402
from platforms.registry import get_platform as real_get_platform  # noqa: E402
from t16_deterministic_discovery import DeterministicHongguoPlatform  # noqa: E402


def install_fixture() -> None:
    fixture = DeterministicHongguoPlatform()
    hongguo_monitor.get_platform = lambda _name: fixture

    def manager_platform(name):
        if name == PlatformName.hongguo or str(name) == PlatformName.hongguo.value:
            return fixture
        return real_get_platform(name)

    jobs_manager.get_platform = manager_platform


def main() -> None:
    import uvicorn

    install_fixture()
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()

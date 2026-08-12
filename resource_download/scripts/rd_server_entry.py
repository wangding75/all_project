"""Packaging entry point for the standalone RD server executable.

The regular ``server/run.py`` starts Uvicorn with an import string.  That is
correct for a source checkout, but an import string is not sufficient for a
PyInstaller archive because Uvicorn starts a second import lookup outside the
archive's normal module graph.  This entry point imports the FastAPI object
statically and passes the object to Uvicorn.  It is packaging glue only; the
application and security semantics remain in ``server/app``.
"""

from __future__ import annotations

import uvicorn

from app.config import get_settings
from app.main import app


def main() -> None:
    settings = get_settings()
    uvicorn.run(app, host=settings.host, port=settings.port, reload=False, workers=1)


if __name__ == "__main__":
    main()

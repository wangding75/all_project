"""Windows desktop shell."""
from .download_manager import DownloadManager
from .download_models import DownloadDescriptor, DownloadTask
from .download_repository import DownloadRepository
from .client_timer import ClientTimer

__all__ = ["ClientTimer", "DownloadDescriptor", "DownloadManager", "DownloadRepository", "DownloadTask"]

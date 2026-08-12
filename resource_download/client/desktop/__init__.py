"""Windows desktop shell."""
from .download_manager import DownloadManager
from .download_models import DownloadDescriptor, DownloadTask
from .download_repository import DownloadRepository

__all__ = ["DownloadDescriptor", "DownloadManager", "DownloadRepository", "DownloadTask"]

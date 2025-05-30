"""循環インポートを回避し、インターフェースを定義するためのプロトコル定義です。"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AppProtocol(Protocol):
    """循環インポートを回避するためのメインアプリケーションのプロトコルです。"""

    def copy_current_pages(self) -> None:
        """現在のページをクリップボードにコピーします。"""
        ...

    def set_status_message(self, message: str) -> None:
        """ステータスバーメッセージを設定します。"""
        ...

    def get_current_file(self) -> str:
        """現在開いているファイルパスを取得します。"""
        ...


@runtime_checkable
class ServiceProtocol(Protocol):
    """Base protocol for all services."""

    def initialize(self) -> None:
        """Initialize the service."""
        ...

    def shutdown(self) -> None:
        """Cleanup service resources."""
        ...


@runtime_checkable
class PDFServiceProtocol(Protocol):
    """Protocol for PDF-related services."""

    def open_document(self, path: str) -> None:
        """Open a PDF document."""
        ...

    def get_page_count(self) -> int:
        """Get number of pages in document."""
        ...

    def extract_pages(self, start: int, end: int) -> str:
        """Extract text from specified page range."""
        ...


@runtime_checkable
class CacheServiceProtocol(Protocol):
    """Protocol for cache services."""

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        ...

    def clear(self) -> None:
        """Clear all cache entries."""
        ...


@runtime_checkable
class ViewerProtocol(Protocol):
    """Protocol for PDF viewer components."""

    def load_pdf(self, filepath: str) -> None:
        """Load PDF file for viewing."""
        ...

    def get_zoom_level(self) -> float:
        """Get current zoom level."""
        ...

    def set_zoom_level(self, zoom: float) -> None:
        """Set zoom level."""
        ...

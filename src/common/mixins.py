"""共有動作パターンのための共通ミックスインです。"""

from ..logger import get_logger
from .protocols import AppProtocol


class StatusMixin:
    """ステータスメッセージを更新する必要があるコンポーネントのためのミックスインです。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app: AppProtocol | None = None

    def set_app(self, app: AppProtocol) -> None:
        """ステータス更新のためのアプリ参照を設定します。"""
        self._app = app

    def update_status(self, message: str) -> None:
        """ステータスバーメッセージを更新します。

        Parameters
        ----------
        message : str
            表示するステータスメッセージです。
        """
        if self._app:
            self._app.set_status_message(message)
        else:
            # アプリ参照がない場合はログにフォールバックします。
            logger = get_logger(self.__class__.__module__)
            logger.info(f"Status: {message}")


class SettingsMixin:
    """Mixin for components that need settings access."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings = None

    def get_settings(self):
        """Get settings instance (lazy loaded)."""
        if self._settings is None:
            from ..container import ServiceLocator

            try:
                self._settings = ServiceLocator.get("settings")
            except (RuntimeError, ValueError):
                # Fallback if container not configured
                from ..models.settings import ApplicationSettings

                self._settings = ApplicationSettings()
        return self._settings

    def save_settings(self) -> None:
        """Save current settings."""
        settings = self.get_settings()
        if settings:
            settings.save_settings()


class ValidationMixin:
    """Mixin for input validation functionality."""

    @staticmethod
    def validate_file_path(filepath: str) -> bool:
        """Validate if file path exists and is PDF.

        Args:
            filepath: File path to validate

        Returns:
            True if valid PDF file
        """
        import os

        if not filepath or not os.path.exists(filepath):
            return False
        return filepath.lower().endswith(".pdf")

    @staticmethod
    def validate_page_number(page_num: int, max_pages: int) -> bool:
        """Validate page number is within bounds.

        Args:
            page_num: Page number to validate (0-based)
            max_pages: Maximum number of pages

        Returns:
            True if page number is valid
        """
        return 0 <= page_num < max_pages

    @staticmethod
    def validate_zoom_level(zoom: float) -> bool:
        """Validate zoom level is within reasonable bounds.

        Args:
            zoom: Zoom level to validate

        Returns:
            True if zoom level is valid
        """
        return 0.1 <= zoom <= 10.0


class CleanupMixin:
    """Mixin for proper resource cleanup."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cleanup_handlers = []

    def register_cleanup(self, handler: callable) -> None:
        """Register a cleanup handler.

        Args:
            handler: Function to call during cleanup
        """
        self._cleanup_handlers.append(handler)

    def cleanup(self) -> None:
        """Execute all registered cleanup handlers."""
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger = get_logger(self.__class__.__module__)
                logger.error(f"Error during cleanup: {e}")

        self._cleanup_handlers.clear()

        # Call parent cleanup if it exists
        if hasattr(super(), "cleanup"):
            super().cleanup()


class LoggingMixin:
    """Mixin for consistent logging functionality."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None

    @property
    def logger(self):
        """Get logger instance (lazy loaded)."""
        if self._logger is None:
            self._logger = get_logger(self.__class__.__module__)
        return self._logger

    def log_debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(f"{self.__class__.__name__}: {message}")

    def log_info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(f"{self.__class__.__name__}: {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(f"{self.__class__.__name__}: {message}")

    def log_error(self, message: str, exc: Exception = None) -> None:
        """Log error message."""
        if exc:
            self.logger.error(f"{self.__class__.__name__}: {message}", exc_info=exc)
        else:
            self.logger.error(f"{self.__class__.__name__}: {message}")


class ConfigMixin:
    """Mixin for configuration access."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._config_cache = {}

    def get_config(self, config_type: str):
        """Get configuration object by type.

        Args:
            config_type: Type of config ('window', 'pdf', 'ui', 'cache', etc.)

        Returns:
            Configuration object
        """
        if config_type not in self._config_cache:
            from ..config import app_config, cache_config, file_config, pdf_config, ui_config, window_config

            config_map = {
                "window": window_config,
                "pdf": pdf_config,
                "ui": ui_config,
                "cache": cache_config,
                "file": file_config,
                "app": app_config,
            }

            self._config_cache[config_type] = config_map.get(config_type)

        return self._config_cache[config_type]

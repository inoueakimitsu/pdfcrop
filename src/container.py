"""PDFCrop の依存性注入コンテナです。"""

from collections.abc import Callable
from typing import Any, TypeVar

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ServiceContainer:
    """シンプルな依存性注入コンテナです。"""

    def __init__(self):
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable] = {}
        self._singletons: dict[str, Any] = {}

    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        """サービスのファクトリー関数を登録します。

        Args:
            name : サービス名
            factory : サービスを作成するファクトリー関数
        """
        self._factories[name] = factory
        logger.debug(f"Registered factory for service: {name}")

    def register_singleton(self, name: str, factory: Callable[[], T]) -> None:
        """シングルトン サービスを登録します。

        Args:
            name : サービス名
            factory : サービスを作成するファクトリー関数（一度だけ呼び出されます）
        """

        def singleton_factory():
            if name not in self._singletons:
                self._singletons[name] = factory()
                logger.debug(f"Created singleton instance for: {name}")
            return self._singletons[name]

        self._factories[name] = singleton_factory
        logger.debug(f"Registered singleton factory for service: {name}")

    def register_instance(self, name: str, instance: T) -> None:
        """既存のインスタンスを登録します。

        Args:
            name : サービス名
            instance : サービスのインスタンス
        """
        self._services[name] = instance
        logger.debug(f"Registered instance for service: {name}")

    def get(self, name: str) -> Any:
        """名前でサービスを取得します。

        Args:
            name : サービス名

        Returns:
            サービスのインスタンス

        Raises:
            ValueError : サービスが登録されていない場合
        """
        # インスタンスが既に作成されているかチェックします。
        if name in self._services:
            return self._services[name]

        # ファクトリーが登録されているかチェックします。
        if name in self._factories:
            instance = self._factories[name]()
            # ファクトリーで作成されたインスタンスはキャッシュしません（シングルトンを除く）。
            return instance

        raise ValueError(f"Service not registered: {name}")

    def has(self, name: str) -> bool:
        """サービスが登録されているかチェックします。

        Args:
            name : サービス名

        Returns:
            サービスが登録されている場合は True
        """
        return name in self._services or name in self._factories

    def clear(self) -> None:
        """登録されたすべてのサービスをクリアします。"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Service container cleared")


class ServiceLocator:
    """サービス ロケーター パターンの実装です。"""

    _container: ServiceContainer | None = None

    @classmethod
    def set_container(cls, container: ServiceContainer) -> None:
        """サービス コンテナを設定します。

        Args:
            container : サービス コンテナのインスタンス
        """
        cls._container = container

    @classmethod
    def get(cls, name: str) -> Any:
        """コンテナからサービスを取得します。

        Args:
            name : サービス名

        Returns:
            サービスのインスタンス

        Raises:
            RuntimeError : コンテナが設定されていない場合
        """
        if cls._container is None:
            raise RuntimeError("Service container not set")
        return cls._container.get(name)

    @classmethod
    def has(cls, name: str) -> bool:
        """サービスが存在するかチェックします。

        Args:
            name : サービス名

        Returns:
            サービスが存在する場合は True
        """
        if cls._container is None:
            return False
        return cls._container.has(name)


def setup_container() -> ServiceContainer:
    """依存性注入コンテナをセットアップし、設定します。

    Returns:
        設定済みのサービス コンテナ
    """
    container = ServiceContainer()

    # コア サービスを登録します。
    from .models.settings import ApplicationSettings
    from .pyside_ui.services.clipboard_manager import ClipboardManager
    from .pyside_ui.services.page_cache import PageCache
    from .pyside_ui.services.pdf_handler import PDFDocumentHandler

    # シングルトンを登録します。
    container.register_singleton("settings", lambda: ApplicationSettings())
    container.register_singleton("page_cache", lambda: PageCache())
    container.register_singleton("clipboard_manager", lambda: ClipboardManager())

    # ファクトリーを登録します。
    container.register_factory("pdf_handler", lambda: PDFDocumentHandler())

    # サービス ロケーターを設定します。
    ServiceLocator.set_container(container)

    logger.info("Dependency injection container configured")
    return container

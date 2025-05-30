"""コンポーネントとコントローラーのベースクラスです。"""

from abc import ABC, abstractmethod
from typing import Any

from ..logger import get_logger


class BaseComponent(ABC):
    """すべての UI コンポーネントのベースクラスです。"""

    def __init__(self, name: str = None):
        self._name = name or self.__class__.__name__
        self._logger = get_logger(f"{self.__module__}.{self._name}")
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """コンポーネントを初期化します。"""
        pass

    def cleanup(self) -> None:
        """コンポーネントのリソースをクリーンアップします。必要に応じてオーバーライドしてください。"""
        self._initialized = False
        self._logger.debug(f"{self._name} cleaned up")

    @property
    def is_initialized(self) -> bool:
        """コンポーネントが初期化されているかどうかを確認します。"""
        return self._initialized

    def _mark_initialized(self) -> None:
        """コンポーネントを初期化済みとしてマークします。"""
        self._initialized = True
        self._logger.debug(f"{self._name} initialized")


class BaseController(ABC):
    """すべてのコントローラーのベースクラスです。"""

    def __init__(self, name: str = None):
        self._name = name or self.__class__.__name__
        self._logger = get_logger(f"{self.__module__}.{self._name}")
        self._components: dict[str, Any] = {}
        self._initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """コントローラーを初期化します。"""
        pass

    def set_components(self, **components) -> None:
        """コンポーネントの依存関係を設定します。"""
        self._components.update(components)

    def get_component(self, name: str) -> Any | None:
        """名前でコンポーネントを取得します。"""
        return self._components.get(name)

    def cleanup(self) -> None:
        """コントローラーのリソースをクリーンアップします。必要に応じてオーバーライドしてください。"""
        self._components.clear()
        self._initialized = False
        self._logger.debug(f"{self._name} cleaned up")

    @property
    def is_initialized(self) -> bool:
        """コントローラーが初期化されているかどうかを確認します。"""
        return self._initialized

    def _mark_initialized(self) -> None:
        """コントローラーを初期化済みとしてマークします。"""
        self._initialized = True
        self._logger.debug(f"{self._name} initialized")

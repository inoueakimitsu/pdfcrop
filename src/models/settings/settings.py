"""PDFCrop アプリケーションの統合設定管理モジュールです。"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import QLocale

from ...exceptions import SettingsError


class SettingsRepository:
    """設定のディスクへの読み書きを処理するクラスです。"""

    def __init__(self, settings_file_path: str | None = None) -> None:
        """設定リポジトリを初期化します。

        Parameters
        ----------
        settings_file_path : str | None
            設定ファイルのパスです。None の場合はデフォルトを使用します。
        """
        if settings_file_path is None:
            from ...config import file_config

            settings_file_path = file_config.SETTINGS_FILE
        self._settings_file_path = Path(settings_file_path)
        self._ensure_settings_directory()

    def _ensure_settings_directory(self) -> None:
        """設定ディレクトリが存在することを確認します。"""
        self._settings_file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> dict[str, Any]:
        """ファイルから設定を読み込みます。

        Returns
        -------
        dict[str, Any]
            設定データを格納した辞書です。

        Raises
        ------
        SettingsError
            設定ファイルが読み込めない場合に発生します。
        """
        try:
            if self._settings_file_path.exists():
                with self._settings_file_path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                from ...config import DEFAULT_SETTINGS

                return DEFAULT_SETTINGS.copy()
        except Exception as e:
            raise SettingsError(f"設定ファイルの読み込みに失敗しました: {str(e)}", str(self._settings_file_path)) from e

    def save_settings(self, settings_data: dict[str, Any]) -> None:
        """設定をファイルに保存します。

        Parameters
        ----------
        settings_data : dict[str, Any]
            保存する設定データです。

        Raises
        ------
        SettingsError
            設定ファイルが保存できない場合に発生します。
        """
        try:
            with self._settings_file_path.open("w", encoding="utf-8") as f:
                json.dump(settings_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise SettingsError(f"設定ファイルの保存に失敗しました: {str(e)}", str(self._settings_file_path)) from e


class ApplicationSettings:
    """
    コンポーネント構成を使用したアプリケーション設定マネージャーです。

    このクラスは、ウィンドウ、ファイル、言語設定を含むすべてのアプリケーション設定を管理します。
    """

    _instance: Optional["ApplicationSettings"] = None

    def __init__(self, settings_file_path: str | None = None) -> None:
        """アプリケーション設定を初期化します。

        Parameters
        ----------
        settings_file_path : str | None
            設定ファイルのパスです。None の場合はデフォルトを使用します。
        """
        self._repository = SettingsRepository(settings_file_path) if settings_file_path else SettingsRepository()
        self._settings_data = self._repository.load_settings()

    def __new__(cls, settings_file_path: str | None = None) -> "ApplicationSettings":
        """後方互換性のためにシングルトンインスタンスを作成または返します。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls, settings_file_path: str | None = None) -> "ApplicationSettings":
        """シングルトンインスタンスを取得します。"""
        if cls._instance is None:
            cls._instance = cls(settings_file_path)
        return cls._instance

    def save_settings(self) -> None:
        """現在の設定をファイルに保存します。"""
        self._repository.save_settings(self._settings_data)

    # ウィンドウ設定メソッドです。
    def get_window_geometry(self) -> str:
        """ウィンドウジオメトリ文字列を取得します。"""
        return self._settings_data.get("window_geometry", "")

    def set_window_geometry(self, geometry: str) -> None:
        """ウィンドウジオメトリ文字列を設定します。"""
        self._settings_data["window_geometry"] = geometry

    # 言語設定メソッドです。
    def get_language(self) -> str:
        """現在の言語設定を取得します。"""
        lang = self._settings_data.get("language", "")
        if not lang:
            # システム言語を自動検出します。
            system_locale = QLocale.system().name()
            return system_locale if system_locale in ["en_US", "ja_JP", "zh_CN", "zh_TW"] else "ja_JP"
        return lang

    def set_language(self, language: str) -> None:
        """言語設定を設定します。"""
        self._settings_data["language"] = language

    def ensure_valid_language_setting(self) -> None:
        """言語設定が有効であることを確認します。"""
        from ...i18n import SUPPORTED_LANGUAGES

        current_lang = self.get_language()
        if current_lang not in SUPPORTED_LANGUAGES:
            # 無効な場合は日本語をデフォルトにします。
            self.set_language("ja_JP")

    # ファイル設定メソッドです。
    def get_last_file(self) -> str:
        """Get last opened file path."""
        return self._settings_data.get("last_file", "")

    def set_last_file(self, filepath: str) -> None:
        """Set last opened file path."""
        normalized_path = self._normalize_path(filepath)
        self._settings_data["last_file"] = normalized_path

    def get_file_settings(self, filepath: str) -> dict[str, Any]:
        """Get settings for a specific file."""
        from ...config import DEFAULT_FILE_SETTINGS

        normalized_path = self._normalize_path(filepath)
        if "recent_files" not in self._settings_data:
            self._settings_data["recent_files"] = {}

        if normalized_path not in self._settings_data["recent_files"]:
            self._settings_data["recent_files"][normalized_path] = DEFAULT_FILE_SETTINGS.copy()
        else:
            # すべてのデフォルトキーが存在することを確認します。
            for key, value in DEFAULT_FILE_SETTINGS.items():
                self._settings_data["recent_files"][normalized_path].setdefault(key, value)

        return self._settings_data["recent_files"][normalized_path]

    def update_file_settings(
        self,
        filepath: str,
        scroll_position: float,
        max_extract_pages: int,
    ) -> None:
        """Update settings for a specific file."""
        from ...config import DEFAULT_FILE_SETTINGS

        normalized_path = self._normalize_path(filepath)
        if "recent_files" not in self._settings_data:
            self._settings_data["recent_files"] = {}

        if normalized_path not in self._settings_data["recent_files"]:
            self._settings_data["recent_files"][normalized_path] = DEFAULT_FILE_SETTINGS.copy()

        file_settings = self._settings_data["recent_files"][normalized_path]
        file_settings["scroll_position"] = scroll_position
        file_settings["max_extract_pages"] = max_extract_pages
        file_settings["last_accessed"] = datetime.now().isoformat()
        self.set_last_file(normalized_path)

    def get_recent_files(self, limit: int = None) -> list[tuple[str, dict[str, Any]]]:
        """Get list of recent files sorted by last accessed time."""
        recent_files = []
        recent_files_data = self._settings_data.get("recent_files", {})

        for filepath, settings in recent_files_data.items():
            # 簡単な PDF ファイル検証（拡張子チェック）です。
            if filepath.lower().endswith(".pdf"):
                recent_files.append((filepath, settings))

        # last_accessed 時刻でソートします（最新のものが最初）。
        recent_files.sort(key=lambda x: x[1].get("last_accessed", ""), reverse=True)

        if limit is not None:
            recent_files = recent_files[:limit]

        return recent_files

    def remove_file_from_recent(self, filepath: str) -> None:
        """Remove a file from recent files list."""
        normalized_path = self._normalize_path(filepath)
        recent_files_data = self._settings_data.get("recent_files", {})

        if normalized_path in recent_files_data:
            del recent_files_data[normalized_path]

        # 削除されたファイルが last_file だった場合はクリアします。
        if self._settings_data.get("last_file") == normalized_path:
            self._settings_data["last_file"] = ""

    def clear_recent_files(self) -> None:
        """Clear all recent files history."""
        self._settings_data["recent_files"] = {}
        self._settings_data["last_file"] = ""

    def cleanup_missing_files(self) -> int:
        """Remove files that no longer exist from recent files list."""

        recent_files_data = self._settings_data.get("recent_files", {})
        missing_files = []

        for filepath in recent_files_data:
            if not os.path.exists(filepath) or not filepath.lower().endswith(".pdf"):
                missing_files.append(filepath)

        for filepath in missing_files:
            self.remove_file_from_recent(filepath)

        return len(missing_files)

    @staticmethod
    def _normalize_path(filepath: str | Path) -> str:
        """Normalize file path to avoid circular imports.

        Args:
            filepath: File path to normalize

        Returns:
            Normalized file path
        """
        return str(Path(filepath).resolve()).replace("\\", "/")

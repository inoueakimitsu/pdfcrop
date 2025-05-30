"""PDFCrop アプリケーションの設定定数を定義するモジュールです。

このモジュールは、アプリケーション全体で使用される設定定数を定義します。
設定は論理的なグループごとにクラスとしてまとめられています。
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final


@dataclass(frozen=True)
class WindowConfig:
    """ウィンドウに関連する設定定数です。

    Parameters
    ----------
    WIDTH: int
        ウィンドウの幅 (ピクセル) です。
    HEIGHT: int
        ウィンドウの高さ (ピクセル) です。
    DEFAULT_SIZE: str
        デフォルトのウィンドウサイズ ("幅x高さ" 形式) です。
    MIN_WIDTH: int
        ウィンドウの最小幅です。
    MIN_HEIGHT: int
        ウィンドウの最小高さです。

    Notes
    -----
    このクラスは、アプリケーションウィンドウのサイズや表示に関する
    設定定数を提供します。

    """

    WIDTH: Final[int] = 800
    HEIGHT: Final[int] = 600
    DEFAULT_SIZE: Final[str] = f"{WIDTH}x{HEIGHT}"
    MIN_WIDTH: Final[int] = 400
    MIN_HEIGHT: Final[int] = 300


@dataclass(frozen=True)
class PDFConfig:
    """PDF 操作に関連する設定定数です。

    Parameters
    ----------
    DEFAULT_ZOOM_SCALE: float
        デフォルトのズームスケールです。
    DEFAULT_MAX_EXTRACT_PAGES: int
        デフォルトの最大抽出ページ数です。
    TEMP_DIRECTORY: str
        一時ファイルを保存するディレクトリです。
    ZOOM_IN_FACTOR: float
        ズームイン倍率です。
    ZOOM_OUT_FACTOR: float
        ズームアウト倍率です。
    MIN_SELECTION_SIZE: int
        最小選択サイズです。

    Notes
    -----
    このクラスは、PDF ファイルの表示や操作に関する設定定数を提供します。

    """

    DEFAULT_ZOOM_SCALE: Final[float] = 1.0
    DEFAULT_MAX_EXTRACT_PAGES: Final[int] = 3
    ZOOM_IN_FACTOR: Final[float] = 1.1
    ZOOM_OUT_FACTOR: Final[float] = 1.1
    MIN_SELECTION_SIZE: Final[int] = 5

    TEMP_DIRECTORY: Final[str] = str(Path(os.getenv("TEMP", "temp")) / "PDFCrop" / "pdfs")
    TEMP_IMAGE_DIRECTORY: Final[str] = str(Path(os.getenv("TEMP", "temp")) / "PDFCrop" / "images")

    # サポートされているファイル拡張子です。
    SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".pdf",)


@dataclass(frozen=True)
class UIConfig:
    """ユーザー インターフェースに関連する設定定数です。

    Parameters
    ----------
    TOOLBAR_PADDING: int
        ツールバーの内部パディングです。
    TOOLBAR_SEPARATOR_PADDING: int
        ツールバーセパレーターのパディングです。
    MAX_PAGES_ENTRY_WIDTH: int
        最大ページ数入力フィールドの幅です。
    SCROLLBAR_WIDTH: int
        スクロールバーの幅です。
    PAGE_PADDING: int
        ページ間のパディングです。
    MENU_BUTTON_MIN_WIDTH: int
        メニューボタンの最小幅です。
    MAX_MENU_PATH_LENGTH: int
        メニューパスの最大長です。
    PATH_TRUNCATION_SUFFIX: str
        パス切り詰め時のサフィックスです。

    Notes
    -----
    このクラスは、UI コンポーネントのレイアウトや表示に関する
    設定定数を提供します。

    """

    TOOLBAR_PADDING: Final[int] = 2
    TOOLBAR_SEPARATOR_PADDING: Final[int] = 5
    MAX_PAGES_ENTRY_WIDTH: Final[int] = 3
    SCROLLBAR_WIDTH: Final[int] = 16
    PAGE_PADDING: Final[int] = 10
    MENU_BUTTON_MIN_WIDTH: Final[int] = 70
    MAX_MENU_PATH_LENGTH: Final[int] = 40
    PATH_TRUNCATION_SUFFIX: Final[str] = "..."


@dataclass(frozen=True)
class FileConfig:
    """ファイル操作に関連する設定定数です。

    Parameters
    ----------
    APP_DATA_DIR: str
        アプリケーションのデータディレクトリです。
    SETTINGS_FILE: str
        設定ファイルのパスです。
    DEFAULT_RECENT_FILES_LIMIT: int
        デフォルトの最近使用したファイル数の上限です。

    Notes
    -----
    このクラスは、設定ファイルやファイル操作に関する定数を提供します。

    """

    APP_DATA_DIR: Final[str] = str(Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "PDFCrop")
    SETTINGS_FILE: Final[str] = str(Path(APP_DATA_DIR) / "settings.json")
    DEFAULT_RECENT_FILES_LIMIT: Final[int] = 20


def _default_settings() -> dict:
    """デフォルト設定値を返します。"""
    return {
        "window_geometry": "",
        "recent_files": {},
        "last_file": "",
        "language": "",  # 言語設定を追加します。
    }


def _default_file_settings() -> dict:
    """ファイルごとのデフォルト設定値を返します。"""
    return {
        "scroll_position": 0.0,
        "last_accessed": "",
        "max_extract_pages": PDFConfig.DEFAULT_MAX_EXTRACT_PAGES,
    }


@dataclass(frozen=True)
class CacheConfig:
    """キャッシュに関連する設定定数です。

    Parameters
    ----------
    CACHE_DIRECTORY: str
        キャッシュファイルを保存するディレクトリです。
    MAX_CACHE_SIZE_GB: float
        キャッシュの最大サイズ (GB) です。
    HIGH_RES_SCALE_FACTOR: float
        高解像度キャッシュのスケールファクターです。
    PRELOAD_RANGE: int
        現在のページの前後何ページをプリロードするかです。
    PLACEHOLDER_COLOR: str
        プレースホルダーの色です。
    LOW_RES_SCALE_FACTOR: float
        低解像度プレースホルダーのスケールファクターです。

    Notes
    -----
    このクラスは、PDF ページのキャッシュに関する設定定数を提供します。

    """

    CACHE_DIRECTORY: Final[str] = str(Path(os.getenv("LOCALAPPDATA", "cache")) / "PDFCrop" / "cache")
    MAX_CACHE_SIZE_GB: Final[float] = 1.0
    HIGH_RES_SCALE_FACTOR: Final[float] = 2.0
    PRELOAD_RANGE: Final[int] = 2
    PLACEHOLDER_COLOR: Final[str] = "#f0f0f0"
    LOW_RES_SCALE_FACTOR: Final[float] = 0.2


# 各設定クラスのインスタンスを作成します。
window_config = WindowConfig()
pdf_config = PDFConfig()
ui_config = UIConfig()
file_config = FileConfig()
cache_config = CacheConfig()

# グローバル設定の定数です。
DEFAULT_SETTINGS = _default_settings()
DEFAULT_FILE_SETTINGS = _default_file_settings()


@dataclass(frozen=True)
class LoggingConfig:
    """ロギングに関連する設定定数です。"""

    LOG_DIRECTORY: Final[str] = str(Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "PDFCrop" / "logs")
    LOG_FILE: Final[str] = str(Path(LOG_DIRECTORY) / "app.log")


# ロギング設定も含めてインスタンスを作成します。
logging_config = LoggingConfig()


@dataclass(frozen=True)
class AppConfig:
    """アプリケーション全般の設定定数です。

    Parameters
    ----------
    APP_NAME: str
        アプリケーション名です。
    LOAD_DELAY_MS: int
        読み込み遅延時間 (ミリ秒) です。
    DEBOUNCE_DELAY_MS: int
        デバウンス遅延時間 (ミリ秒) です。

    Notes
    -----
    このクラスは、アプリケーション全体で使用される定数を提供します。

    """

    APP_NAME: Final[str] = "PDFCrop"
    LOAD_DELAY_MS: Final[int] = 100
    DEBOUNCE_DELAY_MS: Final[int] = 100


# アプリケーション設定のインスタンスを作成します。
app_config = AppConfig()

# エラーメッセージの定数です。
ERROR_FILE_NOT_FOUND: Final[str] = "File not found: {filepath}"
ERROR_INVALID_PDF: Final[str] = "Invalid PDF file: {filepath}"
ERROR_LOAD_FAILED: Final[str] = "Failed to load file: {filepath}"
ERROR_SAVE_FAILED: Final[str] = "Failed to save settings"

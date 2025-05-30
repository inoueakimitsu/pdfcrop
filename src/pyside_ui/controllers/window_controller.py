"""PDFCrop PySide6 ベースのウィンドウ管理を担当するモジュールです。

このモジュールは、メインウィンドウの設定、ジオメトリの管理、タイトル設定などを担当します。
"""

import json

from PySide6.QtWidgets import QMainWindow

from ...config import window_config
from ...logger import get_logger

logger = get_logger(__name__)


class WindowController:
    """
    ウィンドウの管理を担当するコントローラーです。

    このクラスは、ウィンドウのジオメトリ、タイトル、設定の復元などを管理します。

    Attributes
    ----------
    main_window: QMainWindow
        管理対象のメインウィンドウです。
    settings: ApplicationSettings
        アプリケーションの設定です。
    """

    def __init__(self, main_window: QMainWindow, settings):
        """
        WindowController を初期化します。

        Parameters
        ----------
        main_window: QMainWindow
            管理対象のメインウィンドウです。
        settings: ApplicationSettings
            アプリケーションの設定です。
        """
        self.main_window = main_window
        self.settings = settings

    def setup_window(self) -> None:
        """
        ウィンドウの設定を復元します。
        """
        self._set_window_title()
        self._restore_window_geometry()

    def _set_window_title(self, filepath: str | None = None) -> None:
        """
        ウィンドウ タイトルを設定します。

        Parameters
        ----------
        filepath: str | None
            表示するファイル パスです。
        """
        base_title = "PDFCrop"
        if filepath:
            self.main_window.setWindowTitle(f"{filepath} - {base_title}")
        else:
            self.main_window.setWindowTitle(base_title)

    def _restore_window_geometry(self) -> None:
        """
        ウィンドウのジオメトリを設定します。
        """
        geometry_str = self.settings.get_window_geometry()
        if geometry_str:
            try:
                # tkinter と PySide6 でのジオメトリ形式の違いを処理します。
                if "x" in geometry_str and "+" in geometry_str:
                    # tkinter 形式 ("700x780+100+100") から PySide6 形式に変換します。
                    size, position = geometry_str.split("+", 1)
                    width, height = map(int, size.split("x"))
                    x, y = map(int, ("+" + position).split("+")[1:3])
                    self.main_window.setGeometry(x, y, width, height)
                else:
                    # JSON 形式として保存されている場合の処理です。
                    geometry = json.loads(geometry_str)

                    # 保存されたジオメトリの情報を取得します。
                    x = geometry.get("x", 0)
                    y = geometry.get("y", 0)
                    width = geometry.get("width", window_config.WIDTH)
                    height = geometry.get("height", window_config.HEIGHT)

                    # ウィンドウ位置を設定します (タイトル バーを含む全体ウィンドウ位置)。
                    self.main_window.move(x, y)
                    self.main_window.resize(width, height)

            except (ValueError, json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Invalid window geometry: {e}")
                self.main_window.resize(window_config.WIDTH, window_config.HEIGHT)
        else:
            # 設定がない場合はデフォルト値を使用します。
            self.main_window.resize(window_config.WIDTH, window_config.HEIGHT)

    def save_window_geometry(self) -> None:
        """
        ウィンドウのジオメトリを保存します。
        """
        # ウィンドウ位置を保存します。
        frame_geom = self.main_window.frameGeometry()
        geometry = {
            "x": frame_geom.x(),
            "y": frame_geom.y(),
            "width": self.main_window.width(),
            "height": self.main_window.height(),
        }
        self.settings.set_window_geometry(json.dumps(geometry))

    def set_title_with_file(self, filepath: str) -> None:
        """
        ファイルパスを含むタイトルを設定します。

        Parameters
        ----------
        filepath: str
            表示するファイルパスです。
        """
        self._set_window_title(filepath)

    def reset_title(self) -> None:
        """
        タイトルをデフォルトに戻します。
        """
        self._set_window_title()

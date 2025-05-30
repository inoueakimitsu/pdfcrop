"""PDFCrop PySide6 ベースのメインウィンドウを実装するモジュールです。

このモジュールは、アプリケーションのメインウィンドウと、
ドラッグ & ドロップ機能を提供します。
"""

import os

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from ..config import window_config
from ..logger import get_logger
from ..utils import resource_path

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    アプリケーションのメインウィンドウです。

    このクラスは、アプリケーションのメインウィンドウとして機能し、
    ドラッグ & ドロップのサポートや基本的なウィンドウ管理を提供します。

    Attributes
    ----------
    pdf_dropped : Signal(str)
        PDF ファイルがドロップされた時に発行されるシグナルです。
    """

    # PDF ドロップシグナルです。
    pdf_dropped = Signal(str)

    def __init__(self):
        """
        MainWindow を初期化します。
        """
        super().__init__()

        # ウィンドウのデフォルト設定を行います。
        self.setWindowTitle("PDFCrop")
        self.resize(window_config.WIDTH, window_config.HEIGHT)

        # ウィンドウアイコンの設定を行います。
        icon_path = resource_path("resources", "icons", "PDFCrop_icon.ico")
        logger.info(f"Icon path: {icon_path}")
        logger.info(f"Icon exists: {os.path.exists(icon_path)}")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            logger.info("Window icon set successfully")
        else:
            logger.warning(f"Icon file not found at: {icon_path}")

        # セントラルウィジェットを設定します。
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # メインレイアウトを設定します。
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ステータスバーの初期化を行います。
        self.statusBar().showMessage("")

        # ドラッグ & ドロップの有効化を行います。
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        ドラッグイベントの処理を行います。

        Parameters
        ----------
        event : QDragEnterEvent
            ドラッグイベントです。
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        ドロップイベントの処理を行います。

        Parameters
        ----------
        event : QDropEvent
            ドロップイベントです。
        """
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".pdf"):
                # PDF ドロップシグナルを発行します。
                self.pdf_dropped.emit(file_path)
                break
        event.acceptProposedAction()

    def closeEvent(self, event):
        """
        ウィンドウを閉じる際のイベント処理を行います。

        Parameters
        ----------
        event : QCloseEvent
            クローズイベントです。
        """
        # アプリケーションのインスタンスへの参照を確認します。
        app = self.property("app")
        if app and hasattr(app, "_on_closing"):
            logger.info("closeEvent: calling app._on_closing from MainWindow")
            app._on_closing(event)
        else:
            logger.warning("closeEvent: app instance not found or missing _on_closing method")
            super().closeEvent(event)

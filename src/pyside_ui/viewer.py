"""PDFCrop PySide6 ベースの PDF ビューアを実装するモジュールです。

このモジュールは、PDF の表示、ナビゲーション、ズーム機能を統合した
PDF ビューアコンポーネントを提供します。
"""

import time
from pathlib import Path

import fitz
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QScrollBar, QVBoxLayout, QWidget

import src.i18n as i18n_module

from ..config import pdf_config
from ..exceptions import PDFDisplayError, PDFEmptyError, PDFFileNotFoundError
from ..logger import get_logger
from .canvas import PDFGraphicsView
from .services.clipboard_manager import ClipboardManager

logger = get_logger(__name__)


class PDFViewer(QWidget):
    """
    PDF ビューアコンポーネントです。

    このクラスは、PDF の表示、ナビゲーション、ズーム機能を
    統合したビューアコンポーネントを提供します。

    Signals
    -------
    visible_page_changed : Signal(int)
        表示中のページが変更されたときに発行されるシグナルです。
    zoom_changed : Signal(float)
        ズームスケールが変更されたときに発行されるシグナルです。

    Attributes
    ----------
    view : PDFGraphicsView
        PDF を表示するグラフィックスビューです。
    current_document : Optional[fitz.Document]
        現在開いている PDF ドキュメントです。
    """

    # シグナル定義です。
    visible_page_changed = Signal(int)
    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        """
        PDF ビューアを初期化します。

        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェットです。
        """
        super().__init__(parent)

        # レイアウトを設定します。
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # GraphicsView を作成します。
        self.view = PDFGraphicsView(self)

        # スクロール バーを設定します。
        self.scrollbar = QScrollBar(Qt.Orientation.Vertical, self)
        self.view.setVerticalScrollBar(self.scrollbar)
        # スクロールバーのシグナルを直接接続します。
        self.scrollbar.valueChanged.connect(self.view.update_visible_pages)

        # レイアウトに追加します。
        layout.addWidget(self.view)

        # 現在のドキュメントを初期化します。
        self.current_document = None

        # アプリケーションへの参照です。
        # 循環参照を避けるために Any 型で定義します。
        from typing import Any

        self.app: Any = None

        # シグナルを接続します。
        self.view.visible_page_changed.connect(self._on_visible_page_changed)
        self.view.zoom_changed.connect(self._on_zoom_changed)

    def display_pdf_document(
        self,
        document_path: str,
        fit_to_width: bool = False,
        target_width: int | None = None,
        scroll_position: float = 0.0,
    ) -> None:
        """
        PDF ドキュメントを表示します。

        Parameters
        ----------
        document_path : str
            PDF ファイルのパスです。
        fit_to_width : bool
            幅に合わせてズームするかどうかです。
        target_width : int
            ズーム時の目標幅です。
        scroll_position : float
            スクロール位置 (0.0-1.0) です。

        Raises
        ------
        PDFFileNotFoundError
            PDF ファイルが見つからない場合の処理です。
        PDFEmptyError
            PDF にページがない場合の処理です。
        PDFDisplayError
            PDF 表示中にエラーが発生した場合の処理です。
        """
        try:
            # 既存のドキュメントを閉じます。
            if self.current_document:
                self.current_document.close()

            # 新しいドキュメントを開きます。
            self.current_document = fitz.open(document_path)
            if not self.current_document.page_count:
                raise PDFEmptyError(document_path)

            # スケールファクターを設定します。
            if fit_to_width and target_width:
                first_page = self.current_document.load_page(0)
                scale_factor = self.view.calculate_scale_for_width(first_page, target_width)
                self.view.set_zoom_scale(scale_factor)

            # ドキュメントをビューに設定します。
            self.view.set_document(self.current_document)

            # スクロール位置を設定します。
            if scroll_position > 0:
                max_val = self.view.verticalScrollBar().maximum()
                self.view.verticalScrollBar().setValue(int(scroll_position * max_val))

        except (PDFEmptyError, PDFFileNotFoundError):
            raise
        except Exception as e:
            raise PDFDisplayError(f"PDF 表示中にエラーが発生しました: {str(e)}", document_path) from e

    def calculate_visible_page(self) -> int:
        """
        現在表示中のページを特定します。

        Returns
        -------
        int
            現在表示中のページ番号 (0 ベース) です。
        """
        return self.view.calculate_visible_page()

    def get_current_state(self) -> tuple[float, float]:
        """
        現在の表示状態を取得します。

        Returns
        -------
        Tuple[float, float]
            スクロール位置とズーム スケールのタプルです。
        """
        # 垂直スクロール バーの位置を 0.0-1.0 の範囲で計算します。
        vbar = self.view.verticalScrollBar()
        scroll_position = vbar.value() / vbar.maximum() if vbar.maximum() > 0 else 0.0
        return scroll_position, self.view.scale_factor

    def _on_visible_page_changed(self, page_num: int) -> None:
        """
        表示ページが変更されたときに処理を行います。

        Parameters
        ----------
        page_num: int
            新しい表示ページ番号です。
        """
        # シグナルを転送します。
        self.visible_page_changed.emit(page_num)

    def _on_zoom_changed(self, scale_factor: float) -> None:
        """
        ズーム スケールが変更されたときに処理を行います。

        Parameters
        ----------
        scale_factor: float
            新しいズーム スケールです。
        """
        # シグナルを転送します。
        self.zoom_changed.emit(scale_factor)

    def capture_visible_area(self, rect: QRect) -> None:
        """
        表示領域の指定部分をキャプチャします。

        Parameters
        ----------
        rect : QRect
            キャプチャする領域です。
        """
        try:
            # 現在のドラッグモードを保存します。
            original_drag_mode = self.view.dragMode()

            # 一時的にラバーバンドを無効化します（選択矩形を非表示にします）。
            self.view.setDragMode(PDFGraphicsView.DragMode.NoDrag)

            # スクリーンキャプチャを実行します（少し遅延を入れて選択矩形が消えるのを待ちます）。
            QApplication.processEvents()
            screen = self.screen()
            pixmap = None

            if screen:
                global_rect = QRect(self.mapToGlobal(rect.topLeft()), self.mapToGlobal(rect.bottomRight()))
                pixmap = screen.grabWindow(
                    0, global_rect.x(), global_rect.y(), global_rect.width(), global_rect.height()
                )

            # ドラッグモードを元に戻します。
            self.view.setDragMode(original_drag_mode)

            if pixmap and not pixmap.isNull():
                # 一時ディレクトリを作成します。
                Path(pdf_config.TEMP_IMAGE_DIRECTORY).mkdir(parents=True, exist_ok=True)

                # 画像を保存します。
                filepath = Path(pdf_config.TEMP_IMAGE_DIRECTORY) / f"capture-{int(time.time() * 1000)}.png"
                pixmap.save(str(filepath))

                # クリップボードにコピーします。
                clipboard_manager = ClipboardManager()
                clipboard_manager.copy_image_to_clipboard(str(filepath))

                # ステータスメッセージを更新します。
                app = getattr(self, "app", None)
                if app and hasattr(app, "set_status_message"):
                    app.set_status_message(i18n_module._("Captured screenshot to clipboard"))
        except Exception as e:
            logger.exception(f"スクリーンキャプチャ中にエラーが発生しました: {e}")
            QMessageBox.critical(self, i18n_module._("Error"), str(e))

    def copy_current_pages(self) -> None:
        """
        現在表示中のページをクリップボードにコピーします。
        """
        app = getattr(self, "app", None)
        if app and hasattr(app, "copy_current_pages"):
            app.copy_current_pages()

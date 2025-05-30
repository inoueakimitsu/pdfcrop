"""PDFCrop PySide6 ベースのPDF操作コントローラーです。

このモジュールは、PDF操作に関連するビジネスロジックを管理します。
"""

import os
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox

import src.i18n as i18n_module

from ...config import pdf_config
from ...exceptions import (
    ClipboardError,
    PDFDisplayError,
    PDFEmptyError,
    PDFFileNotFoundError,
    PDFProcessingError,
)
from ...logger import get_logger
from ..services.clipboard_manager import ClipboardManager
from ..services.pdf_handler import PDFDocumentHandler

logger = get_logger(__name__)


class PDFController:
    """
    PDF操作を管理するコントローラーです。

    このクラスは、PDF読み込み、ページコピー、ファイル選択などのPDF関連操作を管理します。

    Attributes
    ----------
    pdf_handler : PDFDocumentHandler
        PDF操作のハンドラーです。
    clipboard_manager : ClipboardManager
        クリップボード管理です。
    settings : ApplicationSettings
        アプリケーション設定です。
    """

    def __init__(self, settings):
        """
        PDFController を初期化します。

        Parameters
        ----------
        settings: ApplicationSettings
            アプリケーション設定です。
        """
        self.pdf_handler = PDFDocumentHandler()
        self.clipboard_manager = ClipboardManager()
        self.settings = settings

        # 依存するコンポーネントへの参照（後で設定）です。
        self.main_window = None
        self.pdf_viewer = None
        self.toolbar = None
        self.window_controller = None
        self.menu_manager = None

    def set_components(self, main_window, pdf_viewer, toolbar, window_controller, menu_manager):
        """
        依存するコンポーネントを設定します。

        Parameters
        ----------
        main_window: QMainWindow
            メインウィンドウです。
        pdf_viewer: PDFViewer
            PDFビューアです。
        toolbar: ApplicationToolbar
            ツールバーです。
        window_controller: WindowController
            ウィンドウコントローラーです。
        menu_manager: MenuManager
            メニューマネージャーです。
        """
        self.main_window = main_window
        self.pdf_viewer = pdf_viewer
        self.toolbar = toolbar
        self.window_controller = window_controller
        self.menu_manager = menu_manager

    def load_initial_pdf(self, pdf_file: str | None = None) -> None:
        """
        初期PDF ファイルを読み込みます。

        Parameters
        ----------
        pdf_file: str | None
            読み込むPDFファイルのパスです。
        """
        if pdf_file:
            # コマンドライン引数で指定された PDF を読み込みます。
            QTimer.singleShot(100, lambda: self.load_pdf(pdf_file))
        else:
            # 前回開いていた PDF があれば読み込みます。
            last_file = self.settings.get_last_file()
            if last_file and os.path.exists(last_file):
                QTimer.singleShot(100, lambda: self.load_pdf(last_file))
            else:
                # ファイル選択ダイアログを表示します。
                QTimer.singleShot(100, self.show_file_dialog)

    def show_file_dialog(self) -> None:
        """
        ファイル選択ダイアログを表示します。
        """
        if not self.main_window:
            return

        filepath, file_filter = QFileDialog.getOpenFileName(
            self.main_window, i18n_module._("Open PDF File"), "", i18n_module._("PDF files (*.pdf);;All files (*.*)")
        )

        if filepath:
            self.load_pdf(filepath)
        else:
            # ファイルが選択されなかった場合はタイトルを初期化します。
            if self.window_controller:
                self.window_controller.reset_title()

    def load_pdf(self, filepath: str | None) -> None:
        """
        PDF ファイルを読み込んで表示します。

        Parameters
        ----------
        filepath: str | None
            読み込む PDF ファイルのパスです。
        """
        if not filepath or not self.pdf_viewer or not self.toolbar:
            return

        # 文字列型に変換します（型チェックのためです）。
        filepath_str = str(filepath)

        try:
            # 現在の PDF の設定を保存します。
            if self.pdf_handler.current_document_path:
                current_state = self.pdf_viewer.get_current_state()
                max_pages = self.toolbar.get_max_pages_value()
                self.settings.update_file_settings(
                    self.pdf_handler.current_document_path,
                    current_state[0],
                    max_pages,
                )

            # PDF ファイルを開きます。
            self.pdf_handler.open_document(filepath_str)

            # ファイルの設定を取得します。
            file_settings = self.settings.get_file_settings(filepath_str)
            scroll_position = file_settings.get("scroll_position", 0.0)
            max_pages_setting = file_settings.get(
                "max_extract_pages",
                pdf_config.DEFAULT_MAX_EXTRACT_PAGES,
            )
            self.toolbar.set_max_pages_value(max_pages_setting)

            # PDF を表示します。
            target_width = self.pdf_viewer.width()
            self.pdf_viewer.display_pdf_document(
                filepath_str,
                fit_to_width=True,
                target_width=target_width,
                scroll_position=scroll_position,
            )

            # タイトルをファイル パスで更新します。
            if self.window_controller:
                self.window_controller.set_title_with_file(filepath_str)

            # 最後に開いたファイルとして設定を更新します。
            self.settings.save_settings()

            # メニューの最近開いたファイルリストを更新します
            if self.menu_manager and hasattr(self.menu_manager, "update_recent_files_menu"):
                self.menu_manager.update_recent_files_menu()

        except (PDFFileNotFoundError, PDFEmptyError, PDFDisplayError) as e:
            if self.main_window:
                QMessageBox.critical(self.main_window, i18n_module._("Error"), str(e))
            else:
                logger.error(f"PDF loading error: {e}")

    def copy_current_pages(self) -> None:
        """
        現在のページとその周辺をクリップボードにコピーします。
        """
        if not all([self.toolbar, self.pdf_viewer, self.pdf_handler, self.clipboard_manager]):
            return

        try:
            # 最大ページ数を取得します。
            max_pages = self.toolbar.get_max_pages_value()

            # 現在のページを取得します。
            current_page = self.pdf_viewer.calculate_visible_page()

            # ページ範囲を計算します。
            page_range = self.pdf_handler.calculate_page_range(current_page, max_pages)

            # ページを抽出します。
            save_path = self.pdf_handler.extract_page_range(*page_range)

            # クリップボードにコピーします。
            self.clipboard_manager.copy_file_to_clipboard(save_path)

            # ステータス メッセージを更新します。
            start_page, end_page = page_range
            if self.main_window:
                self.main_window.statusBar().showMessage(
                    i18n_module._("Copied pages {start} to {end}").format(start=start_page + 1, end=end_page)
                )

            # 設定を保存します。
            if self.pdf_handler.current_document_path:
                current_state = self.pdf_viewer.get_current_state()
                self.settings.update_file_settings(
                    self.pdf_handler.current_document_path,
                    current_state[0],
                    max_pages,
                )
                self.settings.save_settings()

        except (PDFFileNotFoundError, PDFProcessingError, ClipboardError) as e:
            if self.main_window:
                QMessageBox.critical(self.main_window, i18n_module._("PDF Copy Error"), str(e))
            else:
                logger.error(f"PDF copy error: {e}")

    def on_max_pages_changed(self, value: int) -> None:
        """
        最大ページ数が変更された時の処理を行います。

        Parameters
        ----------
        value: int
            新しい最大ページ数です。
        """
        # 現在の PDF 設定を更新します。
        if self.pdf_handler and self.pdf_handler.current_document_path:
            if self.pdf_viewer:
                current_state = self.pdf_viewer.get_current_state()
                self.settings.update_file_settings(self.pdf_handler.current_document_path, current_state[0], value)
                self.settings.save_settings()

    def cleanup(self) -> None:
        """
        PDF関連のリソースをクリーンアップします。
        """
        # 一時ファイルを削除します。
        if self.pdf_handler:
            self.pdf_handler.cleanup_temp_files()

        # キャプチャした画像ファイルを削除します。
        try:
            temp_dir = Path(pdf_config.TEMP_IMAGE_DIRECTORY)
            if temp_dir.exists():
                for image_file in temp_dir.glob("capture-*.png"):
                    if image_file.is_file():
                        image_file.unlink()
        except Exception as e:
            logger.exception("画像一時ファイルのクリーンアップ中にエラーが発生しました: %s", e)
            if self.main_window:
                QMessageBox.critical(self.main_window, i18n_module._("Error"), str(e))
            else:
                logger.error(f"Cleanup error: {e}")

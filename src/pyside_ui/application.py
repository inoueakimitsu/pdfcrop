"""PDFCrop PySide6 ベースのアプリケーションのメインモジュールです。

このモジュールは、PySide6 ベースのアプリケーションのメインクラスを提供し、
すべてのコンポーネントを統合して動作を制御します。
"""

import platform
import subprocess
import sys

from PySide6.QtCore import QObject
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QMessageBox

# i18n モジュールへの参照です。
import src.i18n as i18n_module

from ..i18n import set_language
from ..logger import get_logger
from ..utils import authors_file_path
from .controllers.pdf_controller import PDFController
from .controllers.window_controller import WindowController
from .main_window import MainWindow
from .menu_manager import MenuManager
from .toolbar import ApplicationToolbar
from .viewer import PDFViewer

logger = get_logger(__name__)


class PDFViewerApplication(QObject):
    """
    PySide6 ベースの PDF ビューアアプリケーションのメインクラスです。

    このクラスは、アプリケーションの各コンポーネントを統合し、
    イベントハンドラーを設定します。

    Attributes
    ----------
    app : QApplication
        Qt アプリケーションのインスタンスです。
    settings : ApplicationSettings
        アプリケーションの設定です。
    main_window : MainWindow
        アプリケーションのメインウィンドウです。
    pdf_controller : PDFController
        PDF操作のコントローラーです。
    window_controller : WindowController
        ウィンドウ管理のコントローラーです。
    toolbar : ApplicationToolbar
        アプリケーションのツールバーです。
    pdf_viewer : PDFViewer
        PDF ビューアのコンポーネントです。

    Notes
    -----
    このクラスは、アプリケーションの起動から終了までの
    ライフサイクルを管理します。
    """

    def __init__(self, pdf_file: str | None = None) -> None:
        """
        PDFViewerApplication を初期化します。
        """
        super().__init__()

        # 設定を初期化します。
        from ..models.settings import ApplicationSettings

        self.settings = ApplicationSettings()

        # Qt アプリケーションのインスタンスを作成します。
        self.app = QApplication.instance() or QApplication(sys.argv)

        # アプリケーションの設定を行います。
        self.app.setApplicationName("PDFCrop")
        self.app.setOrganizationName("PDFCrop")
        self.pdf_file = pdf_file

        # 国際化の設定を行います。
        self._load_translation()

        # コントローラーと UI コンポーネントを初期化します (run() で初期化します)。
        self.main_window = None
        self.pdf_controller = None
        self.window_controller = None
        self.menu_manager = None
        self.toolbar = None
        self.pdf_viewer = None

        # ショートカットを保持する属性を初期化します。
        self.copy_shortcut = None

    def _load_translation(self) -> None:
        """
        言語設定が有効であることを確認し、翻訳を読み込みます。
        """
        self.settings.ensure_valid_language_setting()
        locale_name = self.settings.get_language()
        set_language(locale_name)  # from src.i18n
        logger.info(f"Language set to: {locale_name}")

    def run(self) -> int:
        """
        アプリケーションを実行します。

        Returns
        -------
        int: アプリケーションの終了コードです。

        Notes
        -----
        このメソッドは、メイン ウィンドウを作成し、
        すべてのコンポーネントを初期化して、
        アプリケーションのメイン ループを開始します。
        """
        # コンポーネントを初期化します。
        self._initialize_components()

        # コンポーネント間の関係を設定します。
        self._setup_component_relationships()

        # ウィンドウの設定を行います。
        self.window_controller.setup_window()

        # イベント ハンドラーを設定します。
        self._setup_event_handlers()

        # 初期 PDF をロードします。
        self.pdf_controller.load_initial_pdf(self.pdf_file)

        # ウィンドウを表示します。
        self.main_window.show()

        # メイン イベント ループを開始します。
        return self.app.exec()

    def _initialize_components(self) -> None:
        """
        アプリケーションのコンポーネントを初期化します。
        """
        # メイン ウィンドウを作成します。
        self.main_window = MainWindow()

        # ウィンドウにアプリケーション インスタンスへの参照を設定します。
        self.main_window.setProperty("app", self)

        # コントローラーを初期化します。
        self.pdf_controller = PDFController(self.settings)
        self.window_controller = WindowController(self.main_window, self.settings)

        # メニュー マネージャーを初期化します。
        self.menu_manager = MenuManager(self.main_window)
        self.menu_manager.connect_file_actions(self.pdf_controller.show_file_dialog, self._on_closing)

        # ツール バーを初期化します。
        self.toolbar = ApplicationToolbar(self.main_window)
        self.main_window.addToolBarBreak()  # メニューバーの下に新しい行を作成します。
        self.main_window.addToolBar(self.toolbar)

        # PDF ビューアを初期化します。
        self.pdf_viewer = PDFViewer(self.main_window)
        self.main_window.setCentralWidget(self.pdf_viewer)

        # ステータス バーを初期化します。
        self.main_window.statusBar().showMessage(
            i18n_module._(
                "Right-click or Ctrl+Left-click or Ctrl+C: Copy current and previous pages | "
                "Right-drag or Shift+Left-drag: Copy selected area"
            )
        )

    def _setup_component_relationships(self) -> None:
        """
        コンポーネント間の関係を設定します。
        """
        # PDFコントローラーに依存コンポーネントを設定
        self.pdf_controller.set_components(
            self.main_window, self.pdf_viewer, self.toolbar, self.window_controller, self.menu_manager
        )

        # メニューマネージャーにPDFコントローラーを設定
        self.menu_manager.set_pdf_controller(self.pdf_controller)

        # ビューアにアプリへの参照を設定します。
        if self.pdf_viewer:
            self.pdf_viewer.app = self

        # ウィンドウにアプリケーション インスタンスへの参照を設定します。
        self.main_window.setProperty("app", self)

    def _setup_event_handlers(self) -> None:
        """
        イベント ハンドラーを設定します。
        """
        if self.main_window is None:
            return

        # メイン ウィンドウからの PDF ドロップ シグナルを接続します。
        self.main_window.pdf_dropped.connect(self.pdf_controller.load_pdf)

        # ウィンドウ リサイズ イベントを接続します。
        self.main_window.resizeEvent = self._on_main_window_resize

        # ショートカット キーを設定します。
        self.copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self.main_window)
        self.copy_shortcut.activated.connect(self.copy_current_pages)

        # ツール バーの値変更シグナルを接続します。
        if self.toolbar is not None and hasattr(self.toolbar, "max_pages_changed"):
            self.toolbar.max_pages_changed.connect(self.pdf_controller.on_max_pages_changed)

    def _on_main_window_resize(self, event) -> None:
        """
        ウィンドウのリサイズ イベントを処理します。

        Parameters
        ----------
        event: QResizeEvent
            リサイズ イベントです。
        """
        if self.main_window is None:
            return

        # 元のリサイズ イベントを処理します。
        from PySide6.QtWidgets import QMainWindow

        QMainWindow.resizeEvent(self.main_window, event)

        # ウィンドウ サイズ変更時に PDF を再表示します。
        if (
            self.pdf_controller
            and self.pdf_viewer
            and self.pdf_controller.pdf_handler
            and self.pdf_controller.pdf_handler.current_document_path
        ):
            target_width = self.pdf_viewer.width()
            self.pdf_viewer.display_pdf_document(
                self.pdf_controller.pdf_handler.current_document_path,
                fit_to_width=True,
                target_width=target_width,
                scroll_position=self.pdf_viewer.get_current_state()[0],
            )

    def set_status_message(self, message: str) -> None:
        """
        ステータス バーにメッセージを表示します。

        Parameters
        ----------
        message: str
            表示するメッセージです。
        """
        if self.main_window:
            self.main_window.statusBar().showMessage(message)

    def copy_current_pages(self) -> None:
        """
        現在のページとその周辺をクリップボードにコピーします。
        """
        if self.pdf_controller:
            self.pdf_controller.copy_current_pages()

    def _show_authors(self) -> None:
        """
        AUTHORS ファイルをデフォルトのテキスト エディターで開きます。
        """
        try:
            authors_path = authors_file_path()

            if platform.system() == "Windows":
                subprocess.run(["notepad.exe", authors_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", authors_path])
            else:  # Linux
                subprocess.run(["xdg-open", authors_path])
        except Exception as e:
            if self.main_window is not None:
                QMessageBox.critical(self.main_window, i18n_module._("Error"), str(e))
            else:
                logger.error(f"Error showing authors: {e}")

    def _on_closing(self, event=None) -> None:
        """
        ウィンドウが閉じられる時の処理を行います。

        Parameters
        ----------
        event: QCloseEvent, optional
            ウィンドウのクローズ イベントです。メニューからの呼び出しの場合は None です。
        """
        logger.info("_on_closing method called - Closing window")

        # 現在の設定を保存します。
        if (
            self.pdf_viewer is not None
            and self.pdf_controller is not None
            and self.pdf_controller.pdf_handler is not None
            and self.toolbar is not None
            and hasattr(self.pdf_viewer, "current_document")
            and self.pdf_viewer.current_document
            and self.pdf_controller.pdf_handler.current_document_path
        ):
            current_state = self.pdf_viewer.get_current_state()
            max_pages = self.toolbar.get_max_pages_value()
            self.settings.update_file_settings(
                self.pdf_controller.pdf_handler.current_document_path,
                current_state[0],
                max_pages,
            )

        # ウィンドウのジオメトリを保存します。
        if self.window_controller:
            self.window_controller.save_window_geometry()

        self.settings.save_settings()

        # PDFコントローラーのクリーンアップを実行します。
        if self.pdf_controller:
            self.pdf_controller.cleanup()

        # イベントがある場合（closeEvent から呼ばれた場合）は処理を続行します。
        if event is not None and hasattr(event, "accept"):
            event.accept()
        else:
            # メニューから呼ばれた場合はアプリケーションを終了します。
            self.app.quit()

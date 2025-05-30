"""PDFCrop PySide6 ベースのメニュー管理を実装するモジュールです。

このモジュールは、アプリケーションのメニューバーと全てのメニュー項目を管理します。
"""

import os
import platform
import subprocess

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QMainWindow, QMenu, QMessageBox, QToolBar, QToolButton

import src.i18n as i18n_module

from ..config import file_config, ui_config
from ..logger import get_logger
from ..utils import authors_file_path

logger = get_logger(__name__)


class MenuManager(QObject):
    """
    アプリケーションのメニュー管理クラスです。

    このクラスは、アプリケーションのメニューバーとそのサブメニューを作成し管理します。

    Signals
    -------
    language_changed : Signal(str)
        言語が変更されたときに発行されるシグナルです。

    Attributes
    ----------
    menubar : QMenuBar
        メニューバーのインスタンスです。
    settings_menu : QMenu
        設定メニューのインスタンスです。
    language_menu : QMenu
        言語サブメニューのインスタンスです。
    recent_file_actions : list[QAction]
        最近開いたファイルのアクションのリストです。
    """

    # シグナル定義です。
    language_changed = Signal(str)

    def __init__(self, main_window: QMainWindow):
        """
        MenuManager を初期化します。

        Parameters
        ----------
        main_window : QMainWindow
            メインウィンドウのインスタンスです。
        """
        super().__init__()
        self.main_window = main_window
        # アプリケーションのインスタンスから設定を取得します。
        self.settings = main_window.property("app").settings

        # 標準メニューバーを隠します。
        main_window.menuBar().hide()

        # 移動可能なツールバーメニューを作成します。
        self.menu_toolbar = QToolBar(i18n_module._("Menu"), main_window)
        self.menu_toolbar.setMovable(True)
        main_window.addToolBar(self.menu_toolbar)

        # PDFコントローラーの参照です。
        self.pdf_controller = None

        # 各メニューを作成します。
        self._create_file_menu_button()
        self._create_settings_menu_button()
        self._create_help_menu_button()

    def set_pdf_controller(self, pdf_controller):
        """
        PDFコントローラーを設定します。

        Parameters
        ----------
        pdf_controller : PDFController
            PDFコントローラーのインスタンスです。
        """
        self.pdf_controller = pdf_controller

    def _create_file_menu_button(self) -> None:
        """
        ファイルメニューボタンを作成します。
        """
        # ファイルメニューボタンを作成します。
        self.file_button = QToolButton()
        self.file_button.setText(i18n_module._("File") + " (&F)")
        self.file_button.setShortcut("Alt+F")
        self.file_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.file_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # 矢印を非表示にします。
        self.file_button.setMinimumWidth(ui_config.MENU_BUTTON_MIN_WIDTH)

        # ファイルメニューを作成します。
        self.file_menu = QMenu()
        self.file_button.setMenu(self.file_menu)

        # 開くアクションを作成します
        self.open_action = QAction(i18n_module._("Open"), self.main_window)
        self.open_action.setShortcut("Ctrl+O")
        self.file_menu.addAction(self.open_action)

        # 最近開いたファイルのセパレータを追加します
        self.file_menu.addSeparator()

        # 最近開いたファイルのリストを追加します
        self.recent_file_actions = []
        recent_files = self._get_recent_files()

        if recent_files:
            for filepath, _ in recent_files:
                truncated_path = self._truncate_path(filepath)
                action = QAction(truncated_path, self.main_window)
                action.setData(filepath)  # 元のパスをデータとして保存します
                self.file_menu.addAction(action)
                self.recent_file_actions.append(action)

        # 終了前のセパレータを追加します
        self.file_menu.addSeparator()

        # 終了アクションを作成します
        self.exit_action = QAction(i18n_module._("Exit"), self.main_window)
        self.exit_action.setShortcut("Alt+F4")
        self.file_menu.addAction(self.exit_action)

        # ツールバーに追加します
        self.menu_toolbar.addWidget(self.file_button)

    def _create_settings_menu_button(self) -> None:
        """
        設定メニューボタンを作成します。
        """
        # 設定メニューボタンを作成します
        self.settings_button = QToolButton()
        self.settings_button.setText(i18n_module._("Settings") + " (&S)")
        self.settings_button.setShortcut("Alt+S")
        self.settings_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.settings_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # 矢印を非表示にします
        self.settings_button.setMinimumWidth(ui_config.MENU_BUTTON_MIN_WIDTH)

        # 設定メニューを作成します
        self.settings_menu = QMenu()
        self.settings_button.setMenu(self.settings_menu)

        # 言語サブメニューを作成します。
        self.language_menu = QMenu(i18n_module._("Language"), self.main_window)
        self.settings_menu.addMenu(self.language_menu)

        # 言語選択用のアクショングループを作成します。
        self.language_group = QActionGroup(self.main_window)
        self.language_group.setExclusive(True)  # 排他的選択（ラジオボタン動作）を設定します。

        # 言語オプションを追加します
        self._add_language("English", "en_US")
        self._add_language("日本語", "ja_JP")
        self._add_language("简体中文", "zh_CN")
        self._add_language("繁體中文", "zh_TW")

        # 現在の言語設定を反映します
        self._set_current_language()

        # ツールバーに追加します
        self.menu_toolbar.addWidget(self.settings_button)

    def _create_help_menu_button(self) -> None:
        """
        ヘルプメニューボタンを作成します。
        """
        # ヘルプメニューボタンを作成します
        self.help_button = QToolButton()
        self.help_button.setText(i18n_module._("Help") + " (&H)")
        self.help_button.setShortcut("Alt+H")
        self.help_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.help_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")  # 矢印を非表示にします
        self.help_button.setMinimumWidth(ui_config.MENU_BUTTON_MIN_WIDTH)

        # ヘルプメニューを作成します
        self.help_menu = QMenu()
        self.help_button.setMenu(self.help_menu)

        # ライセンス アクションを作成します
        self.licenses_action = QAction(i18n_module._("Licenses"), self.main_window)
        self.licenses_action.triggered.connect(self._show_authors)
        self.help_menu.addAction(self.licenses_action)

        # ツールバーに追加します
        self.menu_toolbar.addWidget(self.help_button)

    def _add_language(self, label: str, lang_code: str) -> None:
        """
        言語メニューに言語オプションを追加します。

        Parameters
        ----------
        label : str
            表示する言語名です。
        lang_code : str
            言語コードです（例：'en_US'、'ja_JP'）。
        """
        action = QAction(label, self.main_window)
        action.setCheckable(True)
        action.setData(lang_code)
        action.triggered.connect(lambda: self._change_language(lang_code))

        self.language_group.addAction(action)
        self.language_menu.addAction(action)

    def _change_language(self, lang: str) -> None:
        """
        言語を変更し、設定を保存します。

        Parameters
        ----------
        lang: str
            言語コードです（例：'en_US'、'ja_JP'）。
        """
        current_lang = self.settings.get_language()

        # 現在の言語と異なる場合のみ、変更を適用します。
        if current_lang != lang:
            self.settings.set_language(lang)
            self.settings.save_settings()

            # i18nシステムに言語変更を反映
            from ..i18n import set_language

            set_language(lang)

            # シグナルを発行します
            self.language_changed.emit(lang)

            # 再起動を促すメッセージを表示します。
            QMessageBox.information(
                self.main_window,
                i18n_module._("Language Changed"),
                i18n_module._("Please restart the application for the language change to take effect."),
            )

    def _set_current_language(self) -> None:
        """
        現在の言語設定をメニューに反映します。
        """
        current_lang = self.settings.get_language()
        logger.info(f"Setting current language in menu: {current_lang}")

        # すべてのアクションのチェック状態をリセットします。
        for action in self.language_group.actions():
            action.setChecked(False)
            logger.info(f"Language menu item: {action.data()} (unchecked)")

        # 現在の言語のアクションをチェックします。
        if current_lang:
            for action in self.language_group.actions():
                if action.data() == current_lang:
                    action.setChecked(True)
                    logger.info(f"Checked language menu item: {current_lang}")
                    break

    def _get_recent_files(self, max_files: int = None) -> list:
        """
        最近アクセスしたファイルのリストを取得します。

        Parameters
        ----------
        max_files: int
            表示する最大ファイル数です。

        Returns
        -------
        list
            (ファイルパス, 最終アクセス日時) のタプルのリストです。
        """
        recent_files = []

        # 設定から最近のファイルを取得します
        files_dict = self.settings._settings_data.get("recent_files", {})

        # 最終アクセス日時でソートします
        for filepath, settings in files_dict.items():
            last_accessed = settings.get("last_accessed", "")
            import os

            if last_accessed and os.path.exists(filepath) and filepath.lower().endswith(".pdf"):
                recent_files.append((filepath, last_accessed))

        # 最終アクセス日時の新しい順にソートします
        recent_files.sort(key=lambda x: x[1], reverse=True)

        # 最大表示数に制限します
        if max_files is None:
            max_files = file_config.DEFAULT_RECENT_FILES_LIMIT
        return recent_files[:max_files]

    def _truncate_path(self, path: str, max_length: int = None) -> str:
        """
        ファイルパスが長すぎる場合に短縮します。

        Parameters
        ----------
        path: str
            短縮するファイルパスです。
        max_length: int
            最大長さです。

        Returns
        -------
        str
            短縮されたパスです。
        """
        if max_length is None:
            max_length = ui_config.MAX_MENU_PATH_LENGTH
        if len(path) <= max_length:
            return path

        # パスが長すぎる場合は中央を省略します
        if max_length <= 3:
            return "..."

        # 先頭と末尾を残して中央を省略します
        start_len = (max_length - 3) // 2
        end_len = max_length - 3 - start_len
        return path[:start_len] + "..." + path[-end_len:] if end_len > 0 else path[:start_len] + "..."

    def _open_recent_file(self, action) -> None:
        """
        最近開いたファイルを開きます。

        Parameters
        ----------
        action : QAction
            トリガーされたアクションです。
        """
        filepath = action.data()
        if filepath and os.path.exists(filepath):
            # PDFコントローラーを使用してファイルを開きます
            if hasattr(self, "pdf_controller") and self.pdf_controller:
                self.pdf_controller.load_pdf(filepath)

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
            QMessageBox.critical(self.main_window, i18n_module._("Error"), str(e))

    def update_recent_files_menu(self) -> None:
        """
        最近開いたファイルのメニューを更新します。
        """
        # 既存の最近開いたファイルのアクションを削除します
        for action in self.recent_file_actions:
            self.file_menu.removeAction(action)

        # 最近開いたファイルのリストを再構築します
        self.recent_file_actions = []
        recent_files = self._get_recent_files()

        if recent_files:
            # 最近開いたファイルのアクションを追加します
            for filepath, _ in recent_files:
                truncated_path = self._truncate_path(filepath)
                action = QAction(truncated_path, self.main_window)
                action.setData(filepath)
                self.file_menu.insertAction(self.exit_action, action)
                self.recent_file_actions.append(action)
                action.triggered.connect(lambda checked=False, action=action: self._open_recent_file(action))

            # 最近開いたファイルとExitの間にセパレータを追加します
            self.file_menu.insertSeparator(self.exit_action)

    def connect_file_actions(self, show_file_dialog, on_closing) -> None:
        """
        ファイル メニューのアクションを接続します。

        Parameters
        ----------
        show_file_dialog: callable
            ファイル ダイアログを表示するコールバック関数です。
        on_closing: callable
            アプリケーションを終了するコールバック関数です。
        """
        self.open_action.triggered.connect(show_file_dialog)
        self.exit_action.triggered.connect(on_closing)

        # 最近開いたファイルのアクションを接続します
        for action in self.recent_file_actions:
            action.triggered.connect(lambda checked=False, action=action: self._open_recent_file(action))

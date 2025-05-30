"""PDFCrop の一元化されたエラーハンドリングです。"""

import sys
import traceback
from collections.abc import Callable
from enum import Enum
from typing import Any

from PySide6.QtWidgets import QMessageBox, QWidget

from .i18n import _
from .logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """エラーの深刻度レベルです。"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler:
    """アプリケーションの一元化されたエラー ハンドラーです。"""

    def __init__(self, parent_widget: QWidget | None = None):
        """エラー ハンドラーを初期化します。

        Args:
            parent_widget : エラー ダイアログの親ウィジェット
        """
        self._parent_widget = parent_widget
        self._error_callbacks: dict[type, Callable] = {}
        self._show_dialogs = True

    def set_parent_widget(self, widget: QWidget) -> None:
        """エラー ダイアログの親ウィジェットを設定します。

        Args:
            widget : 親ウィジェット
        """
        self._parent_widget = widget

    def set_show_dialogs(self, show: bool) -> None:
        """エラー ダイアログを有効または無効にします。

        Args:
            show : エラー ダイアログを表示するかどうか
        """
        self._show_dialogs = show

    def register_error_callback(self, error_type: type, callback: Callable) -> None:
        """特定のエラータイプのコールバックを登録します。

        Args:
            error_type : 処理する例外タイプ
            callback : このエラーが発生したときに呼び出す関数
        """
        self._error_callbacks[error_type] = callback

    def handle_error(
        self,
        error: Exception,
        context: str = "",
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        show_dialog: bool = None,
    ) -> None:
        """適切なログ記録と UI フィードバックでエラーを処理します。

        Args:
            error : 発生した例外
            context : エラーが発生したコンテキストの説明
            severity : エラーの深刻度レベル
            show_dialog : ダイアログを表示するかどうか（グローバル設定を上書き）
        """
        # エラー メッセージをフォーマットします。
        error_msg = str(error)
        if context:
            full_message = f"{context}: {error_msg}"
        else:
            full_message = error_msg

        # 深刻度に基づいてエラーをログ記録します。
        if severity == ErrorSeverity.INFO:
            logger.info(full_message)
        elif severity == ErrorSeverity.WARNING:
            logger.warning(full_message)
        elif severity == ErrorSeverity.ERROR:
            logger.error(full_message, exc_info=error)
        elif severity == ErrorSeverity.CRITICAL:
            logger.critical(full_message, exc_info=error)

        # 登録されたコールバックをチェックします。
        error_type = type(error)
        if error_type in self._error_callbacks:
            try:
                self._error_callbacks[error_type](error, context)
            except Exception as callback_error:
                logger.error(f"Error in error callback: {callback_error}")

        # 有効な場合はダイアログを表示します。
        should_show = show_dialog if show_dialog is not None else self._show_dialogs
        if should_show and severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self._show_error_dialog(full_message, severity)

    def handle_exception(self, exc_type: type, exc_value: Exception, exc_traceback: Any, context: str = "") -> None:
        """未捕捉例外を処理します。

        Args:
            exc_type : 例外タイプ
            exc_value : 例外のインスタンス
            exc_traceback : トレースバック オブジェクト
            context : コンテキストの説明
        """
        # トレースバックをフォーマットします。
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_text = "".join(tb_lines)

        # 完全なトレースバックをログ記録します。
        logger.critical(f"Uncaught exception in {context}:\n{tb_text}")

        # 例外を処理します。
        self.handle_error(exc_value, f"Uncaught exception in {context}", ErrorSeverity.CRITICAL)

    def _show_error_dialog(self, message: str, severity: ErrorSeverity) -> None:
        """ユーザーにエラー ダイアログを表示します。

        Args:
            message : 表示するエラー メッセージ
            severity : エラーの深刻度レベル
        """
        if not self._parent_widget:
            return

        # 深刻度に基づいてダイアログのアイコンとタイトルを決定します。
        if severity == ErrorSeverity.WARNING:
            icon = QMessageBox.Warning
            title = _("Warning")
        elif severity == ErrorSeverity.CRITICAL:
            icon = QMessageBox.Critical
            title = _("Critical Error")
        else:
            icon = QMessageBox.Critical
            title = _("Error")

        # ダイアログを作成して表示します。
        msg_box = QMessageBox(self._parent_widget)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()

    def create_exception_hook(self, context: str = "application") -> Callable:
        """sys.excepthook 用の例外フックを作成します。

        Args:
            context : 例外のコンテキスト説明

        Returns:
            例外フック関数
        """

        def exception_hook(exc_type, exc_value, exc_traceback):
            # KeyboardInterrupt は処理しません。
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            self.handle_exception(exc_type, exc_value, exc_traceback, context)

        return exception_hook


# グローバル エラー ハンドラー インスタンスです。
_global_error_handler: ErrorHandler | None = None


def get_error_handler() -> ErrorHandler:
    """グローバル エラー ハンドラー インスタンスを取得します。

    Returns:
        グローバル エラー ハンドラー
    """
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_global_error_handler(handler: ErrorHandler) -> None:
    """グローバル エラー ハンドラー インスタンスを設定します。

    Args:
        handler : グローバルとして設定するエラー ハンドラー
    """
    global _global_error_handler
    _global_error_handler = handler


def setup_global_exception_handling(parent_widget: QWidget | None = None) -> None:
    """グローバル例外処理をセットアップします。

    Args:
        parent_widget : エラー ダイアログの親ウィジェット
    """
    handler = get_error_handler()
    if parent_widget:
        handler.set_parent_widget(parent_widget)

    # グローバル例外フックを設定します。
    sys.excepthook = handler.create_exception_hook("global")

    logger.info("Global exception handling configured")

"""PDFCrop PySide6 ベースのクリップボード操作を担当するモジュールです。

このモジュールは、ファイルパスのクリップボードへのコピーなどの
クリップボード関連の操作を提供します。
"""

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from ...exceptions import ClipboardError
from ...logger import get_logger
from ...utils.powershell_executor import PowerShellExecutor

logger = get_logger(__name__)


class ClipboardTask(QRunnable):
    """
    クリップボード操作をバックグラウンドで実行するためのタスククラスです。

    Attributes
    ----------
    filepath : str
        操作対象のファイルパスです。
    callback : function
        処理完了時に呼び出すコールバック関数です。
    error_callback : function
        エラー発生時に呼び出すコールバック関数です。
    """

    def __init__(self, filepath: str, callback, error_callback):
        """
        ClipboardTask を初期化します。

        Parameters
        ----------
        filepath : str
            操作対象のファイルパスです。
        callback : function
            処理完了時に呼び出すコールバック関数です。
        error_callback : function
            エラー発生時に呼び出すコールバック関数です。
        """
        super().__init__()
        self.filepath = filepath
        self.callback = callback
        self.error_callback = error_callback

    @Slot()
    def run(self) -> None:
        """
        タスクを実行します。

        Notes
        -----
        このメソッドは QRunnable の run() をオーバーライドし、
        バックグラウンドスレッドで PowerShell を使用してクリップボード操作を実行します。
        """
        try:
            # PowerShell スクリプトを作成します。
            commands = [
                "Add-Type -AssemblyName System.Windows.Forms",
                "$files = New-Object System.Collections.Specialized.StringCollection",
                f'$files.Add("{self.filepath}")',
                "[System.Windows.Forms.Clipboard]::SetFileDropList($files)",
            ]

            # PowerShell を実行します。
            result = PowerShellExecutor.execute_script_block(commands)

            if result is None:
                raise ClipboardError("クリップボードへのコピー中にエラーが発生しました", self.filepath)

            # 成功時のコールバックを実行します。
            self.callback()

        except ClipboardError as e:
            # クリップボード操作に失敗した場合です。
            self.error_callback(e)
        except Exception as e:
            # その他の予期しないエラーです。
            self.error_callback(ClipboardError(f"予期しないエラーが発生しました: {str(e)}", self.filepath))


class ImageClipboardTask(QRunnable):
    """
    画像をクリップボードにコピーするためのタスククラスです。

    Attributes
    ----------
    filepath : str
        操作対象の画像ファイルパスです。
    callback : function
        処理完了時に呼び出すコールバック関数です。
    error_callback : function
        エラー発生時に呼び出すコールバック関数です。
    """

    def __init__(self, filepath: str, callback, error_callback):
        """
        ImageClipboardTask を初期化します。

        Parameters
        ----------
        filepath: str
            操作対象の画像ファイル パスです。
        callback: function
            処理完了時に呼び出すコールバック関数です。
        error_callback: function
            エラー発生時に呼び出すコールバック関数です。
        """
        super().__init__()
        self.filepath = filepath
        self.callback = callback
        self.error_callback = error_callback

    @Slot()
    def run(self) -> None:
        """
        タスクを実行します。

        Notes
        -----
        このメソッドは QRunnable の run() をオーバーライドし、
        バックグラウンド スレッドで PowerShell を使用して画像をクリップボードにコピーします。
        """
        try:
            # PowerShell スクリプトを作成します。
            commands = [
                "Add-Type -AssemblyName System.Windows.Forms",
                "Add-Type -AssemblyName System.Drawing",
                f'$img = [System.Drawing.Image]::FromFile("{self.filepath}")',
                "[System.Windows.Forms.Clipboard]::SetImage($img)",
            ]

            # PowerShell を実行します。
            result = PowerShellExecutor.execute_script_block(commands)

            if result is None:
                raise ClipboardError("画像のクリップボードへのコピー中にエラーが発生しました", self.filepath)

            # 成功時のコールバックを実行します。
            self.callback()

        except ClipboardError as e:
            # クリップボード操作に失敗した場合の処理です。
            self.error_callback(e)
        except Exception as e:
            # その他の予期しないエラーの処理です。
            self.error_callback(ClipboardError(f"予期しないエラーが発生しました: {str(e)}", self.filepath))


class ClipboardManager(QObject):
    """
    PySide6 ベースのクリップボード操作を管理するクラスです。

    このクラスは、ファイル パスのクリップボードへのコピーなどのクリップボード関連の操作を提供します。

    Signals
    -------
    operation_completed: Signal
        操作が完了した時に発行されるシグナルです。
    operation_error: Signal(Exception)
        操作中にエラーが発生した時に発行されるシグナルです。

    Notes
    -----
    現在の実装は Windows の PowerShell を使用しています。
    他のプラットフォームへの対応が必要な場合は、プラットフォーム固有の実装を追加する必要があります。
    """

    # シグナルの定義です。
    operation_completed = Signal()
    operation_error = Signal(Exception)

    def __init__(self) -> None:
        """
        ClipboardManager を初期化します。
        """
        super().__init__()
        self.thread_pool = QThreadPool.globalInstance()

    def copy_file_to_clipboard(self, filepath: str | Path) -> None:
        """
        ファイル パスをクリップボードにコピーします。

        Parameters
        ----------
        filepath: str | Path
            クリップボードにコピーするファイルのパスです。

        Raises
        ------
        ClipboardError
            ファイルの検証に失敗した場合に発生します。

        Notes
        -----
        このメソッドは、PowerShell を使用してファイル パスをクリップボードにコピーします。
        ファイル パスは、エクスプローラーなどにペースト可能な形式でコピーされます。
        処理は別スレッドで実行され、完了時に operation_completed シグナルが発行されます。
        エラーが発生した場合は operation_error シグナルが発行されます。
        """
        # パスを検証して文字列に変換します。
        self._validate_filepath(filepath)
        filepath_str = str(Path(filepath).absolute())
        logger.debug(f"ファイル パスをクリップボードにコピーします: {filepath_str}")

        # タスクを作成して実行します。
        task = ClipboardTask(filepath_str, self._on_completion, self._on_error)
        self.thread_pool.start(task)

    def copy_image_to_clipboard(self, filepath: str | Path) -> None:
        """
        画像ファイルをクリップボードにコピーします。

        Parameters
        ----------
        filepath: str | Path
            クリップボードにコピーする画像ファイルのパスです。

        Raises
        ------
        ClipboardError
            ファイルの検証に失敗した場合に発生します。

        Notes
        -----
        このメソッドは、PowerShell を使用して画像ファイルをクリップボードにコピーします。
        処理は別スレッドで実行され、完了時に operation_completed シグナルが発行されます。
        エラーが発生した場合は operation_error シグナルが発行されます。
        """
        # パスを検証して文字列に変換します。
        self._validate_filepath(filepath)
        filepath_str = str(Path(filepath).absolute())
        logger.debug(f"画像ファイルをクリップボードにコピーします: {filepath_str}")

        # タスクを作成して実行します。
        task = ImageClipboardTask(filepath_str, self._on_completion, self._on_error)
        self.thread_pool.start(task)

    @staticmethod
    def _validate_filepath(filepath: str | Path) -> None:
        """
        ファイル パスの妥当性を検証します。

        Parameters
        ----------
        filepath: str | Path
            検証するファイル パスです。

        Raises
        ------
        ClipboardError
            ファイル パスが無効な場合に発生します。

        Notes
        -----
        このメソッドは、ファイル パスが有効で、ファイルが実際に存在することを確認します。
        """
        path = Path(filepath)
        if not path.exists():
            raise ClipboardError("指定されたファイルが存在しません", str(path))
        if not path.is_file():
            raise ClipboardError("指定されたパスはファイルではありません", str(path))

    def _on_completion(self) -> None:
        """
        操作が正常に完了した時の処理です。

        Notes
        -----
        このメソッドは、operation_completed シグナルを発行します。
        """
        logger.debug("クリップボード操作が完了しました")
        self.operation_completed.emit()

    def _on_error(self, error: Exception) -> None:
        """
        操作中にエラーが発生した時の処理です。

        Parameters
        ----------
        error: Exception
            発生したエラーです。

        Notes
        -----
        このメソッドは、operation_error シグナルを発行します。
        """
        logger.error(f"クリップボード操作中にエラーが発生しました: {error}")
        self.operation_error.emit(error)

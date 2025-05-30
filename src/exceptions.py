"""PDFCrop アプリケーションの例外クラスを定義するモジュールです。

このモジュールは、アプリケーション固有の例外クラスを定義します。
各例外クラスは特定のエラー状況に対応し、明確なエラーメッセージを提供します。
"""


# 循環依存を回避するために翻訳インポートを遅延します。
def _get_translator():
    """循環インポートを回避するために翻訳関数を遅延取得します。"""
    try:
        from .i18n import _

        return _
    except ImportError:
        try:
            from i18n import _

            return _
        except ImportError:
            import src.i18n as i18n_module

            return i18n_module._


def _(text):
    """翻訳器を遅延ロードする翻訳関数です。"""
    translator = _get_translator()
    return translator(text)


class PDFError(Exception):
    """
    PDF ファイル操作に関連するエラーの基底クラスです。

    Parameters
    ----------
    message : str
        エラーメッセージです。

    Notes
    -----
    このクラスは、PDF ファイルの操作に関連するすべてのエラーの基底クラスとして機能します。
    具体的なエラーは、このクラスを継承した個別の例外クラスで表現されます。
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class PDFFileNotFoundError(PDFError):
    """
    PDF ファイルが見つからない場合のエラーです。

    Parameters
    ----------
    filepath : str
        見つからなかったファイルのパスです。

    Notes
    -----
    このエラーは、指定されたパスに PDF ファイルが存在しない場合に発生します。
    """

    def __init__(self, filepath: str) -> None:
        super().__init__(_("PDF file not found: {filepath}").format(filepath=filepath))


class PDFEmptyError(PDFError):
    """
    PDF ファイルにページがない場合のエラーです。

    Parameters
    ----------
    filepath : str
        空の PDF ファイルのパスです。

    Notes
    -----
    このエラーは、開こうとした PDF ファイルにページが含まれていない場合に発生します。
    """

    def __init__(self, filepath: str) -> None:
        super().__init__(_("PDF file has no pages: {filepath}").format(filepath=filepath))


class PDFProcessingError(PDFError):
    """
    PDF 処理中にエラーが発生した場合のエラーです。

    Parameters
    ----------
    message : str
        エラーの詳細メッセージです。
    filepath : str | None
        処理中のファイル パスです。

    Notes
    -----
    このエラーは、PDF ファイルの処理中 (ページの抽出など) にエラーが発生した場合に使用されます。
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        if filepath:
            message = _("{message} (file: {filepath})").format(message=message, filepath=filepath)
        super().__init__(message)


class PDFDisplayError(PDFError):
    """
    PDF 表示中にエラーが発生した場合のエラーです。

    Parameters
    ----------
    message : str
        エラーの詳細メッセージです。
    filepath : str | None
        表示しようとしたファイル パスです。

    Notes
    -----
    このエラーは、PDF ファイルの表示処理中にエラーが発生した場合に使用されます。
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        if filepath:
            message = _("{message} (file: {filepath})").format(message=message, filepath=filepath)
        super().__init__(message)


class ClipboardError(Exception):
    """
    クリップボード操作に関連するエラーです。

    Parameters
    ----------
    message : str
        エラーの詳細メッセージです。
    filepath : str | None
        クリップボードに関連するファイル パスです。

    Notes
    -----
    このエラーは、クリップボードへのファイル パスのコピーなど、
    クリップボード操作に関連するエラーが発生した場合に使用されます。
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        if filepath:
            message = _("{message} (file: {filepath})").format(message=message, filepath=filepath)
        super().__init__(message)


class SettingsError(Exception):
    """
    設定の読み込みや保存に関連するエラーです。

    Parameters
    ----------
    message : str
        エラーの詳細メッセージです。
    filepath : str, optional
        設定ファイルのパスです。

    Notes
    -----
    このエラーは、設定ファイルの読み込みや保存時にエラーが発生した場合に使用されます。
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        if filepath:
            message = _("{message} (settings file: {filepath})").format(message=message, filepath=filepath)
        super().__init__(message)


class CacheError(Exception):
    """
    キャッシュ操作に関連するエラーです。

    Parameters
    ----------
    message : str
        エラーの詳細メッセージです。
    filepath : str, optional
        キャッシュに関連するファイル パスです。

    Notes
    -----
    このエラーは、PDF ページのキャッシュ操作に関連するエラーが発生した場合に使用されます。
    """

    def __init__(self, message: str, filepath: str | None = None) -> None:
        if filepath:
            message = _("{message} (file: {filepath})").format(message=message, filepath=filepath)
        super().__init__(message)

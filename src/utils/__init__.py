"""PDFCrop アプリケーションのユーティリティ関数を提供するモジュールです。

このモジュールは、アプリケーション全体で使用される共通のユーティリティ関数を提供します。
PyInstaller 対応のリソースパス取得や、ファイルパス操作などの機能を含みます。
"""

import os
import sys
from pathlib import Path


def resource_path(*relative_parts: str) -> str:
    """
    リソースの絶対パスを返却します。PyInstaller との互換性があります。

    Parameters
    ----------
    *relative_parts : str
        パスの構成要素です。

    Returns
    -------
    str
        リソースファイルの絶対パスです。

    Notes
    -----
    このメソッドは、開発環境と PyInstaller でバンドルされた環境の両方で正しいパスを返します。
    """
    if getattr(sys, "frozen", False):
        # PyInstaller でバンドルされた環境です。
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        # 開発環境では src ディレクトリをベースパスとします。
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, *relative_parts)


def authors_file_path() -> str:
    """
    AUTHORS ファイルのパスを取得します。

    Returns
    -------
    str
        AUTHORS ファイルの絶対パスです。

    Notes
    -----
    PyInstaller でバンドルされた環境と開発環境の両方に対応しています。
    """
    candidates = [
        resource_path("AUTHORS"),
        resource_path("AUTHORS.txt"),
    ]
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        candidates.extend([os.path.join(base_dir, "AUTHORS"), os.path.join(base_dir, "AUTHORS.txt")])

    for path in candidates:
        if os.path.exists(path):
            return path

    # 見つからない場合は、既定のパスを返します。
    return candidates[0]


def normalize_path(filepath: str | Path) -> str:
    """
    ファイルパスを正規化します。

    Parameters
    ----------
    filepath : Union[str, Path]
        正規化するファイルパスです。

    Returns
    -------
    str
        正規化されたファイルパスです。

    Notes
    -----
    バックスラッシュをフォワードスラッシュに変換し、パスを正規化します。
    """
    # バックスラッシュをフォワードスラッシュに変換し、パスを解決します。
    return str(Path(filepath).resolve()).replace("\\", "/")


def truncate_path_for_display(filepath: str, max_length: int = None) -> str:
    """UI 要素での表示用にファイルパスを切り詰めます。

    Args:
        filepath : 切り詰めるファイルパスです。
        max_length : 表示文字列の最大長です。

    Returns:
        必要に応じて省略記号付きの切り詰められたパスです。
    """
    from ..config import ui_config

    if max_length is None:
        max_length = ui_config.MAX_MENU_PATH_LENGTH
    if len(filepath) <= max_length:
        return filepath

    # ファイル名を保持してディレクトリ部分を切り詰めます。
    path_obj = Path(filepath)
    filename = path_obj.name
    suffix = ui_config.PATH_TRUNCATION_SUFFIX

    if len(filename) >= max_length - len(suffix):
        # ファイル名自体が長すぎる場合は切り詰めます。
        return filename[: max_length - len(suffix)] + suffix

    # ディレクトリ部分用の利用可能スペースを計算します。
    available_space = max_length - len(filename) - len(suffix)

    if available_space <= 0:
        return suffix + filename

    # ディレクトリ部分を切り詰めます。
    dir_part = str(path_obj.parent)
    if len(dir_part) > available_space:
        dir_part = dir_part[:available_space]

    return dir_part + suffix + filename


def ensure_directory(directory_path: str | Path) -> Path:
    """
    ディレクトリが存在することを確認し、必要に応じて作成します。

    Parameters
    ----------
    directory_path : Union[str, Path]
        確認するディレクトリのパスです。

    Returns
    -------
    Path
        作成されたディレクトリの Path オブジェクトです。

    Notes
    -----
    親ディレクトリも含めて再帰的に作成されます。
    既に存在する場合はエラーになりません。
    """
    path = Path(directory_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_directory_exists(directory_path: str) -> bool:
    """ディレクトリが存在することを確認し、必要に応じて作成します (bool 戻り値版)。

    Args:
        directory_path : ディレクトリのパスです。

    Returns:
        ディレクトリが存在するか正常に作成された場合 True です。
    """
    try:
        ensure_directory(directory_path)
        return True
    except (OSError, PermissionError):
        return False


def filter_existing_files(filepaths: list[str]) -> list[str]:
    """存在するファイルのみを含むようにファイルパスのリストをフィルターします。

    Args:
        filepaths : チェックするファイルパスのリストです。

    Returns:
        存在するファイルパスのリストです。
    """
    return [filepath for filepath in filepaths if os.path.exists(filepath)]


def get_relative_path(filepath: str, base_path: str) -> str:
    """base_path から filepath への相対パスを取得します。

    Args:
        filepath : 対象ファイルパスです。
        base_path : ベースディレクトリパスです。

    Returns:
        可能であれば相対パス、そうでなければ絶対パスです。
    """
    try:
        return str(Path(filepath).relative_to(Path(base_path)))
    except ValueError:
        # 相対パスが計算できない場合は絶対パスを返します。
        return filepath

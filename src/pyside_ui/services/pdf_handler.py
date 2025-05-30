"""PDFCrop PySide6 ベースの PDF 操作を管理するモジュールです。

このモジュールは、PDF ファイルの読み込み、ページの抽出などの PDF 関連の操作を提供します。
"""

from pathlib import Path

import fitz

from ...config import pdf_config
from ...exceptions import PDFEmptyError, PDFFileNotFoundError, PDFProcessingError
from ...logger import get_logger

logger = get_logger(__name__)


class PDFDocumentHandler:
    """
    PDF ドキュメントの操作を管理するクラスです。

    このクラスは、PDF ファイルの読み込み、ページの抽出などの PDF 関連の操作を提供します。

    Attributes
    ----------
    current_document: Optional[fitz.Document]
        現在開いている PDF ドキュメントです。
    current_document_path: Optional[str]
        現在開いている PDF ドキュメントのパスです。
    temp_directory: Path
        一時ファイルを保存するディレクトリのパスです。

    Notes
    -----
    このクラスは、PyMuPDF ライブラリを使用して PDF ファイルを操作します。
    一時ファイルは指定されたディレクトリに保存され、アプリケーション終了時に
    削除する必要があります。
    """

    def __init__(self, temp_directory: str = pdf_config.TEMP_DIRECTORY) -> None:
        """
        PDFDocumentHandler を初期化します。

        Parameters
        ----------
        temp_directory: str
            一時ファイルを保存するディレクトリです。
        """
        self.current_document: fitz.Document | None = None
        self.current_document_path: str | None = None
        self.temp_directory = Path(temp_directory)

        # 一時ディレクトリを作成します。
        try:
            self.temp_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"一時ディレクトリの作成に失敗しました: {e}")

    def open_document(self, filepath: str | Path) -> None:
        """
        PDF ドキュメントを開きます。

        Parameters
        ----------
        filepath: str | Path
            開く PDF ファイルのパスです。

        Raises
        ------
        PDFFileNotFoundError
            PDF ファイルが見つからない場合の処理です。
        PDFEmptyError
            PDF ファイルにページがない場合の処理です。
        PDFProcessingError
            PDF ファイルの読み込み中にエラーが発生した場合の処理です。

        Notes
        -----
        既に開いているドキュメントがある場合は、新しいドキュメントを開く前に
        閉じられます。
        """
        filepath_str = str(Path(filepath).absolute())

        try:
            # 既存のドキュメントを閉じます。
            self.close_document()

            # 新しいドキュメントを開きます。
            self.current_document = fitz.open(filepath_str)
            if not self.current_document.page_count:
                raise PDFEmptyError(filepath_str)

            self.current_document_path = filepath_str
            logger.info(f"PDF ドキュメントを開きました: {filepath_str}")

        except PDFEmptyError:
            raise
        except FileNotFoundError as e:
            raise PDFFileNotFoundError(filepath_str) from e
        except Exception as e:
            raise PDFProcessingError(f"PDF ファイルの読み込みに失敗しました: {str(e)}", filepath_str) from e

    def close_document(self) -> None:
        """
        現在開いている PDF ドキュメントを閉じます。

        Notes
        -----
        このメソッドは、ドキュメントが開いていない場合は何も行いません。
        """
        if self.current_document:
            path = self.current_document_path
            self.current_document.close()
            self.current_document = None
            self.current_document_path = None
            logger.debug(f"PDF ドキュメントを閉じました: {path}")

    def extract_page_range(self, start_page: int, end_page: int, base_name: str | None = None) -> str:
        """
        指定されたページ範囲の PDF を抽出して新しいファイルとして保存します。

        Parameters
        ----------
        start_page: int
            開始ページ番号 (0 ベース) です。
        end_page: int
            終了ページ番号 (0 ベース) です。
        base_name: str | None
            出力ファイルのベース名です。指定しない場合は元のファイル名を使用します。

        Returns
        -------
        str
            保存されたファイルのパスです。

        Raises
        ------
        PDFFileNotFoundError
            PDF ファイルが開かれていない場合の処理です。
        PDFProcessingError
            ページの抽出中にエラーが発生した場合の処理です。

        Notes
        -----
        抽出された PDF は一時ディレクトリに保存されます。
        ファイル名は (元のファイル名-from-開始ページ-to-終了ページ.pdf) の
        形式になります。
        """
        if not self.current_document or not self.current_document_path:
            raise PDFFileNotFoundError("PDF ファイルが開かれていません")

        try:
            # 一時ディレクトリを作成します。
            self.temp_directory.mkdir(exist_ok=True, parents=True)

            # 出力ファイル名を生成します。
            if base_name is None:
                base_name = Path(self.current_document_path).stem
            save_name = f"{base_name}-from-{start_page + 1:04d}-to-{end_page:04d}.pdf"
            save_path = self.temp_directory / save_name

            # ページを抽出して新しい PDF を作成します。
            with fitz.open() as new_pdf:
                new_pdf.insert_pdf(self.current_document, from_page=start_page, to_page=end_page - 1)
                new_pdf.save(str(save_path.absolute()))

            logger.debug(f"ページを抽出しました: {start_page + 1}〜{end_page}、保存先: {save_path}")
            return str(save_path.absolute())

        except Exception as e:
            raise PDFProcessingError(f"ページの抽出に失敗しました: {str(e)}", self.current_document_path) from e

    def calculate_page_range(self, current_page: int, max_pages: int) -> tuple[int, int]:
        """
        現在のページを中心とした抽出範囲を計算します。

        Parameters
        ----------
        current_page: int
            現在のページ番号 (0 ベース) です。
        max_pages: int
            最大ページ数です。

        Returns
        -------
        Tuple[int, int]
            (開始ページ、終了ページ) のタプルです。

        Notes
        -----
        現在のページを中心に、指定された最大ページ数に収まるように
        開始ページと終了ページを計算します。
        """
        if not self.current_document:
            return (0, 0)

        # 現在のページを含む前方のページを抽出する範囲を計算します。
        # 例として current_page=5、max_pages=3 の場合、3、4、5 ページを抽出 (0 ベースで 2、3、4) します。
        end_page = current_page + 1  # 現在のページを含みます（0 ベースのため +1）。
        start_page = max(0, end_page - max_pages)  # 最大 max_pages 分前のページからとします。

        # 実際に抽出可能な範囲に調整します。
        end_page = min(end_page, self.current_document.page_count)

        return (start_page, end_page)

    def get_page_count(self) -> int:
        """
        現在の PDF ドキュメントのページ数を取得します。

        Returns
        -------
        int
            ページ数です。ドキュメントが開かれていない場合は 0 です。

        Notes
        -----
        このメソッドは、ドキュメントが開かれていない場合でもエラーを
        発生させず、0 を返します。
        """
        return self.current_document.page_count if self.current_document else 0

    def cleanup_temp_files(self) -> None:
        """
        一時ディレクトリ内のファイルをすべて削除します。

        Notes
        -----
        このメソッドは、アプリケーション終了時に呼び出されることを想定しています。
        一時ファイルの削除に失敗してもエラーは発生させません。
        """
        if self.temp_directory.exists():
            for file in self.temp_directory.glob("*.pdf"):
                try:
                    file.unlink()
                    logger.debug(f"一時ファイルを削除しました: {file}")
                except Exception as e:
                    logger.warning(f"一時ファイルの削除に失敗しました: {file}、エラー: {e}")
            try:
                if not any(self.temp_directory.glob("*")):
                    self.temp_directory.rmdir()
                    logger.debug(f"一時ディレクトリを削除しました: {self.temp_directory}")
            except Exception as e:
                logger.warning(f"一時ディレクトリの削除に失敗しました: {self.temp_directory}、エラー: {e}")

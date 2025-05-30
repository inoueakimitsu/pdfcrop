"""PDFCrop PySide6 ベースのページ キャッシュを実装するモジュールです。

このモジュールは、レンダリングされた PDF ページのキャッシュを提供し、
アプリケーションのパフォーマンスを向上させます。
"""

import threading
import time

import fitz
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from ...config import cache_config
from ...logger import get_logger

logger = get_logger(__name__)


class PageCache:
    """
    レンダリングされた PDF ページをキャッシュするクラスです。

    このクラスは、レンダリングされた PDF ページをメモリにキャッシュし、
    再利用することでパフォーマンスを向上させます。

    Attributes
    ----------
    cache : Dict[str, QPixmap]
        キャッシュされたページの辞書です。キーはドキュメントパス、ページ番号、
        スケールファクターの組み合わせです。
    cache_lock : threading.Lock
        キャッシュの同時アクセスを防ぐためのロックです。

    Notes
    -----
    このクラスは、QPixmap オブジェクトをキャッシュし、
    メモリ使用量を管理します。
    """

    def __init__(self) -> None:
        """
        PageCache を初期化します。
        """
        self.cache: dict[str, QPixmap] = {}
        self.cache_lock = threading.Lock()
        self.max_cache_size = cache_config.MAX_CACHE_SIZE_GB
        self.current_cache_size = 0
        self.last_accessed: dict[str, float] = {}

    def get_cache_key(self, doc_path: str, page_num: int, scale_factor: float) -> str:
        """
        キャッシュ キーを生成します。

        Parameters
        ----------
        doc_path: str
            ドキュメントのパスです。
        page_num: int
            ページ番号です。
        scale_factor: float
            スケール ファクターです。

        Returns
        -------
        str
            生成されたキャッシュ キーです。
        """
        return f"{doc_path}_{page_num}_{scale_factor}"

    def get_page_image(self, doc_path: str, page_num: int, scale_factor: float) -> QPixmap | None:
        """
        キャッシュからページ画像を取得します。

        Parameters
        ----------
        doc_path: str
            ドキュメントのパスです。
        page_num: int
            ページ番号です。
        scale_factor: float
            スケール ファクターです。

        Returns
        -------
        Optional[QPixmap]
            キャッシュされたページ画像です。キャッシュにない場合は None です。
        """
        cache_key = self.get_cache_key(doc_path, page_num, scale_factor)

        with self.cache_lock:
            if cache_key in self.cache:
                # アクセス時間を更新します。
                self.last_accessed[cache_key] = time.time()
                return self.cache[cache_key]

            # スケールが異なる同じページが存在するか確認します。
            # より高解像度のキャッシュがあれば、それをリサイズして返します。
            for existing_key in self.cache.keys():
                if existing_key.startswith(f"{doc_path}_{page_num}_"):
                    # キャッシュ キーからスケールを抽出します。
                    try:
                        existing_scale = float(existing_key.split("_")[2])
                        if existing_scale > scale_factor:
                            # 高解像度のキャッシュを取得してリサイズします。
                            high_res_pixmap = self.cache[existing_key]
                            scaled_pixmap = high_res_pixmap.scaled(
                                int(high_res_pixmap.width() * (scale_factor / existing_scale)),
                                int(high_res_pixmap.height() * (scale_factor / existing_scale)),
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )

                            # 新しく生成したスケール バージョンをキャッシュします。
                            self.cache[cache_key] = scaled_pixmap
                            self.last_accessed[cache_key] = time.time()

                            # 推定サイズを計算します。
                            estimated_size = (scaled_pixmap.width() * scaled_pixmap.height() * 4) / (1024 * 1024)
                            self.current_cache_size += estimated_size

                            return scaled_pixmap
                    except (ValueError, IndexError):
                        # キー形式が期待通りでない場合は無視します。
                        continue

        return None

    def cache_page(self, doc_path: str, page_num: int, page: fitz.Page, scale_factor: float | None = None) -> QPixmap:
        """
        ページをキャッシュに追加します。

        Parameters
        ----------
        doc_path: str
            ドキュメントのパスです。
        page_num: int
            ページ番号です。
        page: fitz.Page
            キャッシュする PDF ページです。
        scale_factor: float | None
            スケール ファクターです。指定しない場合は 1.0 が使用されます。

        Returns
        -------
        QPixmap
            キャッシュされたページ画像です。
        """
        # None の場合はデフォルト値を使用します。
        scale_factor = 1.0 if scale_factor is None else scale_factor

        # ページをレンダリングします。
        transform_matrix = fitz.Matrix(scale_factor, scale_factor)
        pix = page.get_displaylist().get_pixmap(matrix=transform_matrix, alpha=False)

        # QPixmap に変換します。
        img_data = pix.tobytes("ppm")
        qimage = QImage.fromData(img_data)
        pixmap = QPixmap.fromImage(qimage)

        # キャッシュに追加します。
        cache_key = self.get_cache_key(doc_path, page_num, scale_factor)

        with self.cache_lock:
            # キャッシュ サイズを管理します。
            estimated_size = (pix.width * pix.height * 4) / (1024 * 1024)  # MB で推定します。

            # キャッシュ サイズが上限に近い場合、最も古いエントリを削除します。
            while self.current_cache_size + estimated_size > self.max_cache_size and self.cache:
                self._remove_oldest_entry()

            # 新しいエントリをキャッシュに追加します。
            self.cache[cache_key] = pixmap
            self.last_accessed[cache_key] = time.time()
            self.current_cache_size += estimated_size

        return pixmap

    def _remove_oldest_entry(self) -> None:
        """
        最も古くアクセスされたキャッシュ エントリを削除します。
        """
        if not self.last_accessed:
            return

        oldest_key = min(self.last_accessed.items(), key=lambda x: x[1])[0]

        # エントリの推定サイズを計算します。
        # ここでは単純な推定を行います。
        if oldest_key in self.cache:
            pixmap = self.cache[oldest_key]
            estimated_size = (pixmap.width() * pixmap.height() * 4) / (1024 * 1024)  # MB で推定します。

            # キャッシュとアクセス時間から削除します。
            del self.cache[oldest_key]
            del self.last_accessed[oldest_key]

            # 現在のキャッシュ サイズを更新します。
            self.current_cache_size -= estimated_size

            logger.debug(f"Removed cache entry: {oldest_key}, estimated size: {estimated_size:.2f}MB")

    def clear_cache(self) -> None:
        """
        キャッシュを完全にクリアします。
        """
        with self.cache_lock:
            self.cache.clear()
            self.last_accessed.clear()
            self.current_cache_size = 0

    def clear_document_cache(self, doc_path: str) -> None:
        """
        特定のドキュメントに関連するキャッシュをクリアします。

        Parameters
        ----------
        doc_path: str
            クリアするドキュメントのパスです。
        """
        keys_to_remove = []

        with self.cache_lock:
            # 削除対象のキーを特定します。
            for key in list(self.cache.keys()):
                if key.startswith(f"{doc_path}_"):
                    keys_to_remove.append(key)

            # 特定したキーを削除します。
            for key in keys_to_remove:
                if key in self.cache:
                    pixmap = self.cache[key]
                    estimated_size = (pixmap.width() * pixmap.height() * 4) / (1024 * 1024)

                    del self.cache[key]
                    if key in self.last_accessed:
                        del self.last_accessed[key]

                    self.current_cache_size -= estimated_size

"""PDF レンダリング コンポーネントです。"""

from enum import Enum

import fitz
from PySide6.QtCore import QObject, QRectF, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsScene

from ...common.base import BaseComponent
from ...config import cache_config
from ...constants import ui_config
from ...logger import get_logger
from ..services.page_cache import PageCache

logger = get_logger(__name__)


class PageState(Enum):
    """PDF ページの状態を表す列挙型です。"""

    PLACEHOLDER = "placeholder"
    LOADING = "loading"
    LOADED = "loaded"


class PageLoadSignal(QObject):
    """ページ読み込みシグナルを提供するクラスです。"""

    load_page = Signal(int, bool)


class PageLoaderRunnable(QRunnable):
    """PDF ページを読み込むためのバックグラウンドタスクです。"""

    def __init__(self, page_num: int, priority: int = 5):
        super().__init__()
        self.page_num = page_num
        self.priority = priority

    def run(self):
        """ページ読み込みを実行します。"""
        page_load_signal.load_page.emit(self.page_num, True)


# グローバルシグナルオブジェクトです。
page_load_signal = PageLoadSignal()


class PDFRenderer(BaseComponent):
    """PDF ページのレンダリングとキャッシュ処理を行うクラスです。"""

    def __init__(self):
        super().__init__("PDFRenderer")
        self._scene: QGraphicsScene | None = None
        self._page_cache: PageCache | None = None
        self._document: fitz.Document | None = None
        self._page_states: dict[int, PageState] = {}
        self._page_rects: dict[int, QRectF] = {}
        self._thread_pool = QThreadPool()

    def initialize(self) -> None:
        """レンダラーを初期化します。"""
        self._page_cache = PageCache()
        self._mark_initialized()

    def set_scene(self, scene: QGraphicsScene) -> None:
        """レンダリング用のグラフィックス シーンを設定します。"""
        self._scene = scene

    def set_document(self, document: fitz.Document) -> None:
        """レンダリング用の PDF ドキュメントを設定します。"""
        self._document = document
        self._page_states.clear()
        self._page_rects.clear()

    def get_page_count(self) -> int:
        """ドキュメントのページ数を取得します。"""
        return len(self._document) if self._document else 0

    def get_page_rect(self, page_num: int) -> QRectF:
        """指定されたページの矩形領域を取得します。"""
        return self._page_rects.get(page_num, QRectF())

    def get_page_state(self, page_num: int) -> PageState:
        """指定されたページの状態を取得します。"""
        return self._page_states.get(page_num, PageState.PLACEHOLDER)

    def set_page_state(self, page_num: int, state: PageState) -> None:
        """指定されたページの状態を設定します。"""
        self._page_states[page_num] = state

    def calculate_page_positions(self, zoom_scale: float) -> None:
        """すべてのページの位置を計算します。"""
        if not self._document:
            return

        y_offset = 0
        page_padding = ui_config.PAGE_PADDING

        for page_num in range(len(self._document)):
            page = self._document[page_num]
            page_rect = page.rect

            # ページの大きさをスケールします。
            width = page_rect.width * zoom_scale
            height = page_rect.height * zoom_scale

            # 水平方向に中央揃えします。
            x_offset = 0  # シーン内で中央揃えされます。

            page_rect_f = QRectF(x_offset, y_offset, width, height)
            self._page_rects[page_num] = page_rect_f

            y_offset += height + page_padding

    def create_placeholder(self, page_num: int, zoom_scale: float) -> None:
        """ページのプレースホルダーを作成します。"""
        if not self._scene or not self._document:
            return

        page_rect = self._page_rects.get(page_num)
        if not page_rect:
            return

        # プレースホルダー矩形を作成します。
        placeholder_color = QColor(cache_config.PLACEHOLDER_COLOR)
        pen = QPen(placeholder_color)

        placeholder_item = self._scene.addRect(page_rect, pen, placeholder_color)
        placeholder_item.setData(0, f"placeholder_{page_num}")

        self.set_page_state(page_num, PageState.PLACEHOLDER)

    def load_page_async(self, page_num: int, high_priority: bool = False) -> None:
        """ページを非同期で読み込みます。"""
        if self.get_page_state(page_num) == PageState.LOADING:
            return

        self.set_page_state(page_num, PageState.LOADING)

        priority = 1 if high_priority else 5
        loader = PageLoaderRunnable(page_num, priority)
        self._thread_pool.start(loader)

    def cleanup(self) -> None:
        """レンダラーのリソースをクリーンアップします。"""
        if self._page_cache:
            self._page_cache.clear_cache()
        self._thread_pool.clear()
        super().cleanup()

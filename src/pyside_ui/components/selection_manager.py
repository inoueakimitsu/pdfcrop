"""エリア選択とラバーバンド管理コンポーネントです。"""

from PySide6.QtCore import QPoint, QRectF
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsView, QRubberBand

from ...common.base import BaseComponent
from ...config import pdf_config
from ...logger import get_logger

logger = get_logger(__name__)


class SelectionManager(BaseComponent):
    """エリア選択とラバーバンド機能を管理するクラスです。"""

    def __init__(self):
        super().__init__("SelectionManager")
        self._view: QGraphicsView | None = None
        self._rubber_band: QRubberBand | None = None
        self._selection_start: QPoint | None = None
        self._selection_rect: QGraphicsRectItem | None = None
        self._is_selecting = False

    def initialize(self) -> None:
        """選択マネージャーを初期化します。"""
        self._mark_initialized()

    def set_view(self, view: QGraphicsView) -> None:
        """選択用のグラフィックスビューを設定します。"""
        self._view = view
        if view:
            self._rubber_band = QRubberBand(QRubberBand.Rectangle, view)

    def start_selection(self, pos: QPoint) -> None:
        """指定された位置でエリア選択を開始します。"""
        if not self._view or not self._rubber_band:
            return

        self._is_selecting = True
        self._selection_start = pos

        # ラバーバンドを初期化します。
        self._rubber_band.setGeometry(pos.x(), pos.y(), 0, 0)
        self._rubber_band.show()

        logger.debug(f"Selection started at {pos}")

    def update_selection(self, pos: QPoint) -> None:
        """選択エリアを現在の位置に更新します。"""
        if not self._is_selecting or not self._selection_start or not self._rubber_band:
            return

        # 選択矩形を計算します。
        start_x = min(self._selection_start.x(), pos.x())
        start_y = min(self._selection_start.y(), pos.y())
        width = abs(pos.x() - self._selection_start.x())
        height = abs(pos.y() - self._selection_start.y())

        # ラバーバンドのジオメトリを更新します。
        self._rubber_band.setGeometry(start_x, start_y, width, height)

    def end_selection(self, pos: QPoint) -> QRectF | None:
        """選択を終了し、シーン座標で選択されたエリアを返します。

        Returns:
            シーン座標での選択矩形、または選択が小さすぎる場合は None
        """
        if not self._is_selecting or not self._selection_start or not self._view:
            return None

        self._is_selecting = False

        # ラバーバンドを非表示にします。
        if self._rubber_band:
            self._rubber_band.hide()

        # 選択サイズを計算します。
        width = abs(pos.x() - self._selection_start.x())
        height = abs(pos.y() - self._selection_start.y())

        # 最小選択サイズをチェックします。
        if width < pdf_config.MIN_SELECTION_SIZE or height < pdf_config.MIN_SELECTION_SIZE:
            logger.debug("Selection too small, ignoring")
            return None

        # シーン座標に変換します。
        start_scene = self._view.mapToScene(self._selection_start)
        end_scene = self._view.mapToScene(pos)

        selection_rect = QRectF(
            min(start_scene.x(), end_scene.x()),
            min(start_scene.y(), end_scene.y()),
            abs(end_scene.x() - start_scene.x()),
            abs(end_scene.y() - start_scene.y()),
        )

        logger.debug(f"Selection completed: {selection_rect}")
        return selection_rect

    def cancel_selection(self) -> None:
        """現在の選択をキャンセルします。"""
        if not self._is_selecting:
            return

        self._is_selecting = False
        if self._rubber_band:
            self._rubber_band.hide()

        logger.debug("Selection cancelled")

    def is_selecting(self) -> bool:
        """現在選択中かどうかをチェックします。"""
        return self._is_selecting

    def highlight_selection(self, rect: QRectF) -> QGraphicsRectItem:
        """シーンに選択ハイライトを追加します。

        Args:
            rect : シーン座標でハイライトする矩形

        Returns:
            選択を表すグラフィックスアイテム
        """
        if not self._view or not self._view.scene():
            return None

        # 選択ハイライトを作成します。
        pen = QPen(QColor(0, 120, 215), 2)  # 青色の選択色です。
        brush = QColor(0, 120, 215, 50)  # 半透明の青色です。

        selection_item = self._view.scene().addRect(rect, pen, brush)
        selection_item.setData(0, "selection_highlight")

        return selection_item

    def clear_selections(self) -> None:
        """シーンからすべての選択ハイライトをクリアします。"""
        if not self._view or not self._view.scene():
            return

        scene = self._view.scene()
        items_to_remove = []

        for item in scene.items():
            if item.data(0) == "selection_highlight":
                items_to_remove.append(item)

        for item in items_to_remove:
            scene.removeItem(item)

        logger.debug("All selections cleared")

    def get_pages_in_selection(self, selection_rect: QRectF, page_rects: dict) -> list[int]:
        """選択範囲と交差するページ番号を取得します。

        Args:
            selection_rect : シーン座標での選択矩形
            page_rects : ページ番号とその矩形をマッピングする辞書

        Returns:
            選択範囲と交差するページ番号のリスト
        """
        intersecting_pages = []

        for page_num, page_rect in page_rects.items():
            if selection_rect.intersects(page_rect):
                intersecting_pages.append(page_num)

        return sorted(intersecting_pages)

    def cleanup(self) -> None:
        """選択マネージャーのリソースをクリーンアップします。"""
        self.cancel_selection()
        if self._rubber_band:
            self._rubber_band.hide()
            self._rubber_band = None
        super().cleanup()

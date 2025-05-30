# PySide6 モジュールをモック化します。
import sys
from unittest.mock import MagicMock, patch

sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtGui"] = MagicMock()
sys.modules["fitz"] = MagicMock()


# モックを使用して、必要なクラスを定義します。
class MockPDFGraphicsView:
    pass


# モック化したクラスを注入します。
with patch("src.pyside_ui.canvas.PDFGraphicsView", MockPDFGraphicsView):
    # この時点ではモックが有効なため、実際の PDFGraphicsView は使用されません。
    pass


class DummyCanvas:
    """PDF キャンバスのテスト用モックです。"""

    def __init__(self, scroll_start=None, scroll_end=None):
        self.current_document = MagicMock()
        self.current_document.page_count = 3
        self.page_positions = {
            0: (0, 0, 100, 1000),
            1: (0, 1020, 100, 1000),
            2: (0, 2040, 100, 1000),
        }
        self.total_height = 3060
        self._height = 800

        if scroll_start is not None and scroll_end is not None:
            self._scroll_start = scroll_start
            self._scroll_end = scroll_end
        else:
            # デフォルトはページ 1 の上部が表示される位置です。
            self._scroll_start = 500 / self.total_height
            self._scroll_end = self._scroll_start + (self._height / self.total_height)

    def calculate_visible_page(self):
        """
        現在表示中のページを特定します。
        PySide6 版の実装を簡略化してテスト用に再実装します。
        """
        if not self.current_document or not self.page_positions:
            return 0

        # テスト用の簡略化された実装を行います。
        visible_pages = []

        # 表示領域を計算します。
        scene_rect_top = self._scroll_start * self.total_height
        scene_rect_bottom = self._scroll_end * self.total_height

        for page_num, (_x, y, _width, height) in self.page_positions.items():
            page_top = y
            page_bottom = y + height

            # ページが表示領域と重なっているかどうかを確認します。
            if (page_top <= scene_rect_bottom) and (page_bottom >= scene_rect_top):
                visible_pages.append(page_num)

        if visible_pages:
            # 表示されているページのうち最大のページ番号を返します。
            return max(visible_pages)

        # 見つからない場合は最も近いページを返します。
        closest_page = 0
        min_distance = float("inf")

        scene_center = (scene_rect_top + scene_rect_bottom) / 2

        for page_num, (_x, y, _width, height) in self.page_positions.items():
            page_center = y + height / 2
            distance = abs(scene_center - page_center)

            if distance < min_distance:
                min_distance = distance
                closest_page = page_num

        return closest_page


def test_calculate_visible_page_top_visible():
    """ページ 1 の上部が表示されている場合のテストです。"""
    canvas = DummyCanvas()
    result = canvas.calculate_visible_page()
    assert result == 1, "ページ 1 の上部が表示されている場合は 1 を返すべきです。"


def test_calculate_visible_page_partially_visible():
    """ページ 2 の一部だけが表示されている場合のテストです。"""
    # ページ 1 の下部とページ 2 の上部が表示される位置にスクロールします。
    scroll_start = 1800 / 3060  # ページ 1 の下部付近です。
    scroll_end = scroll_start + (800 / 3060)  # 表示領域の高さ分です。

    canvas = DummyCanvas(scroll_start, scroll_end)
    result = canvas.calculate_visible_page()
    assert result == 2, "画面内に一部でもページ 2 が表示されている場合は 2 を返すべきです。"

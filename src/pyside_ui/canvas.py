"""PDFCrop PySide6 ベースの PDF キャンバスを実装するモジュールです。

このモジュールは、PDF ページのレンダリング、スクロール、ズームなどの機能を提供します。
"""

from enum import Enum
from typing import Any

import fitz
from PySide6.QtCore import QObject, QPointF, QRect, QRectF, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QMessageBox

from ..config import cache_config, pdf_config, ui_config
from ..logger import get_logger
from .services.page_cache import PageCache

logger = get_logger(__name__)


class PageState(Enum):
    """
    PDF ページの状態を表す列挙型です。
    """

    PLACEHOLDER = "placeholder"
    LOADING = "loading"
    LOADED = "loaded"


class PageLoadSignal(QObject):
    """ページ読み込みのシグナルを提供するクラスです。"""

    load_page = Signal(int, bool)


# グローバルシグナルオブジェクトです。
page_load_signal = PageLoadSignal()


class PageLoaderRunnable(QRunnable):
    """
    PDF ページの読み込みを行うバックグラウンド タスクです。

    Attributes
    ----------
    page_num : int
        読み込むページ番号です。
    priority : int
        読み込み優先度です (低い値が高優先度)。
    """

    def __init__(self, page_num: int, priority: int):
        """
        PageLoaderRunnable を初期化します。

        Parameters
        ----------
        page_num : int
            読み込むページ番号です。
        priority : int
            読み込み優先度です (低い値が高優先度)。
        """
        super().__init__()
        self.page_num = page_num
        self.priority = priority
        self.setAutoDelete(True)

    def run(self):
        """
        タスクを実行します。
        """
        try:
            # メインスレッドでレンダリングを実行するためにシグナル経由で呼び出します。
            page_load_signal.load_page.emit(self.page_num, False)
        except Exception as e:
            logger.exception(f"ページローダーの実行中にエラーが発生しました: {e}")


class PDFGraphicsView(QGraphicsView):
    """
    PDF を表示するカスタム GraphicsView です。

    このクラスは、PDF ページのレンダリング、スクロール、ズーム機能を提供します。

    Signals
    -------
    visible_page_changed : Signal(int)
        表示中のページが変更されたときに発行されるシグナルです。
    zoom_changed : Signal(float)
        ズームスケールが変更されたときに発行されるシグナルです。

    Attributes
    ----------
    scale_factor : float
        現在のズームスケールです。
    page_items : Dict[int, Dict[str, QGraphicsItem]]
        各ページの表示アイテムです。
    page_positions : Dict[int, Tuple[int, int, int, int]]
        各ページの位置情報です。
    page_states : Dict[int, PageState]
        各ページの状態です。
    current_document : Optional[fitz.Document]
        現在開いている PDF ドキュメントです。
    current_visible_page : int
        現在表示中のページ番号です。
    page_cache : PageCache
        ページキャッシュです。
    """

    # シグナル定義です。
    visible_page_changed = Signal(int)
    zoom_changed = Signal(float)

    def __init__(self, parent=None):
        """
        PDFGraphicsView を初期化します。

        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェットです。
        """
        # スーパークラスを初期化します。
        scene = QGraphicsScene(parent)
        super().__init__(scene, parent)

        # フレームとマージンを完全に削除します。
        self.setFrameShape(self.Shape.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)
        self.setViewportMargins(0, 0, 0, 0)

        # シーンの余白も削除します。
        scene.setSceneRect(scene.itemsBoundingRect())

        # 背景を透明にします。
        self.setBackgroundBrush(Qt.GlobalColor.transparent)
        scene.setBackgroundBrush(Qt.GlobalColor.transparent)

        # 余白なしでビューポートを使用します。
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # ドラッグ アンド ドロップを有効化します。
        self.setAcceptDrops(True)

        # スケール ファクターを設定します。
        self.scale_factor = pdf_config.DEFAULT_ZOOM_SCALE

        # ページアイテムを管理します。
        self.page_items: dict[
            int, dict[str, Any]
        ] = {}  # {page_num: {"placeholder": QGraphicsRectItem, "text": QGraphicsTextItem,
        #             "image": QGraphicsPixmapItem}} の形式です。
        self.page_positions: dict[int, tuple[int, int, int, int]] = {}  # {page_num: (x, y, width, height)} の形式です。
        self.page_states: dict[int, PageState] = {}  # {page_num: PageState} の形式です。

        # 現在のドキュメントを設定します。
        self.current_document: fitz.Document | None = None

        # 現在表示中のページを設定します。
        self.current_visible_page = -1

        # ページキャッシュを設定します。
        self.page_cache = PageCache()

        # 読み込みキューとスレッドプールを設定します。
        self.loading_queue: list[tuple[int, int]] = []  # [(priority, page_num), ...] の形式です。
        self.thread_pool = QThreadPool.globalInstance()

        # レンダリングを設定します。
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontSavePainterState, True)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)

        # スクロールバーの処理を設定します。
        self.verticalScrollBar().valueChanged.connect(self._on_vertical_scroll)

        # マウスホイールズーム用の設定を行います。
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # 選択モード関連の変数を設定します。
        self._is_selecting = False
        self._drag_start_point = None

        # グローバルページロードシグナルとスロットを接続します。
        page_load_signal.load_page.connect(self.render_pdf_page)

    def set_document(self, document: fitz.Document) -> None:
        """
        表示する PDF ドキュメントを設定します。

        Parameters
        ----------
        document : fitz.Document
            表示する PDF ドキュメントです。
        """
        self.current_document = document
        self.clear_scene()
        # 新規ドキュメントでは表示ページをリセットします。
        self.current_visible_page = -1

        # すべてのページのプレースホルダーを作成します。
        self._create_all_placeholders()

        # 表示領域のページを優先的に読み込みます。
        self.update_visible_pages()

    def clear_scene(self) -> None:
        """
        シーンの内容をクリアします。
        """
        current_scene = self.scene()
        if current_scene:
            current_scene.clear()
        self.page_items.clear()
        self.page_states.clear()
        self.page_positions.clear()
        self.loading_queue.clear()

    def _create_all_placeholders(self) -> None:
        """
        すべてのページのプレースホルダーを作成します。
        """
        if not self.current_document:
            return
        y_offset = 0
        for page_num in range(self.current_document.page_count):
            page = self.current_document.load_page(page_num)
            width, height = self.get_page_dimensions(page)
            # 左端 (x=0) からページを配置します。
            x = 0
            y = y_offset + ui_config.PAGE_PADDING
            current_scene = self.scene()
            if current_scene:
                placeholder = current_scene.addRect(
                    QRectF(x, y, width, height), QPen(Qt.GlobalColor.gray), QColor(cache_config.PLACEHOLDER_COLOR)
                )
                text_item = current_scene.addText(f"Page {page_num + 1}")
                text_item.setDefaultTextColor(Qt.GlobalColor.gray)
                text_pos = QPointF(
                    x + width / 2 - text_item.boundingRect().width() / 2,
                    y + height / 2 - text_item.boundingRect().height() / 2,
                )
                text_item.setPos(text_pos)
            else:
                placeholder = None
                text_item = None
            self.page_items[page_num] = {"placeholder": placeholder, "text": text_item, "image": None}
            self.page_positions[page_num] = (x, y, width, height)
            self.page_states[page_num] = PageState.PLACEHOLDER
            y_offset += height + (ui_config.PAGE_PADDING * 2)

        # シーンの範囲を設定します（余白なし）。
        current_scene = self.scene()
        if current_scene:
            current_scene.setSceneRect(current_scene.itemsBoundingRect())

    @Slot(int, bool)
    def render_pdf_page(self, page_num: int, force_reload: bool = False) -> None:
        """
        PDF ページをレンダリングします。

        Parameters
        ----------
        page_num : int
            レンダリングするページ番号です。
        force_reload : bool
            強制的に再読み込みを行うかどうかです。
        """
        if not self.current_document or page_num not in self.page_positions:
            return

        # すでに読み込み済みで強制再読み込みでない場合は何もしません。
        if self.page_states.get(page_num) == PageState.LOADED and not force_reload:
            return

        # ページの状態を更新します。
        self.page_states[page_num] = PageState.LOADING

        try:
            # ページを取得します。
            page = self.current_document.load_page(page_num)

            # ページの位置情報を取得します。
            x, y, width, height = self.page_positions[page_num]

            # キャッシュから画像を取得します。
            doc_path = self.current_document.name
            pixmap = self.page_cache.get_page_image(doc_path, page_num, self.scale_factor)

            if pixmap is None:
                # キャッシュにない場合は新たにレンダリングを行います。
                pixmap = self.page_cache.cache_page(doc_path, page_num, page, self.scale_factor)

            # プレースホルダーと既存の画像を削除します
            current_scene = self.scene()
            if current_scene and page_num in self.page_items:
                if self.page_items[page_num]["placeholder"]:
                    current_scene.removeItem(self.page_items[page_num]["placeholder"])
                if self.page_items[page_num]["text"]:
                    current_scene.removeItem(self.page_items[page_num]["text"])
                if self.page_items[page_num]["image"]:
                    current_scene.removeItem(self.page_items[page_num]["image"])

            # 新しい画像アイテムを作成します。
            pixmap_item = None
            if current_scene:
                pixmap_item = current_scene.addPixmap(pixmap)
                pixmap_item.setPos(x, y)

            # アイテム参照を更新します
            self.page_items[page_num] = {"placeholder": None, "text": None, "image": pixmap_item}

            # ページの状態を更新します。
            self.page_states[page_num] = PageState.LOADED

        except Exception as e:
            logger.exception(f"ページ {page_num} のレンダリングに失敗しました: {e}")
            QMessageBox.critical(self, "Error", str(e))
            # エラーが発生した場合はプレースホルダーのままにします
            self.page_states[page_num] = PageState.PLACEHOLDER

    def set_zoom_scale(self, scale_factor: float) -> None:
        """
        ズームスケールを設定します。

        Parameters
        ----------
        scale_factor : float
            新しいズームスケールです。
        """
        old_scale = self.scale_factor
        self.scale_factor = scale_factor

        # スケールが変わった場合にシグナルを発行します。
        if old_scale != scale_factor:
            self.zoom_changed.emit(scale_factor)

    def get_page_dimensions(self, page: fitz.Page) -> tuple[int, int]:
        """
        ページの表示サイズを計算します。

        Parameters
        ----------
        page : fitz.Page
            サイズを計算する PDF ページです。

        Returns
        -------
        Tuple[int, int]
            (幅、高さ) のタプルです。
        """
        width = int(page.rect.width * self.scale_factor)
        height = int(page.rect.height * self.scale_factor)
        return width, height

    def calculate_scale_for_width(self, page: fitz.Page, target_width: int) -> float:
        """
        指定された幅に合わせるためのスケールを計算します。

        Parameters
        ----------
        page : fitz.Page
            スケールを計算する PDF ページです。
        target_width : int
            目標の幅です。

        Returns
        -------
        float
            計算されたスケールです。
        """
        if page.rect.width <= 0 or target_width <= 1:
            return pdf_config.DEFAULT_ZOOM_SCALE

        # viewport の幅を使用します（すでにスクロールバーは除外されています）。
        available_width = self.viewport().width()
        calculated_scale = available_width / page.rect.width
        return calculated_scale if calculated_scale > 0 else pdf_config.DEFAULT_ZOOM_SCALE

    def calculate_visible_page(self) -> int:
        """
        現在表示中のページを特定します。
        画面内に少しでも表示されているページのうち、最大のページ番号を返します。

        Returns
        -------
        int
            現在表示中のページ番号（0ベース）です。
        """
        if not self.current_document or not self.page_positions:
            return 0

        # ビューポートの表示領域
        viewport_rect = self.viewport().rect()
        scene_rect = self.mapToScene(viewport_rect).boundingRect()

        # 表示領域内に存在するページを探します。
        visible_pages = []

        for page_num, (x, y, width, height) in self.page_positions.items():
            page_rect = QRectF(x, y, width, height)

            # ページが表示領域と重なっているかどうかを確認します。
            if scene_rect.intersects(page_rect):
                visible_pages.append(page_num)

        if visible_pages:
            # 表示されているページのうち最大のページ番号を返します。
            return max(visible_pages)

        # 見つからない場合は最も近いページを返します。
        closest_page = 0
        min_distance = float("inf")

        scene_center = scene_rect.center().y()

        for page_num, (_x, y, _width, height) in self.page_positions.items():
            page_center = y + height / 2
            distance = abs(scene_center - page_center)

            if distance < min_distance:
                min_distance = distance
                closest_page = page_num

        return closest_page

    def update_visible_pages(self) -> None:
        """
        現在表示中のページとその周辺ページを優先的に読み込みます。
        """
        if not self.current_document:
            return

        # 現在表示中のページを特定します
        visible_page = self.calculate_visible_page()

        # ページが変化した場合やまだ読み込まれていない場合に処理を行います
        if visible_page != self.current_visible_page or self.page_states.get(visible_page) != PageState.LOADED:
            # 表示ページ変更シグナルを発行します
            if visible_page != self.current_visible_page:
                self.visible_page_changed.emit(visible_page)
                self.current_visible_page = visible_page

            # 読み込みキューをクリアします
            self.loading_queue.clear()

            # 優先度付きで読み込みキューに追加します
            # 1. 現在表示中のページ (優先度 0)
            if self.page_states.get(visible_page) != PageState.LOADED:
                self.loading_queue.append((0, visible_page))

            # 2. 前後のページ (優先度 1)
            preload_range = cache_config.PRELOAD_RANGE
            for offset in range(-preload_range, preload_range + 1):
                if offset == 0:  # 現在のページは既に追加済みです。
                    continue

                page_num = visible_page + offset
                if 0 <= page_num < self.current_document.page_count:
                    if self.page_states.get(page_num) != PageState.LOADED:
                        self.loading_queue.append((1, page_num))

            # 優先度でソートします。
            self.loading_queue.sort(key=lambda x: x[0])

            # ページ読み込みをバックグラウンドで実行します。
            for priority, page_num in self.loading_queue:
                loader = PageLoaderRunnable(page_num, priority)
                self.thread_pool.start(loader)

    def _on_vertical_scroll(self, value) -> None:
        """
        垂直スクロールバーの値が変更されたときの処理です。
        """
        # スクロール後に表示ページを直接更新します。
        self.update_visible_pages()

    def wheelEvent(self, event) -> None:
        """
        マウスホイールイベントを処理します。

        Parameters
        ----------
        event : QWheelEvent
            マウスホイールイベントです。
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl キーを押しながらのホイール操作はズームを行います。
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= pdf_config.ZOOM_IN_FACTOR
            else:
                self.scale_factor /= pdf_config.ZOOM_OUT_FACTOR

            # 強制的に再描画を行います。
            for page_num in self.page_items.keys():
                if self.page_states.get(page_num) == PageState.LOADED:
                    self.page_states[page_num] = PageState.PLACEHOLDER

            # シーン全体をクリアして再描画を行います。
            self.clear_scene()
            self._create_all_placeholders()
            self.update_visible_pages()

            # ズーム変更シグナルを発行します。
            self.zoom_changed.emit(self.scale_factor)
        else:
            # 通常のスクロールを行います。
            super().wheelEvent(event)
            # スクロール後に表示ページを直接更新します。
            self.update_visible_pages()

    def resizeEvent(self, event) -> None:
        """
        リサイズイベントを処理します。

        Parameters
        ----------
        event : QResizeEvent
            リサイズイベントです。
        """
        super().resizeEvent(event)
        # リサイズ後にシーンの幅を更新します。
        current_scene = self.scene()
        if current_scene:
            # シーンの高さを保持しながら幅を更新します。
            scene_rect = current_scene.sceneRect()
            total_width = self.viewport().width()
            current_scene.setSceneRect(0, 0, total_width, scene_rect.height())

        # 表示ページを直接更新します。
        self.update_visible_pages()

    def keyPressEvent(self, event) -> None:
        """
        キーボードイベントを処理します。

        Parameters
        ----------
        event : QKeyEvent
            キーボードイベントです。
        """
        # キー操作後に表示ページを直接更新します。
        super().keyPressEvent(event)
        self.update_visible_pages()

    def mousePressEvent(self, event) -> None:
        """
        マウスの押下イベントを処理します。

        Parameters
        ----------
        event : QMouseEvent
            マウスイベントです。
        """
        # 単純な左クリックです（修飾キーなし、シフトなし）。
        if (
            event.button() == Qt.MouseButton.LeftButton
            and not (event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            # スクロールドラッグモードに設定します。
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            super().mousePressEvent(event)

        # 右クリックです（シフトなし）: PDFコピー
        elif event.button() == Qt.MouseButton.RightButton and not (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            # PDF をコピーします。
            app = self.window().property("app")
            if app and hasattr(app, "copy_current_pages"):
                app.copy_current_pages()

        # 右ドラッグ: 領域選択
        elif event.button() == Qt.MouseButton.RightButton:
            # ドラッグ モードをラバー バンドに設定します
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            # ラバー バンド選択の開始点を設定します
            self._drag_start_point = event.pos()
            self._is_selecting = True
            # イベントを処理
            super().mousePressEvent(event)

        # Shift + 左クリック: 領域選択
        elif event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            # ドラッグ モードをラバー バンドに設定します
            self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            # ラバー バンド選択の開始点を設定します
            self._drag_start_point = event.pos()
            self._is_selecting = True
            # イベントを処理します
            super().mousePressEvent(event)

        # Ctrl + 左クリック: PDF コピー
        elif event.button() == Qt.MouseButton.LeftButton and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # PDF をコピーします
            app = self.window().property("app")
            if app and hasattr(app, "copy_current_pages"):
                app.copy_current_pages()

        else:
            # その他の場合はスクロール ドラッグに設定します
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            super().mousePressEvent(event)

    def dragEnterEvent(self, event) -> None:
        """
        ドラッグエンターイベントを処理します。

        Parameters
        ----------
        event : QDragEnterEvent
            ドラッグエンターイベントです。
        """
        # PDF ファイルのドラッグを受け入れます。
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".pdf"):
                    event.accept()
                    return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        """
        ドラッグムーブイベントを処理します。

        Parameters
        ----------
        event : QDragMoveEvent
            ドラッグムーブイベントです。
        """
        # PDF ファイルのドラッグを受け入れます。
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".pdf"):
                    event.accept()
                    return
        event.ignore()

    def dropEvent(self, event) -> None:
        """
        ドロップイベントを処理します。

        Parameters
        ----------
        event: QDropEvent
            ドロップイベントです。
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(".pdf"):
                    # アプリケーション インスタンスから直接 PDF をロードします
                    app = self.window().property("app")
                    if app and hasattr(app, "_load_pdf"):
                        app._load_pdf(file_path)
                    event.accept()
                    return
        event.ignore()

    def mouseMoveEvent(self, event) -> None:
        """
        マウス移動イベントを処理します。

        Parameters
        ----------
        event : QMouseEvent
            マウス移動イベントです。
        """

        # 親クラスの処理を呼び出します。
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """
        マウスのリリースイベントを処理します。

        Parameters
        ----------
        event: QMouseEvent
            マウスイベントです。
        """
        # 選択モード関連の変数をリセット

        # 選択状態だった場合
        if self._is_selecting and self._drag_start_point is not None:
            end_point = event.pos()
            selection_rect = QRect(self._drag_start_point, end_point).normalized()

            # 選択領域が十分な大きさの場合
            if (
                selection_rect.width() > pdf_config.MIN_SELECTION_SIZE
                and selection_rect.height() > pdf_config.MIN_SELECTION_SIZE
            ):
                # スクリーンショットをキャプチャします
                from .viewer import PDFViewer

                parent = self.parent()
                # 親が PDFViewer の場合のみキャプチャ処理を実行します
                if isinstance(parent, PDFViewer) and hasattr(parent, "capture_visible_area"):
                    parent.capture_visible_area(selection_rect)

            # 選択状態とドラッグ開始点をリセットします
            self._is_selecting = False
            self._drag_start_point = None

        # ドラッグ モードをスクロールに戻します
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # 親クラスの処理を呼び出します
        super().mouseReleaseEvent(event)

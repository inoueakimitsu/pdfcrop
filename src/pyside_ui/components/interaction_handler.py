"""マウスとキーボードの相互作用を処理するコンポーネントです。"""

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView

from ...common.base import BaseComponent
from ...common.protocols import AppProtocol
from ...config import pdf_config
from ...logger import get_logger

logger = get_logger(__name__)


class InteractionHandler(BaseComponent):
    """Handles mouse and keyboard interactions for PDF viewer."""

    def __init__(self):
        super().__init__("InteractionHandler")
        self._view: QGraphicsView | None = None
        self._app: AppProtocol | None = None
        self._is_dragging = False
        self._last_pan_point = QPoint()

    def initialize(self) -> None:
        """Initialize the interaction handler."""
        self._mark_initialized()

    def set_view(self, view: QGraphicsView) -> None:
        """Set the graphics view for interaction handling."""
        self._view = view

    def set_app(self, app: AppProtocol) -> None:
        """Set app reference for callbacks."""
        self._app = app

    def handle_mouse_press(self, event: QMouseEvent) -> bool:
        """Handle mouse press events.

        Returns:
            True if event was handled, False otherwise
        """
        if not self._view:
            return False

        if event.button() == Qt.MiddleButton:
            self._start_pan_mode(event.pos())
            return True
        elif event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ControlModifier:
                self._start_selection_mode(event.pos())
                return True

        return False

    def handle_mouse_move(self, event: QMouseEvent) -> bool:
        """Handle mouse move events.

        Returns:
            True if event was handled, False otherwise
        """
        if not self._view:
            return False

        if self._is_dragging:
            self._update_pan(event.pos())
            return True

        return False

    def handle_mouse_release(self, event: QMouseEvent) -> bool:
        """Handle mouse release events.

        Returns:
            True if event was handled, False otherwise
        """
        if not self._view:
            return False

        if event.button() == Qt.MiddleButton and self._is_dragging:
            self._end_pan_mode()
            return True

        return False

    def handle_wheel_event(self, event: QWheelEvent) -> bool:
        """Handle wheel events for zooming.

        Returns:
            True if event was handled, False otherwise
        """
        if not self._view:
            return False

        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl+Wheel
            angle_delta = event.angleDelta().y()
            zoom_factor = pdf_config.ZOOM_IN_FACTOR if angle_delta > 0 else (1.0 / pdf_config.ZOOM_OUT_FACTOR)

            # Get zoom point in scene coordinates
            zoom_point = self._view.mapToScene(event.position().toPoint())

            # Apply zoom
            self._zoom_at_point(zoom_factor, zoom_point)
            return True

        return False

    def handle_key_press(self, event: QKeyEvent) -> bool:
        """Handle key press events.

        Returns:
            True if event was handled, False otherwise
        """
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_C and modifiers & Qt.ControlModifier:
            if self._app:
                self._app.copy_current_pages()
                return True

        return False

    def _start_pan_mode(self, pos: QPoint) -> None:
        """Start panning mode."""
        if not self._view:
            return

        self._is_dragging = True
        self._last_pan_point = pos
        self._view.setCursor(Qt.ClosedHandCursor)

    def _update_pan(self, pos: QPoint) -> None:
        """Update panning."""
        if not self._view or not self._is_dragging:
            return

        delta = pos - self._last_pan_point
        self._last_pan_point = pos

        # Update scroll bars
        h_scroll = self._view.horizontalScrollBar()
        v_scroll = self._view.verticalScrollBar()

        h_scroll.setValue(h_scroll.value() - delta.x())
        v_scroll.setValue(v_scroll.value() - delta.y())

    def _end_pan_mode(self) -> None:
        """End panning mode."""
        if not self._view:
            return

        self._is_dragging = False
        self._view.setCursor(Qt.ArrowCursor)

    def _start_selection_mode(self, pos: QPoint) -> None:
        """Start area selection mode."""
        # This will be implemented when selection manager is created
        logger.debug(f"Selection mode started at {pos}")

    def _zoom_at_point(self, factor: float, scene_point) -> None:
        """Zoom at specific point."""
        if not self._view:
            return

        # Store the scene point
        old_pos = self._view.mapFromScene(scene_point)

        # Scale the view
        self._view.scale(factor, factor)

        # Get the new position and scroll to maintain the point under cursor
        new_pos = self._view.mapFromScene(scene_point)
        delta = new_pos - old_pos

        h_scroll = self._view.horizontalScrollBar()
        v_scroll = self._view.verticalScrollBar()

        h_scroll.setValue(h_scroll.value() + delta.x())
        v_scroll.setValue(v_scroll.value() + delta.y())

"""PDFCrop PySide6 ベースのツールバーを実装するモジュールです。

このモジュールは、アプリケーションのツールバーとそのコントロールを提供します。
"""

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSpinBox, QToolBar, QWidget

import src.i18n as i18n_module

from ..config import pdf_config, ui_config


class ApplicationToolbar(QToolBar):
    """
    アプリケーションのツールバーです。

    このクラスは、PDF ビューアのツールバーとそのコントロールを提供します。

    Signals
    -------
    max_pages_changed : Signal(int)
        最大ページ数が変更されたときに発行されるシグナルです。

    Attributes
    ----------
    max_pages_spinbox : QSpinBox
        最大ページ数入力用のスピンボックスです。
    """

    # シグナル定義です。
    max_pages_changed = Signal(int)

    def __init__(self, parent=None):
        """
        ApplicationToolbar を初期化します。

        Parameters
        ----------
        parent : QWidget, optional
            親ウィジェットです。
        """
        super().__init__(parent)
        self.setMovable(True)
        self.setFloatable(False)

        # 最大ページ数コントロールを作成します。
        self._create_max_pages_control()
        self.addSeparator()

    def _create_copy_action(self) -> QAction:
        """
        コピーアクションを作成します。

        Returns
        -------
        QAction
            作成されたアクションです。

        Notes
        -----
        このアクションは、現在表示中のページとその周辺をクリップボードにコピーするために使用します。
        """
        action = QAction(i18n_module._("Copy (Ctrl + C)"), self)
        action.setShortcut("Ctrl+C")
        self.addAction(action)
        return action

    def _create_max_pages_control(self) -> None:
        """
        最大ページ数コントロールを作成します。

        Notes
        -----
        このコントロールは、コピー時に含めるページ数を指定するために使用します。
        """
        # コンテナウィジェットを作成します。
        container = QWidget(self)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(
            ui_config.TOOLBAR_PADDING, ui_config.TOOLBAR_PADDING, ui_config.TOOLBAR_PADDING, ui_config.TOOLBAR_PADDING
        )

        # ラベルを作成します。
        label = QLabel(i18n_module._("Pages to Copy:"), container)
        layout.addWidget(label)

        # スピンボックスを作成します。
        self.max_pages_spinbox = QSpinBox(container)
        self.max_pages_spinbox.setMinimum(1)
        self.max_pages_spinbox.setMaximum(100)  # 最大値を適切に設定します。
        self.max_pages_spinbox.setValue(pdf_config.DEFAULT_MAX_EXTRACT_PAGES)
        self.max_pages_spinbox.valueChanged.connect(self._on_max_pages_changed)
        layout.addWidget(self.max_pages_spinbox)

        # コンテナをツールバーに追加します。
        self.addWidget(container)

    def _create_capture_action(self) -> QAction:
        """
        範囲キャプチャアクションを作成します。

        Returns
        -------
        QAction
            作成されたアクションです。
        """
        action = QAction(i18n_module._("Capture"), self)
        self.addAction(action)
        return action

    def _increment_max_pages(self) -> None:
        """
        最大抽出ページ数の値を 1 増やします。
        """
        self.max_pages_spinbox.setValue(self.max_pages_spinbox.value() + 1)

    def _decrement_max_pages(self) -> None:
        """
        最大抽出ページ数の値を 1 減らします。ただし、1 未満にはなりません。
        """
        self.max_pages_spinbox.setValue(max(1, self.max_pages_spinbox.value() - 1))

    @Slot(int)
    def _on_max_pages_changed(self, value: int) -> None:
        """
        最大ページ数が変更されたときの処理を行います。

        Parameters
        ----------
        value : int
            新しい最大ページ数です。
        """
        self.max_pages_changed.emit(value)

    def get_max_pages_value(self) -> int:
        """
        最大ページ数の入力値を取得します。

        Returns
        -------
        int
            入力された最大ページ数です。
        """
        return self.max_pages_spinbox.value()

    def set_max_pages_value(self, value: int) -> None:
        """
        最大ページ数の入力値を設定します。

        Parameters
        ----------
        value : int
            設定するページ数です。
        """
        self.max_pages_spinbox.setValue(value)

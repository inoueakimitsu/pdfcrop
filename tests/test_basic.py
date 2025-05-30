"""基本的なアプリケーションの機能をテストします。"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# PySide6 モジュールをモック化します。
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtGui"] = MagicMock()


class TestAppCreation(unittest.TestCase):
    """基本的なアプリケーションの作成をテストします。"""

    @patch("src.pyside_ui.application.QApplication")
    def test_app_creation(self, mock_qapp) -> None:
        """基本的なアプリケーションの作成をテストします。"""
        # モックの設定をします。
        mock_qapp.instance.return_value = None

        # アプリケーションの作成をします。
        from src.pyside_ui.application import PDFViewerApplication

        app = PDFViewerApplication()
        self.assertIsNotNone(app)

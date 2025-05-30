"""PDFCrop アプリケーションのエントリー ポイントです。

このモジュールは、アプリケーションを起動するためのエントリー ポイントを提供します。
PySide6 ベースの実装を使用します。
"""

import argparse
import sys

from src.logger import get_logger

logger = get_logger(__name__)

# 言語設定はアプリケーション内で処理されます


def main() -> int:
    """
    アプリケーションのエントリー ポイントです。

    Returns
    -------
    int
        アプリケーションの終了コードです。
    """
    parser = argparse.ArgumentParser(description="PDF ビューアー アプリケーション")
    parser.add_argument("pdf_file", nargs="?", help="PDF ファイルのパスです。")
    args = parser.parse_args()

    logger.info("Starting application with PySide6 UI")

    # PySide6 ベースのアプリケーションをインポートします。
    from src.pyside_ui.application import PDFViewerApplication

    pdf_file = args.pdf_file if args.pdf_file else None
    app = PDFViewerApplication(pdf_file)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())

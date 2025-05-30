"""テストパッケージの初期化です。

PyMuPDF (``fitz``) がインストールされていない環境でもテストが動作するように、
簡易的なスタブを登録します。"""

from __future__ import annotations

import os
import sys
import types

os.environ["RUNNING_TESTS"] = "1"

if "fitz" not in sys.modules:
    stub = types.SimpleNamespace(
        Document=object,
        Page=object,
        Matrix=lambda *args, **kwargs: None,
        open=lambda *args, **kwargs: None,
    )
    sys.modules["fitz"] = stub

if "PIL" not in sys.modules:
    pil_stub = types.ModuleType("PIL")
    pil_stub.Image = types.SimpleNamespace(open=lambda *a, **k: None)
    pil_stub.ImageTk = types.ModuleType("ImageTk")
    pil_stub.ImageTk.PhotoImage = object
    pil_stub.ImageGrab = types.SimpleNamespace(grab=lambda *a, **k: None)
    sys.modules["PIL"] = pil_stub
    sys.modules["PIL.Image"] = pil_stub.Image
    sys.modules["PIL.ImageTk"] = pil_stub.ImageTk
    sys.modules["PIL.ImageGrab"] = pil_stub.ImageGrab

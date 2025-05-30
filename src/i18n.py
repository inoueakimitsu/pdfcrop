import gettext
import locale
import os
from pathlib import Path

try:
    from .logger import get_logger
except ImportError:
    from logger import get_logger

logger = get_logger(__name__)

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"

_translator: gettext.NullTranslations | gettext.GNUTranslations
_current_language: str | None = None

_ = gettext.gettext


# 対応言語のリストです。
SUPPORTED_LANGUAGES = ["en_US", "ja_JP", "zh_CN", "zh_TW"]


def set_language(lang: str | None = None) -> None:
    """翻訳を初期化し、グローバルな gettext 関数を設定します。

    Parameters
    ----------
    lang : str | None
        使用する言語を指定します。None の場合は、システムのデフォルト言語を使用します。

    Returns
    -------
    None
        戻り値はありません。
    """
    global _translator, _, _current_language

    # システムの言語を検出しないようにします（言語が明示的に設定されている場合の処理です）。
    if lang is not None:
        use_lang = lang
    else:
        use_lang = os.environ.get("PDFCROP_LANG")
        if use_lang is None:
            use_lang, _enc = locale.getdefaultlocale()

    # 言語が対応言語でない場合は日本語をデフォルトとします。
    if use_lang not in SUPPORTED_LANGUAGES:
        use_lang = "ja_JP"

    _current_language = use_lang
    logger.info("Setting language to: %s", use_lang)
    logger.info("Locale directory: %s", LOCALE_DIR)
    mo_path = LOCALE_DIR / use_lang / "LC_MESSAGES" / "pdfcrop.mo"
    logger.info("Looking for translation files in: %s", mo_path)
    logger.info("Translation file exists: %s", mo_path.exists())

    try:
        # まず fallback=False で試します。
        _translator = gettext.translation(
            "pdfcrop",
            localedir=LOCALE_DIR,
            languages=[use_lang] if use_lang else None,
            fallback=False,
        )
        logger.info("Translation loaded successfully: %s", type(_translator))
    except Exception as e:
        logger.warning("Failed to load translation for %s: %s", use_lang, e)
        # fallback を使用します。
        _translator = gettext.translation(
            "pdfcrop",
            localedir=LOCALE_DIR,
            languages=[use_lang] if use_lang else None,
            fallback=True,
        )
        logger.info("Fallback translation loaded: %s", type(_translator))
        logger.info("Is NullTranslations: %s", isinstance(_translator, gettext.NullTranslations))

    _ = _translator.gettext

    # モジュールのグローバル変数も更新します。
    globals()["_"] = _

    # 翻訳のテストを実行します。
    test_str = _("Open PDF File")
    logger.info("Translation test - 'Open PDF File' translates to: %s", test_str)


def get_current_language() -> str | None:
    """現在設定されている言語を取得します。

    Returns
    -------
    str | None
        現在の言語コード、または None（設定されていない場合）
    """
    return _current_language


__all__ = ["_", "set_language", "get_current_language"]

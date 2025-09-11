"""
Inputs パッケージ - データ取得層

各種データソースからの情報取得を担当
"""

from .notion_input import NotionInput, NotionInputError
from .gdocs_input import GdocsInput, GdocsInputError

__all__ = ["NotionInput", "NotionInputError", "GdocsInput", "GdocsInputError"]

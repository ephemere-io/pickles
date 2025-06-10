"""
Inputs パッケージ - データ取得層

各種データソースからの情報取得を担当
"""

from .notion_input import NotionInput, NotionInputError

__all__ = ["NotionInput", "NotionInputError"]

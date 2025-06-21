"""
Prompts パッケージ - 分析プロンプト管理

各開発者が独立してプロンプトを編集できるよう分離
"""

from .domi_prompts import DomiPrompts
from .aga_prompts import AgaPrompts

__all__ = ["DomiPrompts", "AgaPrompts"] 
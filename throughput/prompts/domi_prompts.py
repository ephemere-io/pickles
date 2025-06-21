"""
DOMI専用プロンプト管理クラス

ドミニク用の分析プロンプトを管理
"""

from typing import Final


class DomiPrompts:
    """DOMI用プロンプト管理クラス"""
    
    # 基本プロンプトテンプレート
    BASE_TEMPLATE: Final[str] = "以下のデータを分析してください：\n\n{formatted_data}\n\n"
    
    # DOMI用分析プロンプト
    ANALYSIS_PROMPT: Final[str] = (
        "この期間の筆者の思考パターン、関心事、活動傾向を分析し、"
        "本人も気づいていないような変化や傾向を抽出して、"
        "詳細なレポートを作成してください。"
        "\n\n特に以下の観点で分析してください："
        "\n- 思考の深度と複雑さの変化"
        "\n- 新しい関心領域の発見"
        "\n- 行動パターンの変化"
        "\n- 潜在的な課題や機会の特定"
    )
    
    @classmethod
    def create_prompt(cls, formatted_data: str) -> str:
        """DOMI用分析プロンプトを生成"""
        return cls.BASE_TEMPLATE.format(formatted_data=formatted_data) + cls.ANALYSIS_PROMPT 
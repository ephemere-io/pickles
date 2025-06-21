"""
AGA専用プロンプト管理クラス

アガツマ用の分析プロンプトを管理
"""

from typing import Final


class AgaPrompts:
    """AGA用プロンプト管理クラス"""
    
    # 基本プロンプトテンプレート
    BASE_TEMPLATE: Final[str] = "以下のデータを分析してください：\n\n{formatted_data}\n\n"
    
    # AGA用分析プロンプト
    ANALYSIS_PROMPT: Final[str] = (
        "この期間の筆者の感情の変化と心境を分析し、"
        "ストレス要因や幸福度の変化を含む感情レポートを作成してください。"
        "\n\n特に以下の観点で分析してください："
        "\n- 感情の起伏とトリガー要因"
        "\n- エネルギーレベルの変動"
        "\n- 対人関係の影響"
        "\n- 心理的な成長や変化の兆候"
    )
    
    @classmethod
    def create_prompt(cls, formatted_data: str) -> str:
        """AGA用分析プロンプトを生成"""
        return cls.BASE_TEMPLATE.format(formatted_data=formatted_data) + cls.ANALYSIS_PROMPT 
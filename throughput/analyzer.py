import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# 定数をインポート
from utils import AnalysisTypes

load_dotenv()


class AnalysisError(Exception):
    """分析処理時のエラー"""
    pass


class DocumentAnalyzer:
    """ドキュメント分析クラス"""
    
    def __init__(self):
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_documents(self, 
                         raw_data: List[Dict[str, str]], 
                         analysis_type: str = AnalysisTypes.COMPREHENSIVE,
                         apply_filters: bool = True) -> Dict[str, str]:
        """ドキュメントを総合的に分析"""
        
        # フィルタリング
        filtered_data = self._filter_data(raw_data) if apply_filters else raw_data
        
        # 統計情報生成
        stats = self._generate_statistics(raw_data, filtered_data)
        
        # AI分析実行
        insights = self._generate_insights(filtered_data, analysis_type)
        
        return {
            "statistics": stats,
            "insights": insights,
            "data_count": len(filtered_data)
        }
    
    def _filter_data(self, data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """データをフィルタリング"""
        filtered = []
        seen_titles = set()
        exclude_keywords = ["test", "テスト", "削除予定"]
        
        for item in data:
            # 最小文字数チェック
            if len(item.get("text", "")) < 10:
                continue
            
            # 除外キーワードチェック
            text = item.get("text", "").lower()
            title = item.get("title", "").lower()
            if any(keyword.lower() in text or keyword.lower() in title for keyword in exclude_keywords):
                continue
            
            # 重複タイトルチェック
            item_title = item.get("title", "")
            if item_title and item_title in seen_titles:
                continue
            
            filtered.append(item)
            if item_title:
                seen_titles.add(item_title)
        
        return filtered
    
    def _generate_statistics(self, raw_data: List[Dict[str, str]], filtered_data: List[Dict[str, str]]) -> str:
        """統計情報を生成"""
        raw_count = len(raw_data)
        filtered_count = len(filtered_data)
        
        if filtered_count == 0:
            return f"取得データ数: {raw_count}件、フィルタ後: 0件（分析対象なし）"
        
        total_length = sum(len(item.get("text", "")) for item in filtered_data)
        avg_length = total_length // filtered_count if filtered_count > 0 else 0
        
        return f"取得データ数: {raw_count}件、フィルタ後: {filtered_count}件\n平均文字数: {avg_length}文字"
    
    def _generate_insights(self, data: List[Dict[str, str]], analysis_type: str) -> str:
        """AI分析を実行してインサイトを生成"""
        if not data:
            return "分析対象のデータがありません。"
        
        # データをフォーマット
        formatted_data = self._format_data_for_analysis(data)
        
        # プロンプト作成
        prompt = self._create_analysis_prompt(formatted_data, analysis_type)
        
        # AI分析実行
        try:
            resp = self._client.responses.create(
                model="o4-mini",
                reasoning={"effort": "high"},
                input=[{"role": "user", "content": prompt}],
                max_output_tokens=3000
            )
            
            data_dict = resp.to_dict()
            message_block = next(
                (item for item in data_dict["output"] if item.get("type") == "message"),
                None
            )
            
            if not message_block:
                raise RuntimeError("AI応答が見つかりませんでした。")
            
            return message_block["content"][0]["text"]
            
        except Exception as e:
            raise AnalysisError(f"AI分析エラー: {e}")
    
    def _format_data_for_analysis(self, data: List[Dict[str, str]]) -> str:
        """分析用にデータをフォーマット"""
        if not data:
            return ""
        
        # タイトルを持つデータがあるかチェック
        has_titles = any("title" in item and item["title"] for item in data)
        
        formatted_items = []
        for item in data:
            if has_titles:
                # ドキュメント形式
                title = item.get("title", "Untitled")
                text = f"日付: {item['date']}\nタイトル: {title}\n内容: {item['text']}"
            else:
                # 日誌形式
                text = f"{item['date']}: {item['text']}"
            
            formatted_items.append(text)
        
        return "\n\n".join(formatted_items)
    
    def _create_analysis_prompt(self, formatted_data: str, analysis_type: str) -> str:
        """分析タイプに応じたプロンプトを作成"""
        base_prompt = f"以下のデータを分析してください：\n\n{formatted_data}\n\n"
        
        if analysis_type == AnalysisTypes.COMPREHENSIVE:
            return base_prompt + (
                "この期間の筆者の思考パターン、関心事、活動傾向を分析し、"
                "本人も気づいていないような変化や傾向を抽出して、"
                "詳細なレポートを作成してください。"
            )
        elif analysis_type == AnalysisTypes.EMOTIONAL:
            return base_prompt + (
                "この期間の筆者の感情の変化と心境を分析し、"
                "ストレス要因や幸福度の変化を含む感情レポートを作成してください。"
            )
        elif analysis_type == AnalysisTypes.PRODUCTIVITY:
            return base_prompt + (
                "この期間の筆者の生産性とタスク管理状況を分析し、"
                "効率化の提案を含む生産性レポートを作成してください。"
            )
        else:
            return base_prompt + "このデータの特徴と傾向を分析してレポートを作成してください。"


 
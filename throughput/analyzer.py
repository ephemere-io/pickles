import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# 定数をインポート
from utils import AnalysisTypes, Logger
# プロンプト管理クラスをインポート
from .prompts import DomiPrompts, AgaPrompts

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
                         analysis_type: str = AnalysisTypes.DOMI,
                         apply_filters: bool = True) -> Dict[str, str]:
        """ドキュメントを総合的に分析"""
        
        # フィルタリングは一旦無効化
        # filtered_data = self._filter_data(raw_data) if apply_filters else raw_data
        filtered_data = raw_data

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
            Logger.log_ai_request(f"データ長={len(formatted_data)}文字, max_tokens=50000でリクエスト送信")
            
            resp = self._client.responses.create(
                model="o4-mini",
                reasoning={"effort": "high"},
                input=[{"role": "user", "content": prompt}],
                max_output_tokens=50000
            )
            
            Logger.log_ai_response("APIレスポンス受信完了")
            data_dict = resp.to_dict()
            Logger.log_ai_processing(f"レスポンス構造解析: {list(data_dict.keys())}")
            
            # レスポンス構造をより詳細にログ出力
            if "output" in data_dict:
                Logger.log_debug(f"アウトプットアイテム数: {len(data_dict['output'])}")
                for i, item in enumerate(data_dict["output"]):
                    Logger.log_debug(f"アイテム {i}: type={item.get('type')}, keys={list(item.keys())}")
            else:
                Logger.log_ai_error("レスポンスに'output'キーが存在しません", {"response": data_dict})
            
            message_block = next(
                (item for item in data_dict["output"] if item.get("type") == "message"),
                None
            )
            
            if not message_block:
                # より詳細なエラー情報を提供
                available_types = [item.get("type") for item in data_dict.get("output", [])]
                error_msg = f"メッセージブロックが見つかりません"
                Logger.log_ai_error(error_msg, {
                    "available_types": available_types,
                    "full_response": data_dict
                })
                raise RuntimeError(f"{error_msg}。利用可能なタイプ: {available_types}")
            
            Logger.log_ai_processing(f"メッセージブロック発見: コンテンツ数={len(message_block.get('content', []))}")
            
            if not message_block.get("content") or len(message_block["content"]) == 0:
                error_msg = "メッセージブロックにコンテンツが含まれていません"
                Logger.log_ai_error(error_msg, {"message_block": message_block})
                raise RuntimeError(error_msg)
            
            content_text = message_block["content"][0].get("text", "")
            Logger.log_ai_success(f"分析結果生成完了: {len(content_text)}文字")
            
            return content_text
            
        except Exception as e:
            # 詳細なエラー情報を含める
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "prompt_length": len(prompt),
                "data_length": len(formatted_data),
                "analysis_type": analysis_type
            }
            Logger.log_ai_error("AI分析処理でエラーが発生しました", error_details)
            raise AnalysisError(f"AI分析エラー: {e} | 詳細: {error_details}")
    
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
        if analysis_type == AnalysisTypes.DOMI:
            return DomiPrompts.create_prompt(formatted_data)
        elif analysis_type == AnalysisTypes.AGA:
            return AgaPrompts.create_prompt(formatted_data)
        else:
            # フォールバック用の基本プロンプト
            base_prompt = f"以下のデータを分析してください：\n\n{formatted_data}\n\n"
            return base_prompt + "このデータの特徴と傾向を分析してレポートを作成してください。"


 
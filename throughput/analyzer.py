import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# 定数をインポート
from utils import AnalysisTypes, logger
# プロンプト管理クラスをインポート
from .prompts import DomiPrompts, AgaPrompts
# 履歴管理クラスをインポート
from .analysis_history import AnalysisHistory

load_dotenv()


class AnalysisError(Exception):
    """分析処理時のエラー"""
    pass


class DocumentAnalyzer:
    """ドキュメント分析クラス"""
    
    def __init__(self, enable_history: bool = True, user_name: str = None, language: str = None):
        # テストモードの場合はモックを使用
        if os.getenv('PICKLES_TEST_MODE') == '1':
            from tests.fixtures.mock_handlers import mock_openai_api
            self._client = mock_openai_api()(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self._enable_history = enable_history
        self._history = AnalysisHistory() if enable_history else None
        self._user_name = user_name
        self._language = language
    
    def analyze_documents(self, 
                         raw_data: List[Dict[str, str]], 
                         analysis_type: str = AnalysisTypes.DOMI,
                         language: str = None,
                         apply_filters: bool = True) -> Dict[str, str]:
        """ドキュメントを総合的に分析"""
        
        logger.debug(f"言語設定 @ analyser.py, analyze_document内", "ai", language=language)
        
        # フィルタリングは一旦無効化
        # filtered_data = self._filter_data(raw_data) if apply_filters else raw_data
        filtered_data = raw_data

        # 統計情報生成
        stats = self._generate_statistics(raw_data, filtered_data)
        
        # AI分析実行
        insights = self._generate_insights(filtered_data, analysis_type, language)
        
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
    
    def _generate_insights(self, data: List[Dict[str, str]], analysis_type: str, language: str = "日本語") -> str:
        """AI分析を実行してインサイトを生成"""
        if not data:
            return "分析対象のデータがありません。"
        
        # データをフォーマット
        formatted_data = self._format_data_for_analysis(data)
        
        # 履歴を使用する場合
        if self._enable_history and self._history:
            logger.info("過去の分析履歴を含めてAI分析を実行", "ai", analysis_type=analysis_type)
            # プロンプト作成
            prompt = self._create_analysis_prompt(formatted_data, analysis_type, language)
            # 履歴を含むメッセージ配列を取得
            messages = self._history.get_conversation_history(analysis_type, prompt)
            logger.debug("履歴メッセージ構成完了", "ai", message_count=len(messages))
        else:
            logger.info("履歴なしで新規AI分析を実行", "ai", analysis_type=analysis_type, language=language)
            # プロンプト作成
            prompt = self._create_analysis_prompt(formatted_data, analysis_type, language)
            # 単一メッセージとして送信
            messages = [{"role": "user", "content": prompt}]

        logger.debug(f"言語設定 @ analyser.py, _generate_insights", "ai", language=language)
        logger.debug(f"作成したプロンプト: {prompt}")

        # AI分析実行
        try:
            logger.start("AI APIリクエスト送信", "ai", 
                        data_length=len(formatted_data), 
                        max_tokens=50000, 
                        message_count=len(messages))
            
            resp = self._client.responses.create(
                model="o4-mini",
                reasoning={"effort": "high"},
                input=messages,
                max_output_tokens=50000
            )
            
            logger.success("AI APIレスポンス受信", "ai")
            data_dict = resp.to_dict()
            logger.debug("レスポンス構造解析", "ai", response_keys=list(data_dict.keys()))
            
            # レスポンス構造をより詳細にログ出力
            if "output" in data_dict:
                logger.debug("アウトプットアイテム解析", "ai", item_count=len(data_dict['output']))
                for i, item in enumerate(data_dict["output"]):
                    logger.debug(f"アイテム{i}詳細", "ai", type=item.get('type'), keys=list(item.keys()))
            else:
                logger.error("レスポンスに'output'キーが存在しません", "ai", response=data_dict)
            
            message_block = next(
                (item for item in data_dict["output"] if item.get("type") == "message"),
                None
            )
            
            if not message_block:
                # より詳細なエラー情報を提供
                available_types = [item.get("type") for item in data_dict.get("output", [])]
                error_msg = f"メッセージブロックが見つかりません"
                logger.error(error_msg, "ai", 
                           available_types=available_types,
                           response_keys=list(data_dict.keys()))
                raise RuntimeError(f"{error_msg}。利用可能なタイプ: {available_types}")
            
            logger.debug("メッセージブロック発見", "ai", content_count=len(message_block.get('content', [])))
            
            if not message_block.get("content") or len(message_block["content"]) == 0:
                error_msg = "メッセージブロックにコンテンツが含まれていません"
                logger.error(error_msg, "ai", message_block_keys=list(message_block.keys()))
                raise RuntimeError(error_msg)
            
            insights = message_block["content"][0].get("text", "")
            logger.complete("AI分析処理", "ai", result_length=len(insights))
            
            # 履歴に保存
            if self._enable_history and self._history:
                data_summary = f"{len(data)}件のデータ（平均{sum(len(item.get('text', '')) for item in data) // len(data)}文字）"
                self._history.save_analysis(analysis_type, data_summary, insights)
                logger.debug("分析結果を履歴に保存", "ai")
            
            return insights
            
        except Exception as e:
            # 詳細なエラー情報を含める
            logger.error("AI分析処理でエラーが発生", "ai",
                        error_type=type(e).__name__,
                        error_message=str(e),
                        data_length=len(formatted_data),
                        analysis_type=analysis_type,
                        history_enabled=self._enable_history)
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
    
    def _create_analysis_prompt(self, formatted_data: str, analysis_type: str, language: str) -> str:

        logger.debug(f"言語設定 @ analyser.py, _create_analysis_prompt", "ai", language=language)

        """分析タイプに応じたプロンプトを作成"""
        if analysis_type == AnalysisTypes.DOMI:
            return DomiPrompts.create_prompt(formatted_data, self._user_name, language)
        elif analysis_type == AnalysisTypes.AGA:
            return AgaPrompts.create_prompt(formatted_data, self._user_name, language)
        else:
            # フォールバック用の基本プロンプト
            user_prefix = f"ユーザー「{self._user_name}」さんの" if self._user_name else ""
            base_prompt = f"以下の{user_prefix}データを分析してください：\n\n{formatted_data}\n\n"
            return base_prompt + "このデータの特徴と傾向を分析してレポートを作成してください。"


 
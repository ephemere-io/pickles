import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class AnalysisHistory:
    """AI分析履歴の管理を担当するクラス"""
    
    def __init__(self, history_file: str = "analysis_history.json", max_history: int = 10):
        self.history_file = history_file
        self.max_history = max_history
    
    def load_history(self) -> List[Dict]:
        """分析履歴を読み込む"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def save_analysis(self, analysis_type: str, data_summary: str, insights: str) -> None:
        """新しい分析結果を履歴に保存"""
        history = self.load_history()
        
        new_entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": analysis_type,
            "data_summary": data_summary,
            "insights": insights
        }
        
        history.append(new_entry)
        
        # 最大履歴数を超えた場合、古いものを削除
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        self._save_history(history)
    
    def get_conversation_history(self, analysis_type: str, current_data: str) -> List[Dict[str, str]]:
        """OpenAI APIのinput形式で履歴を返す"""
        history = self.load_history()
        messages = []
        
        # 同じ分析タイプの過去3回分の履歴を取得
        relevant_history = [
            entry for entry in history 
            if entry["analysis_type"] == analysis_type
        ][-3:]  # 最新3件
        
        # 過去の分析をcontextとして追加
        for entry in relevant_history:
            # 過去の分析データ
            messages.append({
                "role": "user",
                "content": f"以前の分析データ（{entry['timestamp'][:10]}）:\n{entry['data_summary']}"
            })
            # 過去の分析結果
            messages.append({
                "role": "assistant", 
                "content": entry["insights"]
            })
        
        # 現在の分析データを追加
        messages.append({
            "role": "user",
            "content": current_data
        })
        
        return messages
    
    def get_history_summary(self) -> Dict[str, int]:
        """履歴の統計情報を返す"""
        history = self.load_history()
        
        analysis_counts = {}
        for entry in history:
            analysis_type = entry["analysis_type"]
            analysis_counts[analysis_type] = analysis_counts.get(analysis_type, 0) + 1
        
        return {
            "total_analyses": len(history),
            "by_type": analysis_counts,
            "oldest": history[0]["timestamp"][:10] if history else None,
            "newest": history[-1]["timestamp"][:10] if history else None
        }
    
    def _save_history(self, history: List[Dict]) -> None:
        """履歴をファイルに保存"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"⚠️ 履歴保存エラー: {e}")
    
    def clear_history(self) -> None:
        """履歴をクリア"""
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
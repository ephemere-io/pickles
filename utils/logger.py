import json
from datetime import datetime
from typing import Dict, Any, Optional

class Logger:
    """シンプルで分析しやすい単一クラスLogger"""
    
    # レベルと文字のマッピング
    LEVEL_TEXTS = {
        "DEBUG": "DEBUG:",
        "INFO": "INFO:", 
        "WARNING": "WARN:",
        "ERROR": "ERROR:",
        "SUCCESS": "SUCCESS:"
    }
    
    # カテゴリと絵文字のマッピング
    CATEGORY_EMOJIS = {
        "system": "🥒",
        "data": "📊", 
        "ai": "🤖",
        "api": "🔗",
        "email": "📧",
        "file": "📁",
        "db": "💾",
        "network": "🌐",
        "security": "🔒",
        "performance": "⚡",
        "notion": "📋",
        "sheets": "📈",
        "execution": "🔄",
        "scheduler": "⏰"
    }
    
    def __init__(self, json_output: bool = False):
        """
        Args:
            json_output: Trueならログを構造化JSON形式でも出力
        """
        self.json_output = json_output
    
    def _log(self, level: str, category: str, message: str, extra_data: Dict[str, Any]):
        """内部ログメソッド"""
        timestamp = datetime.now()
        
        # 構造化データ
        log_data = {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "category": category,
            "message": message,
            **extra_data
        }
        
        # JSON出力（分析用）
        if self.json_output:
            print(json.dumps(log_data, ensure_ascii=False))
        
        # 人間が読みやすい出力
        level_text = self.LEVEL_TEXTS.get(level, "INFO")
        category_emoji = self.CATEGORY_EMOJIS.get(category, "📋")
        
        time_str = timestamp.strftime("%H:%M:%S")
        human_readable = f"{level_text} {category_emoji} [{time_str}] {message}"
        
        # 追加データがあれば表示
        if extra_data:
            details = ", ".join(f"{k}={v}" for k, v in extra_data.items())
            human_readable += f" ({details})"
        
        print(human_readable)
    
    # === 基本ログメソッド ===
    def debug(self, message: str, category: str = "system", **kwargs):
        self._log("DEBUG", category, message, kwargs)
    
    def info(self, message: str, category: str = "system", **kwargs):
        self._log("INFO", category, message, kwargs)
    
    def warning(self, message: str, category: str = "system", **kwargs):
        self._log("WARNING", category, message, kwargs)
    
    def error(self, message: str, category: str = "system", **kwargs):
        self._log("ERROR", category, message, kwargs)
    
    def success(self, message: str, category: str = "system", **kwargs):
        self._log("SUCCESS", category, message, kwargs)
    
    # === よく使うパターンのメソッド ===
    def start(self, what: str, category: str = "system", **kwargs):
        """開始ログ"""
        self.info(f"{what}開始", category, **kwargs)
    
    def complete(self, what: str, category: str = "system", count: Optional[int] = None, **kwargs):
        """完了ログ"""
        message = f"{what}完了"
        if count is not None:
            kwargs["count"] = count
        self.success(message, category, **kwargs)
    
    def failed(self, what: str, reason: str = "", category: str = "system", **kwargs):
        """失敗ログ"""
        message = f"{what}失敗"
        if reason:
            kwargs["reason"] = reason
        self.error(message, category, **kwargs)


# グローバルインスタンス（便利のため）
logger = Logger()
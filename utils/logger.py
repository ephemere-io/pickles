from typing import List, Dict

class Logger:
    """ログ出力を担当するクラス"""
    
    @staticmethod
    def log_start(data_source: str, days: int) -> None:
        print(f"📥 データ取得中... (ソース: {data_source}, 期間: {days}日)")
    
    @staticmethod
    def log_data_fetched(count: int) -> None:
        print(f"✅ {count}件のデータを取得しました")
    
    @staticmethod
    def log_no_data() -> None:
        print("⚠️  取得データが0件です。")
    
    @staticmethod
    def log_analysis_start(analysis_type: str) -> None:
        print(f"🔄 分析処理中... (タイプ: {analysis_type})")
    
    @staticmethod
    def log_analysis_complete(data_count: int) -> None:
        print(f"✅ 分析完了 (対象データ: {data_count}件)")
    
    @staticmethod
    def log_delivery_start(delivery_methods: List[str]) -> None:
        print(f"📤 レポート配信中... (方法: {delivery_methods})")
    
    @staticmethod
    def log_delivery_complete() -> None:
        print("✅ 配信完了")
    
    @staticmethod
    def log_error(error_message: str) -> None:
        print(f"❌ エラー: {error_message}")
    
    @staticmethod
    def log_system_start() -> None:
        print("🥒 Pickles Personal Insight Analytics System")
        print("=" * 50)
    
    @staticmethod
    def log_results(results: Dict[str, str]) -> None:
        print("\n" + "=" * 50)
        print("📋 実行結果:")
        for method, result in results.items():
            print(f"  {method}: {result}")
    
    @staticmethod
    def log_scheduler_start(cron_day: str, cron_hour: int, cron_minute: int) -> None:
        print(f"⏰ スケジューラー開始: 毎週{cron_day}曜日 {cron_hour:02d}:{cron_minute:02d} JST")


 
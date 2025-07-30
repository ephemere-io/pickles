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
    
    # 汎用デバッグログメソッド
    @staticmethod
    def log_debug(message: str) -> None:
        print(f"🔍 {message}")
    
    @staticmethod
    def log_info(message: str) -> None:
        print(f"ℹ️  {message}")
    
    @staticmethod
    def log_warning(message: str) -> None:
        print(f"⚠️  {message}")
    
    @staticmethod
    def log_error_detail(message: str, details: Dict = None) -> None:
        print(f"💥 {message}")
        if details:
            print(f"🔎 詳細: {details}")
    
    # AI分析関連の特化ログ
    @staticmethod
    def log_ai_request(message: str) -> None:
        print(f"🤖 {message}")
    
    @staticmethod
    def log_ai_response(message: str) -> None:
        print(f"📨 {message}")
    
    @staticmethod
    def log_ai_processing(message: str) -> None:
        print(f"⚙️  {message}")
    
    @staticmethod
    def log_ai_success(message: str) -> None:
        print(f"🎉 {message}")
    
    @staticmethod
    def log_ai_error(message: str, details: Dict = None) -> None:
        print(f"🚨 {message}")
        if details:
            print(f"🔎 詳細: {details}")
    
    # メール送信関連のログ
    @staticmethod
    def log_email_start(to_email: str, subject: str, from_email: str, smtp_info: str) -> None:
        print(f"📧 HTMLメール送信開始: {to_email}")
        print(f"   件名: {subject}")
        print(f"   送信元: {from_email}")
        print(f"   SMTPサーバー: {smtp_info}")
    
    @staticmethod
    def log_email_progress(message: str) -> None:
        print(f"   {message}")
    
    @staticmethod
    def log_email_success(to_email: str) -> None:
        print(f"   ✅ メール送信成功: {to_email}")
    
    @staticmethod
    def log_email_error(error: str) -> None:
        print(f"   ❌ メール送信エラー: {error}")
    
    # Google Sheets関連のログ
    @staticmethod
    def log_sheets_reading(spreadsheet_id: str) -> None:
        print(f"📊 スプレッドシート {spreadsheet_id} からユーザーデータを読み込み中...")
    
    @staticmethod
    def log_sheets_user_added(user_name: str, email: str, api_key_info: str = None) -> None:
        if api_key_info:
            print(f"   📝 APIキー: {api_key_info}")
        print(f"✅ ユーザー追加: {user_name} ({email})")
    
    @staticmethod
    def log_sheets_summary(user_count: int) -> None:
        print(f"📊 合計{user_count}人のユーザーデータを読み込みました")
    
    @staticmethod
    def log_sheets_error(error: str) -> None:
        print(f"❌ Google Sheets API エラー: {error}")
    
    # 実行プロセス関連のログ
    @staticmethod
    def log_execution_start(user_name: str) -> None:
        print(f"🚀 {user_name} の分析を開始...")
    
    @staticmethod
    def log_execution_complete(user_name: str) -> None:
        print(f"✅ {user_name} の分析が完了しました")
    
    @staticmethod
    def log_execution_error(user_name: str) -> None:
        print(f"❌ {user_name} の分析でエラーが発生:")
    
    @staticmethod
    def log_execution_timeout(user_name: str) -> None:
        print(f"⏰ {user_name} の分析がタイムアウトしました")
    
    @staticmethod
    def log_execution_log(log_content: str) -> None:
        print("📋 実行ログ:")
        print(log_content)
    
    # Notion API関連のログ
    @staticmethod
    def log_notion_api_key(api_key_info: str) -> None:
        print(f"🔑 NotionInput: APIキー設定済み ({api_key_info})")
    
    @staticmethod
    def log_notion_no_api_key() -> None:
        print("⚠️ NotionInput: APIキーが設定されていません")


 
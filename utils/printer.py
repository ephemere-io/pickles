from types import SimpleNamespace

# TypeScriptのオブジェクトのような定数定義
CommandArgs = SimpleNamespace(
    SOURCE="--source",
    ANALYSIS="--analysis",
    DELIVERY="--delivery",
    DAYS="--days",
    HELP="--help",
    USER_NAME="--user-name",
    EMAIL_TO="--email-to",
    NOTION_API_KEY="--notion-api-key",
    GDOCS_URL="--gdocs-url",
    LANGUAGE="--language"
)

DataSources = SimpleNamespace(
    NOTION="notion",
    GDOCS="gdocs"
)

AnalysisTypes = SimpleNamespace(
    DOMI="domi",
    AGA="aga"
)

DeliveryMethods = SimpleNamespace(
    CONSOLE="console",
    EMAIL_TEXT="email_text",
    EMAIL_HTML="email_html",
    FILE_TEXT="file_text",
    FILE_HTML="file_html"
)


class UsagePrinter:
    """使用方法表示を担当するクラス"""
    
    @staticmethod
    def print_usage() -> None:
        usage = f"""
🥒 Pickles - Personal Insight Analytics System

使用方法: uv run python main.py [オプション]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 基本オプション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {CommandArgs.SOURCE} <source>     データソース
                                    • {DataSources.NOTION} (デフォルト)
                                    • {DataSources.GDOCS}
  
  {CommandArgs.ANALYSIS} <type>      分析タイプ
                                    • {AnalysisTypes.DOMI} (デフォルト)
                                    • {AnalysisTypes.AGA}
  
  {CommandArgs.DELIVERY} <method>    配信方法
                                    • {DeliveryMethods.CONSOLE} (デフォルト)
                                    • {DeliveryMethods.EMAIL_HTML}
                                    • {DeliveryMethods.EMAIL_TEXT}
                                    • {DeliveryMethods.FILE_HTML}
                                    • {DeliveryMethods.FILE_TEXT}
  
  {CommandArgs.DAYS} <number>        分析日数 (デフォルト: 7)
                                    7日超でコンテキスト分析実行
  
  {CommandArgs.LANGUAGE} <lang>      出力言語 (デフォルト: english)
                                    • japanese
                                    • english
  
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 指定実行設定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {CommandArgs.USER_NAME} <name>     ユーザー名
  {CommandArgs.EMAIL_TO} <email>     送信先メールアドレス
  {CommandArgs.NOTION_API_KEY} <key> Notion APIキー (--source notion時)
  {CommandArgs.GDOCS_URL} <url>      Google Docs URL (--source gdocs時)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕒 その他
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {CommandArgs.HELP}                 このヘルプを表示

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 よく使う例
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 基本実行 (Notion + DOMI分析 + コンソール出力)
uv run python main.py

# 英語でメール送信
uv run python main.py --delivery email_html --language english

# Google Docsから7日分分析
uv run python main.py --source gdocs --gdocs-url "https://docs.google.com/document/d/DOC_ID"

# 30日コンテキストでAGA分析
uv run python main.py --analysis aga --days 30

# 指定実行（Notion）
uv run python main.py --user-name "田中太郎" --email-to "tanaka@example.com" --notion-api-key "secret_xxx"

# 指定実行（Google Docs）
uv run python main.py --source gdocs --gdocs-url "https://docs.google.com/document/d/DOC_ID" --user-name "田中太郎"
        """
        print(usage) 
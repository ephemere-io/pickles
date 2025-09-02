from types import SimpleNamespace

# TypeScriptのオブジェクトのような定数定義
CommandArgs = SimpleNamespace(
    SOURCE="--source",
    ANALYSIS="--analysis",
    DELIVERY="--delivery",
    DAYS="--days",
    SCHEDULE="--schedule",
    HISTORY="--history",
    HELP="--help",
    USER_NAME="--user-name",
    EMAIL_TO="--email-to",
    NOTION_API_KEY="--notion-api-key",
    LANGUAGE="--language"
)

DataSources = SimpleNamespace(
    NOTION="notion"
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

使用方法:
  python main.py [オプション]

オプション:
  {CommandArgs.SOURCE}         データソース ({DataSources.NOTION})
  {CommandArgs.ANALYSIS}       分析タイプ ({AnalysisTypes.DOMI} | {AnalysisTypes.AGA})
  {CommandArgs.DELIVERY}       配信方法 ({DeliveryMethods.CONSOLE},{DeliveryMethods.EMAIL_TEXT},{DeliveryMethods.EMAIL_HTML},{DeliveryMethods.FILE_TEXT},{DeliveryMethods.FILE_HTML})
  {CommandArgs.DAYS}          分析日数 (最小: 7, デフォルト: 7)
                              7日より多い場合、コンテキスト分析を実行
  {CommandArgs.HISTORY}       分析履歴使用 (on | off, デフォルト: on)
  {CommandArgs.SCHEDULE}      定期実行モード
  {CommandArgs.USER_NAME}     ユーザー名 (マルチユーザー対応)
  {CommandArgs.EMAIL_TO}      送信先メールアドレス (マルチユーザー対応)
  {CommandArgs.NOTION_API_KEY} Notion APIキー (マルチユーザー対応)
  {CommandArgs.LANGUAGE}      言語設定 (マルチユーザー対応)
  {CommandArgs.HELP}          このヘルプを表示

例:
  python main.py                                                                # デフォルト: {DataSources.NOTION}
  python main.py {CommandArgs.SOURCE} {DataSources.NOTION} {CommandArgs.ANALYSIS} {AnalysisTypes.DOMI}
  python main.py {CommandArgs.SOURCE} {DataSources.NOTION} {CommandArgs.ANALYSIS} {AnalysisTypes.AGA}
  python main.py {CommandArgs.DELIVERY} {DeliveryMethods.CONSOLE},{DeliveryMethods.FILE_HTML} {CommandArgs.DAYS} 14
  python main.py {CommandArgs.HISTORY} off                                      # 履歴なしで分析
  python main.py {CommandArgs.SCHEDULE}
  python main.py {CommandArgs.DAYS} 30                                          # 30日間のコンテキストで分析
  python main.py {CommandArgs.ANALYSIS} {AnalysisTypes.DOMI} {CommandArgs.DAYS} 14  # DOMI分析を14日間コンテキストで実行
  
マルチユーザー例:
  python main.py {CommandArgs.USER_NAME} "田中太郎" {CommandArgs.EMAIL_TO} "tanaka@example.com" {CommandArgs.NOTION_API_KEY} "secret_xxx"
  python read_spreadsheet_and_execute.py --spreadsheet-id "1ABC...XYZ" --analysis {AnalysisTypes.DOMI} --delivery {DeliveryMethods.EMAIL_HTML} --language {CommandArgs.LANGUAGE}
        """
        print(usage) 
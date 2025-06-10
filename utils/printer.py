from types import SimpleNamespace

# TypeScriptのオブジェクトのような定数定義
CommandArgs = SimpleNamespace(
    SOURCE="--source",
    ANALYSIS="--analysis",
    DELIVERY="--delivery",
    DAYS="--days",
    SCHEDULE="--schedule",
    HELP="--help"
)

DataSources = SimpleNamespace(
    DATABASE_ENTRIES="database_entries",
    RECENT_DOCUMENTS="recent_documents"
)

AnalysisTypes = SimpleNamespace(
    COMPREHENSIVE="comprehensive",
    EMOTIONAL="emotional",
    PRODUCTIVITY="productivity"
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
  {CommandArgs.SOURCE}         データソース ({DataSources.DATABASE_ENTRIES} | {DataSources.RECENT_DOCUMENTS})
  {CommandArgs.ANALYSIS}       分析タイプ ({AnalysisTypes.COMPREHENSIVE} | {AnalysisTypes.EMOTIONAL} | {AnalysisTypes.PRODUCTIVITY})
  {CommandArgs.DELIVERY}       配信方法 ({DeliveryMethods.CONSOLE},{DeliveryMethods.EMAIL_TEXT},{DeliveryMethods.EMAIL_HTML},{DeliveryMethods.FILE_TEXT},{DeliveryMethods.FILE_HTML})
  {CommandArgs.DAYS}          取得日数 (デフォルト: 7)
  {CommandArgs.SCHEDULE}      定期実行モード
  {CommandArgs.HELP}          このヘルプを表示

例:
  python main.py                                                                # デフォルト: {DataSources.DATABASE_ENTRIES}
  python main.py {CommandArgs.SOURCE} {DataSources.RECENT_DOCUMENTS} {CommandArgs.ANALYSIS} {AnalysisTypes.COMPREHENSIVE}
  python main.py {CommandArgs.DELIVERY} {DeliveryMethods.CONSOLE},{DeliveryMethods.FILE_HTML} {CommandArgs.DAYS} 14
  python main.py {CommandArgs.SCHEDULE}
        """
        print(usage) 
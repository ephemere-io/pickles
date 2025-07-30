#!/usr/bin/env python3
"""
Pickles - Personal Insight Analytics System

Input-Throughput-Output アーキテクチャによる
日々の感情と思考の分析システム
"""

import sys
from typing import List, Dict
from functools import partial
from apscheduler.schedulers.blocking import BlockingScheduler

# 各コンポーネントのインポート
from inputs import NotionInput, NotionInputError
from throughput import DocumentAnalyzer, AnalysisError
from outputs import ReportDelivery, OutputError
from utils import Logger, UsagePrinter, CommandArgs, DataSources, AnalysisTypes, DeliveryMethods


class PicklesSystem:
    """Picklesシステムメインクラス"""
    
    def __init__(self, user_config: Dict[str, str] = None, enable_history: bool = True):
        # user_configから各種設定を取得
        notion_api_key = user_config.get('notion_api_key') if user_config else None
        email_config = {
            'email_to': user_config.get('email_to'),
            'user_name': user_config.get('user_name')
        } if user_config and user_config.get('email_to') else None
        
        user_name = user_config.get('user_name') if user_config else None
        
        self._notion_input = NotionInput(api_key=notion_api_key)
        self._analyzer = DocumentAnalyzer(enable_history=enable_history, user_name=user_name)
        self._delivery = ReportDelivery(email_config=email_config)
        self._logger = Logger()
        
    def run_analysis(self, 
                    data_source: str = "notion",
                    analysis_type: str = "comprehensive",
                    delivery_methods: List[str] = None,
                    days: int = 7) -> Dict[str, str]:
        """分析を実行してレポートを生成・配信"""
        
        if delivery_methods is None:
            delivery_methods = ["console"]
        
        # バリデーション
        if data_source != DataSources.NOTION:
            return {"error": f"未対応のデータソース: {data_source}"}

        try:
            # データ取得
            self._logger.log_start(data_source, days)
            raw_data = self._fetch_data(data_source, days)
            
            if not raw_data:
                self._logger.log_no_data()
                return {"error": "データが見つかりませんでした"}
            
            self._logger.log_data_fetched(len(raw_data))
            
            # 分析実行
            self._logger.log_analysis_start(analysis_type)
            analysis_result = self._analyzer.analyze_documents(
                raw_data, 
                analysis_type=analysis_type,
                apply_filters=True
            )
            self._logger.log_analysis_complete(analysis_result['data_count'])
            
            # レポート配信
            self._logger.log_delivery_start(delivery_methods)
            delivery_results = self._delivery.deliver_report(
                analysis_result,
                delivery_methods=delivery_methods,
                report_format="comprehensive"
            )
            self._logger.log_delivery_complete()
            
            return delivery_results
            
        except (NotionInputError, AnalysisError, OutputError) as e:
            error_msg = str(e)
            self._logger.log_error(error_msg)
            return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            self._logger.log_error(error_msg)
            return {"error": error_msg}
    
    def _fetch_data(self, data_source: str, days: int) -> List[Dict[str, str]]:
        """データ取得"""
        if data_source == DataSources.NOTION:
            return self._notion_input.fetch_notion_documents(days)
        else:
            raise ValueError(f"未対応のデータソース: {data_source}")
    
    def _parse_command_args(self, args: List[str]) -> Dict[str, any]:
        """コマンドライン引数を解析"""
        default_args = {
            "source": DataSources.NOTION,
            "analysis": AnalysisTypes.DOMI, 
            "delivery": [DeliveryMethods.CONSOLE],
            "days": 7,
            "history": True,
            "schedule": False,
            "user_name": None,
            "email_to": None,
            "notion_api_key": None
        }
        
        parsed_args = default_args.copy()
        i = 1
        
        while i < len(args):
            arg = args[i]
            
            if arg == CommandArgs.HELP:
                return {"help": True}
            elif arg == CommandArgs.SOURCE and i + 1 < len(args):
                parsed_args["source"] = args[i + 1]
                i += 1
            elif arg == CommandArgs.ANALYSIS and i + 1 < len(args):
                parsed_args["analysis"] = args[i + 1]
                i += 1
            elif arg == CommandArgs.DELIVERY and i + 1 < len(args):
                parsed_args["delivery"] = args[i + 1].split(",")
                i += 1
            elif arg == CommandArgs.DAYS and i + 1 < len(args):
                parsed_args["days"] = int(args[i + 1])
                i += 1
            elif arg == CommandArgs.HISTORY and i + 1 < len(args):
                parsed_args["history"] = args[i + 1].lower() == "on"
                i += 1
            elif arg == CommandArgs.SCHEDULE:
                parsed_args["schedule"] = True
            elif arg == CommandArgs.USER_NAME and i + 1 < len(args):
                parsed_args["user_name"] = args[i + 1]
                i += 1
            elif arg == CommandArgs.EMAIL_TO and i + 1 < len(args):
                parsed_args["email_to"] = args[i + 1]
                i += 1
            elif arg == CommandArgs.NOTION_API_KEY and i + 1 < len(args):
                parsed_args["notion_api_key"] = args[i + 1]
                i += 1
            
            i += 1
        
        return parsed_args
    
    def schedule_job(self, 
                    cron_day: str = "mon", 
                    cron_hour: int = 7, 
                    cron_minute: int = 0) -> None:
        """定期実行をスケジュール"""
        scheduler = BlockingScheduler(timezone="Asia/Tokyo")
        
        # デフォルト設定で週次実行
        default_analysis = partial(
            self.run_analysis,
            data_source=DataSources.NOTION,
            analysis_type=AnalysisTypes.DOMI,
            delivery_methods=[DeliveryMethods.CONSOLE, DeliveryMethods.EMAIL_TEXT],
            days=7
        )
        
        scheduler.add_job(
            default_analysis,
            trigger="cron", 
            day_of_week=cron_day, 
            hour=cron_hour, 
            minute=cron_minute
        )
        
        self._logger.log_scheduler_start(cron_day, cron_hour, cron_minute)
        scheduler.start()


def main() -> None:
    """メイン関数"""
    logger = Logger()
    usage_printer = UsagePrinter()
    
    # 引数を事前に解析して履歴設定を取得
    temp_system = PicklesSystem()  # 一時的なインスタンス
    args = temp_system._parse_command_args(sys.argv)
    
    if args.get("help"):
        usage_printer.print_usage()
        sys.exit(0)
    
    # ユーザー設定の構築
    user_config = None
    if args.get("user_name") or args.get("email_to") or args.get("notion_api_key"):
        user_config = {
            'user_name': args.get("user_name"),
            'email_to': args.get("email_to"),
            'notion_api_key': args.get("notion_api_key")
        }
    
    # システムを初期化
    system = PicklesSystem(user_config=user_config, enable_history=args["history"])
    
    logger.log_system_start()
    if args["history"]:
        logger.log_info("分析履歴機能: 有効")
    else:
        logger.log_info("分析履歴機能: 無効")
    
    if args["schedule"]:
        # スケジュール実行モード
        system.schedule_job()
    else:
        # 即座に実行モード
        results = system.run_analysis(
            data_source=args["source"],
            analysis_type=args["analysis"],
            delivery_methods=args["delivery"],
            days=args["days"]
        )
        
        logger.log_results(results)


if __name__ == "__main__":
    main()
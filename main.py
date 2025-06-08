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
    
    def __init__(self):
        self._notion_input = NotionInput()
        self._analyzer = DocumentAnalyzer()
        self._delivery = ReportDelivery()
        self._logger = Logger()
        
    def run_analysis(self, 
                    data_source: str = "database_entries",
                    analysis_type: str = "comprehensive",
                    delivery_methods: List[str] = None,
                    days: int = 7) -> Dict[str, str]:
        """分析を実行してレポートを生成・配信"""
        
        if delivery_methods is None:
            delivery_methods = ["console"]
        
        # バリデーション
        valid_sources = {DataSources.DATABASE_ENTRIES, DataSources.RECENT_DOCUMENTS}
        if data_source not in valid_sources:
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
        if data_source == DataSources.DATABASE_ENTRIES:
            return self._notion_input.fetch_database_entries(days)
        elif data_source == DataSources.RECENT_DOCUMENTS:
            return self._notion_input.fetch_recent_documents(days)
        else:
            raise ValueError(f"未対応のデータソース: {data_source}")
    
    def _parse_command_args(self, args: List[str]) -> Dict[str, any]:
        """コマンドライン引数を解析"""
        default_args = {
            "source": DataSources.DATABASE_ENTRIES,
            "analysis": AnalysisTypes.COMPREHENSIVE, 
            "delivery": [DeliveryMethods.CONSOLE],
            "days": 7,
            "schedule": False
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
            elif arg == CommandArgs.SCHEDULE:
                parsed_args["schedule"] = True
            
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
            data_source=DataSources.DATABASE_ENTRIES,
            analysis_type=AnalysisTypes.COMPREHENSIVE,
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
    system = PicklesSystem()
    
    logger.log_system_start()
    
    args = system._parse_command_args(sys.argv)
    
    if args.get("help"):
        usage_printer.print_usage()
        sys.exit(0)
    
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
#!/usr/bin/env python3
"""
Pickles - Personal Insight Analytics System

Input-Throughput-Output アーキテクチャによる
日々の感情と思考の分析システム
"""

import os
import sys
from typing import List, Dict
from functools import partial
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

# 各コンポーネントのインポート
from inputs import NotionInput, NotionInputError, GdocsInput, GdocsInputError
from throughput import DocumentAnalyzer, AnalysisError
from outputs import ReportDelivery, OutputError
from utils import logger, UsagePrinter, CommandArgs, DataSources, AnalysisTypes, DeliveryMethods


class PicklesSystem:
    """Picklesシステムメインクラス"""
    
    def __init__(self, user_config: Dict[str, str] = None, enable_history: bool = True):
        # user_configから各種設定を取得
        notion_api_key = user_config.get('notion_api_key') if user_config else None
        gdocs_url = user_config.get('gdocs_url') if user_config else None
        email_config = {
            'email_to': user_config.get('email_to'),
            'user_name': user_config.get('user_name')
        } if user_config and user_config.get('email_to') else None
        
        user_name = user_config.get('user_name') if user_config else None

        language = user_config.get('language') if user_config else None


        self._notion_input = NotionInput(api_key=notion_api_key)
        self._gdocs_url = gdocs_url
        self._analyzer = DocumentAnalyzer(enable_history=enable_history, user_name=user_name, language=language)
        self._delivery = ReportDelivery(email_config=email_config)
        # グローバルloggerインスタンスを使用
        
    def run_analysis(self, 
                    data_source: str = "notion",
                    analysis_type: str = "comprehensive",
                    delivery_methods: List[str] = None,
                    language: str = None,
                    days: int = 7) -> Dict[str, str]:
        """分析を実行してレポートを生成・配信
        
        Args:
            data_source: データソース
            analysis_type: 分析タイプ
            delivery_methods: 配信方法
            language: 出力言語
            days: 分析対象日数（最小7日）
        """
        

        if delivery_methods is None:
            delivery_methods = ["console"]
        
        # バリデーション
        if data_source not in [DataSources.NOTION, DataSources.GDOCS]:
            return {"error": f"未対応のデータソース: {data_source}"}
        
        # Google Docsの場合はURLが必要（コマンドライン引数または.env）
        if data_source == DataSources.GDOCS and not self._gdocs_url:
            return {"error": "Google Docsを使用する場合は--gdocs-urlでURLを指定するか、.envにGOOGLE_DOCS_URLを設定してください"}
        
        # daysの最小値チェック
        if days < 7:
            logger.error("分析日数が最小値未満", "system", days=days, minimum=7)
            return {"error": "分析日数は最低7日必要です"}

        try:
            # コンテキスト用データ取得（days > 7の場合）
            context_data = None
            week_data = None
            
            if days > 7:
                # コンテキスト分析用にdays日分のデータを取得
                logger.start(f"{data_source}からの{days}日間データ取得（コンテキスト用）", "data", days=days)
                context_data = self._fetch_data(data_source, days)
                
                if not context_data:
                    logger.warning("コンテキストデータが見つかりません", "data", source=data_source, days=days)
                    return {"error": "データが見つかりませんでした"}
                
                logger.success("コンテキストデータ取得完了", "data", count=len(context_data), source=data_source)
                
                # 直近7日分のデータも取得
                logger.start(f"{data_source}からの直近7日間データ取得", "data", days=7)
                week_data = self._fetch_data(data_source, 7)
                
                if not week_data:
                    logger.warning("直近7日間のデータが見つかりません", "data", source=data_source)
                    # フォールバック: context_dataから直近7日分を正しく抽出
                    week_data = self._extract_recent_days_from_context(context_data, 7)
                
                logger.success("直近7日間データ取得完了", "data", count=len(week_data), source=data_source)
            else:
                # days == 7の場合は通常の処理
                logger.start(f"{data_source}からのデータ取得", "data", days=days)
                raw_data = self._fetch_data(data_source, days)
                
                if not raw_data:
                    logger.warning("データが見つかりません", "data", source=data_source, days=days)
                    return {"error": "データが見つかりませんでした"}
                
                logger.success("データ取得完了", "data", count=len(raw_data), source=data_source)
                week_data = raw_data
            
            # 分析実行
            if days > 7:
                logger.start(f"{analysis_type}分析処理（{days}日間コンテキスト付き）", "ai", 
                           week_count=len(week_data), context_count=len(context_data))
                analysis_result = self._analyzer.analyze_documents(
                    week_data,
                    analysis_type=analysis_type,
                    apply_filters=True,
                    language=language,
                    context_data=context_data
                )
            else:
                logger.start(f"{analysis_type}分析処理", "ai", data_count=len(week_data))
                analysis_result = self._analyzer.analyze_documents(
                    week_data,
                    analysis_type=analysis_type,
                    apply_filters=True,
                    language=language
                )
            
            logger.complete(f"{analysis_type}分析処理", "ai", analyzed_count=analysis_result['data_count'])

            # レポート配信
            logger.start("レポート配信処理", "system", methods=delivery_methods)
            delivery_results = self._delivery.deliver_report(
                analysis_result,
                delivery_methods=delivery_methods,
                report_format="comprehensive"
            )
            logger.complete("レポート配信処理", "system", method_count=len(delivery_methods))
            
            return delivery_results
            
        except (NotionInputError, GdocsInputError, AnalysisError, OutputError) as e:
            error_msg = str(e)
            logger.error("アプリケーションエラー", "system", error_type=type(e).__name__, details=error_msg)
            return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"予期しないエラー: {e}"
            logger.error("予期しないエラー", "system", error_type=type(e).__name__, details=str(e))
            return {"error": error_msg}
    
    def _fetch_data(self, data_source: str, days: int) -> List[Dict[str, str]]:
        """データ取得"""
        if data_source == DataSources.NOTION:
            return self._notion_input.fetch_notion_documents(days)
        elif data_source == DataSources.GDOCS:
            return GdocsInput().fetch_gdocs_documents(self._gdocs_url, days)
        else:
            raise ValueError(f"未対応のデータソース: {data_source}")
    
    def _extract_recent_days_from_context(self, context_data: List[Dict[str, str]], days: int) -> List[Dict[str, str]]:
        """コンテキストデータから直近N日分のデータを正しく抽出
        
        日付でソートし、最新のN日分のデータを返す。
        日付が欠落している場合は除外する。
        """
        from datetime import datetime, timedelta
        
        # 日付が存在するデータのみをフィルタリング
        data_with_dates = [d for d in context_data if d.get('date')]
        
        if not data_with_dates:
            logger.warning("日付情報を持つデータがありません", "data")
            return context_data[:days] if len(context_data) > days else context_data
        
        # 日付でソート（新しい順）
        try:
            sorted_data = sorted(
                data_with_dates,
                key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'),
                reverse=True
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"日付のパース中にエラー: {e}", "data")
            # フォールバック: 元の順序で最初のN件を返す
            return data_with_dates[:days] if len(data_with_dates) > days else data_with_dates
        
        # 最新の日付を基準に、直近N日間の範囲を計算
        if sorted_data:
            try:
                latest_date = datetime.strptime(sorted_data[0]['date'], '%Y-%m-%d')
                cutoff_date = latest_date - timedelta(days=days-1)
                
                # 直近N日間のデータのみを抽出
                recent_data = [
                    d for d in sorted_data
                    if datetime.strptime(d['date'], '%Y-%m-%d') >= cutoff_date
                ]
                
                # 古い順（昇順）に並び替えて返す
                recent_data.reverse()
                
                logger.info(f"コンテキストから{len(recent_data)}件の直近データを抽出", "data",
                          latest_date=latest_date.strftime('%Y-%m-%d'),
                          cutoff_date=cutoff_date.strftime('%Y-%m-%d'))
                
                return recent_data
            except (ValueError, KeyError) as e:
                logger.warning(f"日付範囲の計算中にエラー: {e}", "data")
        
        # 最終フォールバック: ソート済みデータの最初のN件を返す
        result = sorted_data[:days] if len(sorted_data) > days else sorted_data
        # 古い順（昇順）に並び替えて返す
        result.reverse()
        return result
    
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
            "notion_api_key": None,
            "gdocs_url": None,
            "language": None,
            "month_context": False
        }
        
        parsed_args = default_args.copy()
        i = 1
        
        while i < len(args):
            arg = args[i]
            
            if arg == CommandArgs.HELP:
                return {"help": True}
            elif arg == CommandArgs.SOURCE and i + 1 < len(args):
                source_value = args[i + 1]
                valid_data_sources = [DataSources.NOTION, DataSources.GDOCS]
                if source_value not in valid_data_sources:
                    logger.error("無効なデータソース", "system", value=source_value, 
                               valid_values=valid_data_sources)
                    sys.exit(1)
                parsed_args["source"] = source_value
                i += 1
            elif arg == CommandArgs.ANALYSIS and i + 1 < len(args):
                analysis_value = args[i + 1]
                valid_analysis_types = [AnalysisTypes.DOMI, AnalysisTypes.AGA]
                if analysis_value not in valid_analysis_types:
                    logger.error("無効な分析タイプ", "system", value=analysis_value,
                               valid_values=valid_analysis_types)
                    sys.exit(1)
                parsed_args["analysis"] = analysis_value
                i += 1
            elif arg == CommandArgs.DELIVERY and i + 1 < len(args):
                delivery_values = args[i + 1].split(",")
                valid_delivery_methods = [
                    DeliveryMethods.CONSOLE, DeliveryMethods.EMAIL_TEXT,
                    DeliveryMethods.EMAIL_HTML, DeliveryMethods.FILE_TEXT,
                    DeliveryMethods.FILE_HTML
                ]
                for delivery_value in delivery_values:
                    if delivery_value not in valid_delivery_methods:
                        logger.error("無効な配信方法", "system", value=delivery_value,
                                   valid_values=valid_delivery_methods)
                        sys.exit(1)
                parsed_args["delivery"] = delivery_values
                i += 1
            elif arg == CommandArgs.DAYS and i + 1 < len(args):
                days_value = int(args[i + 1])
                if days_value < 7:
                    logger.error("無効な日数指定", "system", value=days_value, minimum=7)
                    print("エラー: 分析日数は最低7日必要です")
                    sys.exit(1)
                parsed_args["days"] = days_value
                i += 1
            elif arg == CommandArgs.HISTORY and i + 1 < len(args):
                history_value = args[i + 1].lower()
                valid_history_values = ["on", "off"]
                if history_value not in valid_history_values:
                    logger.error("無効な履歴オプション", "system", value=history_value,
                                valid_values=valid_history_values)
                    sys.exit(1)
                parsed_args["history"] = history_value == "on"
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
            elif arg == CommandArgs.GDOCS_URL and i + 1 < len(args):
                parsed_args["gdocs_url"] = args[i + 1]
                i += 1
            elif arg == CommandArgs.LANGUAGE and i + 1 < len(args):
                parsed_args["language"] = args[i + 1]
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
        
        logger.info("スケジューラー開始", "scheduler", day=cron_day, hour=cron_hour, minute=cron_minute)
        scheduler.start()


def parse_command_args(args: List[str]) -> Dict[str, any]:
    """コマンドライン引数を解析（スタンドアロン関数）"""
    default_args = {
        "source": DataSources.NOTION,
        "analysis": AnalysisTypes.DOMI, 
        "delivery": [DeliveryMethods.CONSOLE],
        "days": 7,
        "history": True,
        "schedule": False,
        "user_name": None,
        "email_to": None,
        "notion_api_key": None,
        "gdocs_url": None,
        "language": None
    }
    
    parsed_args = default_args.copy()
    i = 1
    
    while i < len(args):
        arg = args[i]
        
        if arg == CommandArgs.HELP:
            return {"help": True}
        elif arg == CommandArgs.SOURCE and i + 1 < len(args):
            source_value = args[i + 1]
            valid_data_sources = [DataSources.NOTION, DataSources.GDOCS]
            if source_value not in valid_data_sources:
                logger.error("無効なデータソース", "system", value=source_value, 
                           valid_values=valid_data_sources)
                sys.exit(1)
            parsed_args["source"] = source_value
            i += 1
        elif arg == CommandArgs.ANALYSIS and i + 1 < len(args):
            analysis_value = args[i + 1]
            valid_analysis_types = [AnalysisTypes.DOMI, AnalysisTypes.AGA]
            if analysis_value not in valid_analysis_types:
                logger.error("無効な分析タイプ", "system", value=analysis_value,
                           valid_values=valid_analysis_types)
                sys.exit(1)
            parsed_args["analysis"] = analysis_value
            i += 1
        elif arg == CommandArgs.DELIVERY and i + 1 < len(args):
            delivery_values = args[i + 1].split(",")
            valid_delivery_methods = [
                DeliveryMethods.CONSOLE, DeliveryMethods.EMAIL_TEXT,
                DeliveryMethods.EMAIL_HTML, DeliveryMethods.FILE_TEXT,
                DeliveryMethods.FILE_HTML
            ]
            for delivery_value in delivery_values:
                if delivery_value not in valid_delivery_methods:
                    logger.error("無効な配信方法", "system", value=delivery_value,
                               valid_values=valid_delivery_methods)
                    sys.exit(1)
            parsed_args["delivery"] = delivery_values
            i += 1
        elif arg == CommandArgs.DAYS and i + 1 < len(args):
            parsed_args["days"] = int(args[i + 1])
            i += 1
        elif arg == CommandArgs.HISTORY and i + 1 < len(args):
            history_value = args[i + 1].lower()
            valid_history_values = ["on", "off"]
            if history_value not in valid_history_values:
                logger.error("無効な履歴オプション", "system", value=history_value,
                            valid_values=valid_history_values)
                sys.exit(1)
            parsed_args["history"] = history_value == "on"
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
        elif arg == CommandArgs.GDOCS_URL and i + 1 < len(args):
            parsed_args["gdocs_url"] = args[i + 1]
            i += 1
        elif arg == CommandArgs.LANGUAGE and i + 1 < len(args):
            parsed_args["language"] = args[i + 1]
            i += 1
        elif arg == "--month-context":
            parsed_args["month_context"] = True
        
        i += 1
    
    return parsed_args


def main() -> None:
    """メイン関数"""
    usage_printer = UsagePrinter()
    
    # 引数を解析（PicklesSystemインスタンスを作らずに直接解析）
    args = parse_command_args(sys.argv)
    
    if args.get("help"):
        usage_printer.print_usage()
        sys.exit(0)
    
    # ユーザー設定の構築（コマンドライン引数を優先し、.envをフォールバック）
    user_config = None
    if args.get("user_name") or args.get("email_to") or args.get("notion_api_key") or args.get("gdocs_url") or args.get("language"):
        user_config = {
            'user_name': args.get("user_name"),
            'email_to': args.get("email_to"),
            'notion_api_key': args.get("notion_api_key"),
            'gdocs_url': args.get("gdocs_url") or os.getenv("GOOGLE_DOCS_URL"),
            'language': args.get("language")
        }


    # システムを初期化
    system = PicklesSystem(user_config=user_config, enable_history=args["history"])
    
    logger.info("Picklesシステム開始", "system")
    if args["history"]:
        logger.info("分析履歴機能有効", "system", feature="history")
    else:
        logger.info("分析履歴機能無効", "system", feature="history")
    
    # 設定情報をログ出力（テスト用の明確な形式で）
    delivery_str = ",".join(args["delivery"]) if isinstance(args["delivery"], list) else args["delivery"]
    logger.info("設定確認", "system", 
               analysis=args["analysis"], 
               delivery=delivery_str, 
               source=args["source"],
               days=args["days"],
               language=args['language'])
    
    if args["schedule"]:
        # スケジュール実行モード
        system.schedule_job()
    else:
        # 即座に実行モード
        results = system.run_analysis(
            data_source=args["source"],
            analysis_type=args["analysis"],
            delivery_methods=args["delivery"],
            days=args["days"],
            language=args["language"]
        )
        
        # 実行結果をログ出力
        if "error" in results:
            logger.error("分析実行失敗", "system", error=results["error"])
        else:
            success_methods = [k for k, v in results.items() if "成功" in str(v)]
            logger.success("分析実行完了", "system", 
                         success_count=len(success_methods),
                         methods=list(results.keys()))
        
        # エラーがある場合は終了コード1で終了
        if "error" in results:
            sys.exit(1)


if __name__ == "__main__":
    main()
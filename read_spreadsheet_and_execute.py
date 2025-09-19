#!/usr/bin/env python3
"""
Google Sheetsからユーザーデータを読み込んで、各ユーザーに対してPicklesを実行するスクリプト

使用方法:
python read_spreadsheet_and_execute.py --spreadsheet-id <SPREADSHEET_ID> --analysis domi --delivery email_html
"""

import os
import sys
import subprocess
import argparse
from typing import List, Dict
from googleapiclient.errors import HttpError
from utils import logger, get_google_service, GoogleAPIError


class GoogleSheetsReader:
    """Google Sheetsからユーザーデータを読み込むクラス"""
    
    def __init__(self, service_account_key_file: str = None):
        """
        service_account_key_file: サービスアカウントキーのJSONファイルパス
        環境変数GOOGLE_APPLICATION_CREDENTIALSが設定されている場合はそちらを優先
        """
        # 統一されたGoogle APIサービスを使用
        try:
            self._google_service = get_google_service(service_account_key_file)
            self.service = self._google_service.get_sheets_service()
            logger.info("Google Sheets統合サービス初期化完了", "sheets")
        except GoogleAPIError as e:
            logger.error("Google Sheets統合サービス初期化失敗", "sheets", error=str(e))
            raise ValueError(f"Google Sheets初期化エラー: {e}")
    
    def read_user_data(self, spreadsheet_id: str, range_name: str = "A1:E") -> List[Dict[str, str]]:
        """
        スプレッドシートからユーザーデータを読み込む
        
        想定するスプレッドシート構造:
        A列: EMAIL_TO
        B列: NOTION_API_KEY  
        C列: GOOGLE_DOCS_URL
        D列: user name
        E列: LANGUAGE
        """
        try:
            # アクセステストを実行
            if not self._google_service.test_sheets_access(spreadsheet_id):
                raise ValueError(f"Google Sheetsへのアクセスが拒否されました。スプレッドシート共有設定を確認してください: {spreadsheet_id}")
            
            # スプレッドシートのデータを取得
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id, 
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                logger.warning("スプレッドシートにデータが見つかりません", "sheets")
                return []
            
            # ヘッダー行を除外してユーザーデータを構築
            user_data_list = []
            for i, row in enumerate(values[1:], start=2):  # ヘッダー行をスキップ
                if len(row) >= 3:  # 最低限必要な列数をチェック  
                    user_data = {
                        'email_to': row[0].strip() if row[0] else '',
                        'notion_api_key': row[1].strip() if row[1] else '',
                        'google_docs_url': row[2].strip() if len(row) > 2 and row[2] else '',
                        'user_name': row[3].strip() if len(row) > 3 and row[3] else f'User {i-1}',
                        'language': row[4].strip() if len(row) > 4 and row[4] else 'japanese',
                    }
                    
                    # 必須フィールドのバリデーション（email_toは必須、データソースは少なくとも一つ）
                    if user_data['email_to'] and (user_data['notion_api_key'] or user_data['google_docs_url']):
                        # データソース情報の構築
                        source_info = []
                        if user_data['notion_api_key']:
                            api_key = user_data['notion_api_key']
                            if len(api_key) > 10:
                                source_info.append(f"Notion: {api_key[:4]}...{api_key[-4:]}")
                            else:
                                source_info.append(f"Notion: ⚠️短いキー({len(api_key)}文字)")
                        if user_data['google_docs_url']:
                            doc_url = user_data['google_docs_url']
                            # URLの最後の部分を表示
                            url_display = doc_url[-20:] if len(doc_url) > 20 else doc_url
                            source_info.append(f"GDocs: ...{url_display}")
                        
                        user_data_list.append(user_data)
                        logger.info("ユーザーデータ追加", "sheets", 
                                   user=user_data['user_name'], 
                                   email=user_data['email_to'], 
                                   sources=", ".join(source_info))
                    else:
                        logger.warning(f"行{i}: 必須フィールドが不足", "sheets", 
                                      row=i, missing="EMAIL_TO および (NOTION_API_KEY または GOOGLE_DOCS_URL)")
                else:
                    logger.warning(f"行{i}: 列数が不足", "sheets", row=i, required_columns=3)
            
            logger.success("スプレッドシートデータ読み込み完了", "sheets", user_count=len(user_data_list))
            return user_data_list
            
        except GoogleAPIError as error:
            logger.error("Google API統合エラー", "sheets", error=str(error))
            return []
        except HttpError as error:
            logger.error("Google Sheets APIエラー", "sheets", error=str(error))
            return []
        except Exception as error:
            logger.error("スプレッドシート読み込みエラー", "sheets", error=str(error))
            return []


def execute_pickles_for_user(user_data: Dict[str, str], analysis_type: str, delivery_methods: str, days: int = 7) -> bool:
    """
    指定されたユーザーに対してPicklesを実行
    データソース優先順位: Notion > Google Docs
    """
    try:
        # ユーザーデータから言語設定を取得（デフォルトはjapanese）
        user_language = user_data.get('language', 'japanese')
        
        # データソースの決定（優先順位: Notion > Google Docs）
        cmd = [
            sys.executable, "main.py",
            "--analysis", analysis_type,
            "--delivery", delivery_methods,
            "--days", str(days),
            "--user-name", user_data['user_name'],
            "--email-to", user_data['email_to'],
            "--language", user_language
        ]
        
        if user_data.get('notion_api_key'):
            # Notionを優先して使用
            cmd.extend(["--source", "notion", "--notion-api-key", user_data['notion_api_key']])
            data_source = "Notion"
        elif user_data.get('google_docs_url'):
            # Google Docsをフォールバックとして使用
            cmd.extend(["--source", "gdocs", "--gdocs-url", user_data['google_docs_url']])
            data_source = "Google Docs"
        else:
            logger.error(f"{user_data['user_name']}: データソースが設定されていません", "execution")
            return False
        
        logger.info(f"{user_data['user_name']}: {data_source}を使用", "execution")
        
        # デバッグ: 実行コマンドをログ出力
        logger.debug(f"実行コマンド", "execution", cmd=" ".join(cmd))
        
        logger.start(f"{user_data['user_name']}のPickles実行 ({data_source})", "execution")
        
        # Picklesを実行（タイムアウトを600秒に延長）
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.complete(f"{user_data['user_name']}のPickles実行 ({data_source})", "execution")
            # 成功時もログを表示
            if result.stdout:
                logger.debug("実行ログ出力", "execution", stdout=result.stdout)
            return True
        else:
            logger.failed(f"{user_data['user_name']}のPickles実行", "execution")
            logger.error("実行エラー詳細", "execution", 
                        stdout=result.stdout, stderr=result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("実行タイムアウト", "execution", user=user_data['user_name'], timeout=600)
        return False
    except Exception as e:
        logger.error("実行中の例外発生", "execution", user=user_data['user_name'], error=str(e))
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Google Sheetsからユーザーデータを読み込んでPicklesを実行")
    parser.add_argument("--spreadsheet-id", required=True, help="Google SpreadsheetsのID")
    parser.add_argument("--range", default="A1:E", help="読み込み範囲 (デフォルト: A1:E)")
    parser.add_argument("--analysis", default="domi", choices=["domi", "aga"], help="分析タイプ")
    parser.add_argument("--delivery", default="email_html", help="配信方法")
    parser.add_argument("--days", type=int, default=7, help="取得日数")
    parser.add_argument("--service-account-key", help="サービスアカウントキーファイルのパス")
    
    args = parser.parse_args()
    
    try:
        # Google Sheetsリーダーを初期化
        sheets_reader = GoogleSheetsReader(args.service_account_key)
        
        # ユーザーデータを読み込み
        logger.start("スプレッドシート読み込み", "sheets", spreadsheet_id=args.spreadsheet_id)
        user_data_list = sheets_reader.read_user_data(args.spreadsheet_id, args.range)
        
        if not user_data_list:
            logger.error("実行可能なユーザーデータが見つかりません", "execution")
            sys.exit(1)
        
        # 各ユーザーに対してPicklesを実行
        success_count = 0
        total_count = len(user_data_list)
        
        logger.info(f"{total_count}人のユーザーに対してPickles分析を実行", "execution", 
                   user_count=total_count, analysis_type=args.analysis, 
                   delivery=args.delivery, days=args.days)
        
        for i, user_data in enumerate(user_data_list, 1):
            logger.info(f"[{i}/{total_count}] ユーザー処理開始", "execution", 
                       user=user_data['user_name'], progress=f"{i}/{total_count}")
            if execute_pickles_for_user(user_data, args.analysis, args.delivery, args.days):
                success_count += 1
        
        # 実行結果サマリー
        logger.info("実行結果サマリー", "execution", 
                   success=success_count, total=total_count, failed=total_count - success_count)
        
        if success_count == total_count:
            logger.success("すべてのユーザーの分析が正常完了", "execution")
            sys.exit(0)
        else:
            logger.warning("一部のユーザーで分析に失敗", "execution")
            sys.exit(1)
            
    except Exception as e:
        logger.error("実行エラー", "execution", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
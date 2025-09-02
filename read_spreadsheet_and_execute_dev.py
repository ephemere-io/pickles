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
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import logger


class GoogleSheetsReader:
    """Google Sheetsからユーザーデータを読み込むクラス"""
    
    def __init__(self, service_account_key_file: str = None):
        """
        service_account_key_file: サービスアカウントキーのJSONファイルパス
        環境変数GOOGLE_APPLICATION_CREDENTIALSが設定されている場合はそちらを優先
        """
        self.service_account_key_file = service_account_key_file or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        if not self.service_account_key_file:
            raise ValueError("Google Service Account key file is required. Set GOOGLE_APPLICATION_CREDENTIALS or provide key file path.")
        
        # Google Sheets APIの認証とサービス構築
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.credentials = service_account.Credentials.from_service_account_file(
            self.service_account_key_file, 
            scopes=self.scopes
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
    
    def read_user_data(self, spreadsheet_id: str, range_name: str = "A1:D") -> List[Dict[str, str]]:
        """
        スプレッドシートからユーザーデータを読み込む
        
        想定するスプレッドシート構造:
        A列: EMAIL_TO
        B列: NOTION_API_KEY  
        C列: user name
        D列: LANGUAGE
        E列: その他（オプション）
        """
        try:
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
                        'user_name': row[2].strip() if row[2] else f'User {i-1}',
                        'language' : row[3].strip() if row[3] else '日本語',
                    }

                    logger.debug(f"言語設定 @ read_spreadsheet_and_execute_dev.py, read_user_data", "ai", language=user_data['language'])

                    # 必須フィールドのバリデーション
                    if user_data['email_to'] and user_data['notion_api_key']:
                        # デバッグ: APIキーの詳細を表示（最初と最後の文字のみ）
                        api_key = user_data['notion_api_key']
                        if len(api_key) > 10:
                            api_key_info = f"{api_key[:4]}...{api_key[-4:]} (長さ: {len(api_key)}文字)"
                        else:
                            api_key_info = f"⚠️ APIキーが短すぎます: {len(api_key)}文字"
                        
                        user_data_list.append(user_data)
                        logger.info("ユーザーデータ追加", "sheets", 
                                   user=user_data['user_name'], 
                                   email=user_data['email_to'], 
                                   api_key_info=api_key_info)
                    else:
                        logger.warning(f"行{i}: 必須フィールドが不足", "sheets", 
                                      row=i, missing="EMAIL_TO, NOTION_API_KEY")
                else:
                    logger.warning(f"行{i}: 列数が不足", "sheets", row=i, required_columns=3)
            
            logger.success("スプレッドシートデータ読み込み完了", "sheets", user_count=len(user_data_list))
            return user_data_list
            
        except HttpError as error:
            logger.error("Google Sheets APIエラー", "sheets", error=str(error))
            return []
        except Exception as error:
            logger.error("スプレッドシート読み込みエラー", "sheets", error=str(error))
            return []


def execute_pickles_for_user(user_data: Dict[str, str], analysis_type: str, delivery_methods: str, days: int = 7, month_context: bool = False) -> bool:
    """
    指定されたユーザーに対してPicklesを実行
    """
    try:
        cmd = [
            sys.executable, "main.py",
            "--analysis", analysis_type,
            "--delivery", delivery_methods,
            "--days", str(days),
            "--user-name", user_data['user_name'],
            "--email-to", user_data['email_to'],
            "--notion-api-key", user_data['notion_api_key'],
            "--language", user_data['language']
        ]
        
        # 30days Contextが有効な場合、フラグを追加
        if month_context:
            cmd.append("--month-context")
        
        logger.start(f"{user_data['user_name']}のPickles実行", "execution")

        logger.debug(f"言語設定 @ read_spreadsheet_and_execute_dev.py, execute_pickles_for_user", "ai", language=user_data['language'])
        
        # Picklesを実行（元のcmdを使用）
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.complete(f"{user_data['user_name']}のPickles実行", "execution")
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
        logger.error("実行タイムアウト", "execution", user=user_data['user_name'], timeout=300)
        return False
    except Exception as e:
        logger.error("実行中の例外発生", "execution", user=user_data['user_name'], error=str(e))
        return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Google Sheetsからユーザーデータを読み込んでPicklesを実行")
    parser.add_argument("--spreadsheet-id", required=True, help="Google SpreadsheetsのID")
    parser.add_argument("--range", default="A1:D", help="読み込み範囲 (デフォルト: A1:D)")
    parser.add_argument("--analysis", default="domi", choices=["domi", "aga"], help="分析タイプ")
    parser.add_argument("--delivery", default="email_html", help="配信方法")
    parser.add_argument("--days", type=int, default=7, help="取得日数")
    parser.add_argument("--service-account-key", help="サービスアカウントキーファイルのパス")
    parser.add_argument("--month-context", action="store_true", help="30日間のコンテキストを含めて分析")
    
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
                   delivery=args.delivery, days=args.days, month_context=args.month_context)
        
        for i, user_data in enumerate(user_data_list, 1):
            logger.info(f"[{i}/{total_count}] ユーザー処理開始", "execution", 
                       user=user_data['user_name'], progress=f"{i}/{total_count}")
            if execute_pickles_for_user(user_data, args.analysis, args.delivery, args.days, args.month_context):
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
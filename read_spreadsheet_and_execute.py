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
from utils import Logger


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
        D列: その他（オプション）
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
                Logger.log_warning("スプレッドシートにデータが見つかりません")
                return []
            
            # ヘッダー行を除外してユーザーデータを構築
            user_data_list = []
            for i, row in enumerate(values[1:], start=2):  # ヘッダー行をスキップ
                if len(row) >= 3:  # 最低限必要な列数をチェック  
                    user_data = {
                        'email_to': row[0].strip() if row[0] else '',
                        'notion_api_key': row[1].strip() if row[1] else '',
                        'user_name': row[2].strip() if row[2] else f'User {i-1}'
                    }
                    
                    # 必須フィールドのバリデーション
                    if user_data['email_to'] and user_data['notion_api_key']:
                        # デバッグ: APIキーの詳細を表示（最初と最後の文字のみ）
                        api_key = user_data['notion_api_key']
                        if len(api_key) > 10:
                            api_key_info = f"{api_key[:4]}...{api_key[-4:]} (長さ: {len(api_key)}文字)"
                        else:
                            api_key_info = f"⚠️ APIキーが短すぎます: {len(api_key)}文字"
                        
                        user_data_list.append(user_data)
                        Logger.log_sheets_user_added(user_data['user_name'], user_data['email_to'], api_key_info)
                    else:
                        Logger.log_warning(f"行{i}: 必須フィールド(EMAIL_TO, NOTION_API_KEY)が不足しています")
                else:
                    Logger.log_warning(f"行{i}: 列数が不足しています（最低3列必要）")
            
            Logger.log_sheets_summary(len(user_data_list))
            return user_data_list
            
        except HttpError as error:
            Logger.log_sheets_error(str(error))
            return []
        except Exception as error:
            Logger.log_error(f"スプレッドシート読み込みエラー: {error}")
            return []


def execute_pickles_for_user(user_data: Dict[str, str], analysis_type: str, delivery_methods: str, days: int = 7) -> bool:
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
            "--notion-api-key", user_data['notion_api_key']
        ]
        
        Logger.log_execution_start(user_data['user_name'])
        
        # Picklesを実行（元のcmdを使用）
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            Logger.log_execution_complete(user_data['user_name'])
            # 成功時もログを表示
            if result.stdout:
                Logger.log_execution_log(result.stdout)
            return True
        else:
            Logger.log_execution_error(user_data['user_name'])
            print(f"   STDOUT: {result.stdout}")
            print(f"   STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        Logger.log_execution_timeout(user_data['user_name'])
        return False
    except Exception as e:
        Logger.log_error(f"{user_data['user_name']} の実行エラー: {e}")
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
    
    args = parser.parse_args()
    
    try:
        # Google Sheetsリーダーを初期化
        sheets_reader = GoogleSheetsReader(args.service_account_key)
        
        # ユーザーデータを読み込み
        Logger.log_sheets_reading(args.spreadsheet_id)
        user_data_list = sheets_reader.read_user_data(args.spreadsheet_id, args.range)
        
        if not user_data_list:
            print("❌ 実行可能なユーザーデータが見つかりませんでした")
            sys.exit(1)
        
        # 各ユーザーに対してPicklesを実行
        success_count = 0
        total_count = len(user_data_list)
        
        print(f"\n🎯 {total_count}人のユーザーに対してPickles分析を実行します")
        print(f"   分析タイプ: {args.analysis}")
        print(f"   配信方法: {args.delivery}")
        print(f"   取得日数: {args.days}日\n")
        
        for i, user_data in enumerate(user_data_list, 1):
            print(f"[{i}/{total_count}] ", end="")
            if execute_pickles_for_user(user_data, args.analysis, args.delivery, args.days):
                success_count += 1
            print()  # 改行
        
        # 実行結果サマリー
        print("=" * 50)
        print(f"📊 実行結果サマリー")
        print(f"   成功: {success_count}/{total_count} 人")
        print(f"   失敗: {total_count - success_count}/{total_count} 人")
        print("=" * 50)
        
        if success_count == total_count:
            print("🎉 すべてのユーザーの分析が正常に完了しました！")
            sys.exit(0)
        else:
            print("⚠️ 一部のユーザーで分析に失敗しました")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
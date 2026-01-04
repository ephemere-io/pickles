#!/usr/bin/env python3
"""
Google Sheetsからユーザーデータを読み込んで、各ユーザーに対してPicklesを実行するスクリプト

使用方法:
python read_spreadsheet_and_execute.py --spreadsheet-id <SPREADSHEET_ID> --analysis domi --delivery email_html
"""

import argparse
import sys
import subprocess
from typing import List, Dict
from utils.logger import logger
from utils.google_service import get_google_service
from models.user import User, mask_name


class GoogleSheetsReader:
    """Google Sheetsからユーザーデータを読み込む"""

    def __init__(self):
        self.sheets_service = get_google_service().get_sheets_service()

    def read_user_data(self, spreadsheet_id: str, range_name: str = "A1:E") -> List[Dict]:
        """Google Sheetsからユーザーデータを読み込む"""
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        rows = result.get('values', [])

        if not rows or len(rows) < 2:
            logger.warning("ユーザーデータが見つかりません", "sheets")
            return []

        # ヘッダー行をスキップ
        data_rows = rows[1:]

        user_data_list = []
        for row in data_rows:
            if not row or len(row) == 0:
                continue

            # 列が不足している場合は空文字で埋める
            while len(row) < 5:
                row.append('')

            user_data = {
                'email_to': row[0].strip(),
                'notion_api_key': row[1].strip() if row[1] else None,
                'google_docs_url': row[2].strip() if row[2] else None,
                'user_name': row[3].strip(),
                'language': row[4].strip() if row[4] else 'japanese'
            }

            # メールアドレスが必須
            if user_data['email_to']:
                user_data_list.append(user_data)

        return user_data_list


def execute_pickles_for_user(user: User, analysis_type: str,
                             delivery_methods: str, days: int = 7) -> bool:
    """指定されたユーザーに対してPicklesを実行

    Args:
        user: Userドメインモデル
        analysis_type: 分析タイプ（domi/aga）
        delivery_methods: 配信方法
        days: 取得日数

    Returns:
        成功したかどうか
    """

    logger.info(f"🎯 {mask_name(user.user_name)} の分析開始", "execution")

    user_data = user.to_dict()

    cmd = [
        sys.executable, "main.py",
        "--user-id", user.id,  # UUIDを渡す
        "--analysis", analysis_type,
        "--delivery", delivery_methods,
        "--days", str(days),
        "--user-name", user_data['user_name'],
        "--email-to", user_data['email_to'],
        "--language", user_data['language']
    ]

    # データソース追加
    if user.notion_api_key:
        cmd.extend(["--source", "notion",
                   "--notion-api-key", user.notion_api_key])
    elif user.google_docs_url:
        cmd.extend(["--source", "gdocs",
                   "--gdocs-url", user.google_docs_url])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            # 最終分析時刻を更新
            user.update_last_analysis_at()
            logger.success(f"✅ {mask_name(user.user_name)} 完了", "execution")
            return True
        else:
            logger.error(f"❌ {mask_name(user.user_name)} 失敗", "execution")
            return False

    except Exception as e:
        logger.error(f"❌ {mask_name(user.user_name)} エラー", "execution",
                    error_type=type(e).__name__)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Pickles Multi-User Execution with Supabase Sync"
    )

    parser.add_argument("--spreadsheet-id", required=True,
                       help="Google SpreadsheetsのID")
    parser.add_argument("--range", default="A1:E",
                       help="読み込み範囲（デフォルト: A1:E）")
    parser.add_argument("--analysis", default="domi",
                       choices=["domi", "aga"], help="分析タイプ")
    parser.add_argument("--delivery", default="email_html",
                       help="配信方法（カンマ区切りで複数指定可）")
    parser.add_argument("--days", type=int, default=7,
                       help="取得日数")

    args = parser.parse_args()

    try:
        logger.start("Google Sheets読み込み開始", "sheets",
                    spreadsheet_id=args.spreadsheet_id)

        # 1. Google Sheetsから読み込み
        sheets_reader = GoogleSheetsReader()
        sheets_data = sheets_reader.read_user_data(args.spreadsheet_id)

        logger.info(f"Google Sheetsから{len(sheets_data)}人読み込み", "sheets")

        # 2. Userドメインモデルで同期（自動的にSupabaseと同期）
        users = User.sync_from_google_sheets(sheets_data)

        if not users:
            logger.error("実行可能なユーザーが見つかりません", "execution")
            sys.exit(1)

        # 3. 各ユーザーに対して実行
        success_count = 0
        total_count = len(users)

        logger.info(f"📊 {total_count}人のユーザーに対して分析実行", "execution")

        for i, user in enumerate(users, 1):
            logger.info(f"[{i}/{total_count}] {mask_name(user.user_name)}", "execution")

            if execute_pickles_for_user(user, args.analysis,
                                       args.delivery, args.days):
                success_count += 1

        # 結果サマリー
        logger.complete("実行完了", "execution",
                       success=success_count,
                       total=total_count,
                       failed=total_count - success_count)

        sys.exit(0 if success_count > 0 else 1)

    except Exception as e:
        logger.error("実行エラー", "execution", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

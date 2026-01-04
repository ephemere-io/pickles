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
from googleapiclient.errors import HttpError
from utils.logger import logger
from utils.google_service import get_google_service, GoogleAPIError
from models.user import User, mask_name, mask_email


class GoogleSheetsReader:
    """Google Sheetsからユーザーデータを読み込む"""

    def __init__(self, service_account_key_file: str = None):
        """
        service_account_key_file: サービスアカウントキーのJSON文字列
        環境変数GOOGLE_SERVICE_ACCOUNT_KEYから自動的に読み込まれます
        """
        try:
            self._google_service = get_google_service(service_account_key_file)
            self.sheets_service = self._google_service.get_sheets_service()
            logger.info("Google Sheets統合サービス初期化完了", "sheets")
        except GoogleAPIError as e:
            logger.error("Google Sheets統合サービス初期化失敗", "sheets", error=str(e))
            raise ValueError(f"Google Sheets初期化エラー: {e}")

    def read_user_data(self, spreadsheet_id: str, range_name: str = "A1:E") -> List[Dict]:
        """Google Sheetsからユーザーデータを読み込む

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
                raise ValueError(f"Google Sheetsへのアクセスが拒否されました: {spreadsheet_id}")

            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()

            rows = result.get('values', [])

            if not rows or len(rows) < 2:
                logger.warning("ユーザーデータが見つかりません", "sheets")
                return []

            # ヘッダー行をスキップ
            user_data_list = []
            for i, row in enumerate(rows[1:], start=2):
                if not row or len(row) == 0:
                    continue

                # 列が不足している場合は空文字で埋める
                while len(row) < 5:
                    row.append('')

                user_data = {
                    'email_to': row[0].strip(),
                    'notion_api_key': row[1].strip() if row[1] else None,
                    'google_docs_url': row[2].strip() if row[2] else None,
                    'user_name': row[3].strip() if row[3] else f'User {i-1}',
                    'language': row[4].strip() if row[4] else 'japanese'
                }

                # 必須フィールドのバリデーション（email + データソース）
                if user_data['email_to'] and (user_data['notion_api_key'] or user_data['google_docs_url']):
                    # データソース情報の構築（マスク済み）
                    source_info = []
                    if user_data['notion_api_key']:
                        api_key = user_data['notion_api_key']
                        if len(api_key) > 10:
                            source_info.append(f"Notion: {api_key[:4]}...{api_key[-4:]}")
                        else:
                            source_info.append(f"Notion: 短いキー({len(api_key)}文字)")
                    if user_data['google_docs_url']:
                        source_info.append("GDocs: あり")

                    user_data_list.append(user_data)
                    logger.info("ユーザーデータ追加", "sheets",
                               user=mask_name(user_data['user_name']),
                               email=mask_email(user_data['email_to']),
                               sources=", ".join(source_info))
                elif user_data['email_to']:
                    logger.warning(f"行{i}: データソースが不足", "sheets",
                                  row=i, missing="NOTION_API_KEY または GOOGLE_DOCS_URL")
                else:
                    logger.warning(f"行{i}: 必須フィールドが不足", "sheets", row=i)

            logger.success("スプレッドシートデータ読み込み完了", "sheets",
                          user_count=len(user_data_list))
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
    masked_name = mask_name(user.user_name)
    user_data = user.to_dict()

    # データソースの決定（優先順位: Notion > Google Docs）
    if user.notion_api_key:
        data_source = "Notion"
    elif user.google_docs_url:
        data_source = "Google Docs"
    else:
        logger.error(f"❌ {masked_name} データソースなし", "execution")
        return False

    logger.info(f"{masked_name}: {data_source}を使用", "execution")

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

    # デバッグ: 実行コマンドをログ出力（個人情報はマスク）
    # 機密情報を含む引数の次の値をマスク
    sensitive_args = {'--email-to', '--user-name', '--gdocs-url', '--notion-api-key'}
    safe_cmd = []
    skip_next = False
    for c in cmd:
        if skip_next:
            safe_cmd.append('***')
            skip_next = False
        elif c in sensitive_args:
            safe_cmd.append(c)
            skip_next = True
        elif 'secret' in c.lower():
            safe_cmd.append('***')
        else:
            safe_cmd.append(c)
    logger.debug("実行コマンド", "execution", cmd=" ".join(safe_cmd))

    logger.start(f"{masked_name}のPickles実行 ({data_source})", "execution")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            # 最終分析時刻を更新
            user.update_last_analysis_at()
            logger.complete(f"{masked_name}のPickles実行 ({data_source})", "execution")
            return True
        else:
            logger.failed(f"{masked_name}のPickles実行", "", "execution")
            # stdout/stderrの末尾500文字をログ出力（エラーは通常末尾にある）
            stdout_tail = result.stdout[-500:] if result.stdout else ""
            stderr_tail = result.stderr[-500:] if result.stderr else ""
            logger.error("実行エラー詳細", "execution",
                        return_code=result.returncode,
                        stdout_tail=stdout_tail,
                        stderr_tail=stderr_tail)
            return False

    except subprocess.TimeoutExpired:
        logger.error("実行タイムアウト", "execution",
                    user=masked_name, timeout=600)
        return False

    except Exception as e:
        logger.error("実行中の例外発生", "execution",
                    user=masked_name, error_type=type(e).__name__)
        return False


def filter_users_for_batch(users: List[User], batch_id: int, total_batches: int) -> List[User]:
    """バッチ用にユーザーリストをフィルタリング（動的分割）"""
    import math

    total_users = len(users)
    users_per_batch = math.ceil(total_users / total_batches)

    start_index = (batch_id - 1) * users_per_batch
    end_index = min(batch_id * users_per_batch, total_users)

    batch_users = users[start_index:end_index]

    logger.info("バッチ分割詳細", "execution",
               total_users=total_users,
               batch_id=batch_id,
               total_batches=total_batches,
               start_index=start_index,
               end_index=end_index,
               batch_size=len(batch_users))

    return batch_users


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
    parser.add_argument("--batch-id", type=int,
                       help="バッチID（並列実行用）")
    parser.add_argument("--total-batches", type=int,
                       help="総バッチ数（並列実行用）")
    parser.add_argument("--service-account-key",
                       help="サービスアカウントキーファイルのパス")

    args = parser.parse_args()

    try:
        logger.start("Google Sheets読み込み開始", "sheets",
                    spreadsheet_id=args.spreadsheet_id)

        # 1. Google Sheetsから読み込み
        sheets_reader = GoogleSheetsReader(args.service_account_key)
        sheets_data = sheets_reader.read_user_data(args.spreadsheet_id, args.range)

        logger.info(f"Google Sheetsから{len(sheets_data)}人読み込み", "sheets")

        # 2. Userドメインモデルで同期（自動的にSupabaseと同期）
        users = User.sync_from_google_sheets(sheets_data)

        if not users:
            logger.error("実行可能なユーザーが見つかりません", "execution")
            sys.exit(1)

        # バッチフィルタリング（並列実行用）
        if args.batch_id is not None and args.total_batches is not None:
            users = filter_users_for_batch(users, args.batch_id, args.total_batches)
            logger.info(f"バッチ{args.batch_id}/{args.total_batches}で処理", "execution",
                       batch_users=len(users))

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
        logger.info("実行結果サマリー", "execution",
                   success=success_count, total=total_count,
                   failed=total_count - success_count)

        # 終了コード: 3パターン
        if total_count == 0:
            logger.info("処理対象ユーザーなし", "execution")
            sys.exit(0)
        elif success_count == total_count:
            logger.success("すべてのユーザーの分析が正常完了", "execution")
            sys.exit(0)
        elif success_count > 0:
            logger.warning("一部のユーザーで分析に失敗したが、一部成功", "execution")
            sys.exit(0)  # 部分成功は正常終了扱い
        else:
            logger.error("すべてのユーザーで分析に失敗", "execution")
            sys.exit(1)

    except Exception as e:
        logger.error("実行エラー", "execution", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

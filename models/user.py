"""Userドメインモデル"""
from typing import Optional, List, Dict
from datetime import datetime
from supabase.client import get_supabase_client
from utils.logger import logger


def mask_email(email: str) -> str:
    """メールアドレスをマスク（例: t***@example.com）"""
    if not email or '@' not in email:
        return '***'
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        masked_local = '*'
    else:
        masked_local = local[0] + '***'
    return f"{masked_local}@{domain}"


def mask_name(name: str) -> str:
    """ユーザー名をマスク（例: 山田太郎 → 山***）"""
    if not name:
        return '***'
    if len(name) <= 1:
        return '*'
    return name[0] + '***'


class User:
    """ユーザードメインモデル

    責務:
    - Supabaseとの永続化ロジック
    - Google Sheetsとの同期ロジック
    - ユーザー情報のバリデーション
    """

    def __init__(
        self,
        id: Optional[str] = None,
        email: str = None,
        user_name: str = None,
        notion_api_key: Optional[str] = None,
        google_docs_url: Optional[str] = None,
        language: str = 'japanese',
        is_active: bool = True,
        **kwargs
    ):
        self.id = id
        self.email = email
        self.user_name = user_name
        self.notion_api_key = notion_api_key
        self.google_docs_url = google_docs_url
        self.language = language
        self.is_active = is_active
        self.source_type = self._detect_source_type()

    def _detect_source_type(self) -> str:
        """データソースタイプを判定"""
        has_notion = bool(self.notion_api_key)
        has_gdocs = bool(self.google_docs_url)

        if has_notion and has_gdocs:
            return 'both'
        elif has_notion:
            return 'notion'
        elif has_gdocs:
            return 'gdocs'
        return 'unknown'

    @classmethod
    def find_by_email(cls, email: str) -> Optional['User']:
        """メールアドレスでユーザーを検索"""
        supabase = get_supabase_client()
        result = supabase.table('users').select('*').eq('email', email).execute()

        if result.data:
            return cls(**result.data[0])
        return None

    @classmethod
    def find_all_active(cls) -> List['User']:
        """アクティブなユーザーをすべて取得"""
        supabase = get_supabase_client()
        result = supabase.table('users').select('*').eq('is_active', True).execute()

        return [cls(**row) for row in result.data]

    def save(self) -> 'User':
        """ユーザーを保存（新規作成または更新）"""
        supabase = get_supabase_client()

        if self.id:
            # 更新
            result = supabase.table('users').update({
                'user_name': self.user_name,
                'language': self.language,
                'notion_api_key': self.notion_api_key,
                'google_docs_url': self.google_docs_url,
                'source_type': self.source_type,
                'is_active': self.is_active,
                'updated_at': 'now()'
            }).eq('id', self.id).execute()

            logger.info(f"✓ ユーザー更新: {mask_email(self.email)}", "user")
        else:
            # 新規作成
            result = supabase.table('users').insert({
                'email': self.email,
                'user_name': self.user_name,
                'language': self.language,
                'notion_api_key': self.notion_api_key,
                'google_docs_url': self.google_docs_url,
                'source_type': self.source_type,
                'is_active': self.is_active
            }).execute()

            self.id = result.data[0]['id']
            logger.success(f"✨ ユーザー作成: {mask_email(self.email)}", "user")

        return self

    def deactivate(self):
        """ユーザーを非アクティブ化"""
        self.is_active = False
        self.save()
        logger.warning(f"⚠️  ユーザー非アクティブ化: {mask_email(self.email)}", "user")

    def update_last_analysis_at(self):
        """最終分析時刻を更新"""
        supabase = get_supabase_client()
        supabase.table('users').update({
            'last_analysis_at': 'now()'
        }).eq('id', self.id).execute()

    @classmethod
    def sync_from_google_sheets(
        cls,
        sheets_data: List[Dict]
    ) -> List['User']:
        """Google Sheetsからユーザー情報を同期

        Args:
            sheets_data: Google Sheetsから読み込んだデータ

        Returns:
            同期されたUserオブジェクトのリスト
        """
        sheets_emails = [row['email_to'] for row in sheets_data]

        # 既存ユーザーを取得
        supabase = get_supabase_client()
        existing_result = supabase.table('users').select('id, email').execute()
        existing_users = {u['email']: u['id'] for u in existing_result.data}

        synced_users = []

        # Google Sheetsの各行を処理
        for row in sheets_data:
            email = row['email_to']

            if email in existing_users:
                # 既存ユーザー更新
                user = cls.find_by_email(email)
                user.user_name = row['user_name']
                user.language = row.get('language', 'japanese')
                user.notion_api_key = row.get('notion_api_key')
                user.google_docs_url = row.get('google_docs_url')
                user.is_active = True
                user.save()
            else:
                # 新規ユーザー作成
                user = cls(
                    email=email,
                    user_name=row['user_name'],
                    language=row.get('language', 'japanese'),
                    notion_api_key=row.get('notion_api_key'),
                    google_docs_url=row.get('google_docs_url'),
                    is_active=True
                )
                user.save()

            synced_users.append(user)

        # Sheetsから削除されたユーザーを非アクティブ化
        removed_emails = set(existing_users.keys()) - set(sheets_emails)
        for email in removed_emails:
            user = cls.find_by_email(email)
            if user:
                user.deactivate()

        logger.complete(f"同期完了: {len(synced_users)}人", "user")
        return synced_users

    def to_dict(self) -> Dict:
        """辞書形式に変換（実行用データ）"""
        return {
            'user_id': self.id,
            'email_to': self.email,
            'user_name': self.user_name,
            'notion_api_key': self.notion_api_key,
            'google_docs_url': self.google_docs_url,
            'language': self.language
        }

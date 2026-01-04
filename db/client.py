"""Supabaseクライアント初期化"""
import os
from supabase import create_client, Client
from functools import lru_cache


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Supabaseクライアントのシングルトンインスタンス取得"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')

    if not url or not key:
        raise ValueError(
            "SUPABASE_URLとSUPABASE_KEYを環境変数に設定してください"
        )

    return create_client(url, key)

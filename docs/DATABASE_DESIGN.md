# データベース設計（Phase 0: 実行履歴管理）

## 📋 概要

Phase 0では、**Google Sheetsを継続使用しつつ、Supabaseで実行履歴を記録**します。
Google Sheetsはユーザー情報のマスター（真実の源泉）として維持し、Supabaseは実行履歴の永続化とUUID管理に特化します。

## 🎯 前提とする運用形態

### Google Sheetsを継続使用

本設計では、**ユーザー情報の管理はGoogle Sheetsで継続**します。

**Google Sheetsの構造**:

```
列A: EMAIL_TO         例: dominick.chen@gmail.com
列B: NOTION_API_KEY   例: ntn_G17609648604...
列C: GOOGLE_DOCS_URL  例: (空欄またはURL)
列D: USER_NAME        例: Dominique
列E: LANGUAGE         例: japanese
```

**運用フロー**:

1. ユーザー追加: Google Sheetsに行を追加
2. ユーザー情報変更: Google Sheets上で編集（API Key変更など）
3. ユーザー削除: Google Sheetsから行を削除
4. 次回実行時: 自動的にSupabaseと同期

### Supabaseの役割

Supabaseは**実行履歴の記録**と**UUID管理**に特化:

**usersテーブル**:

- Google Sheetsから同期された情報のキャッシュ
- メールアドレス → UUID の変換テーブル
- 最終分析時刻の記録

**analysis_runs / deliveriesテーブル**:

- 分析実行履歴の永続化
- エラー追跡、配信履歴の管理

**重要**: usersテーブルへの直接CRUD操作は原則として行いません。Google Sheetsが真実の源泉です。

---

## 🎯 設計原則

1. **Google Sheetsを真実の源泉として維持**
    - ユーザー情報の編集はGoogle Sheetsで実施
    - Supabaseは自動同期されるキャッシュ
2. **JSONB使用ゼロ**
    - すべてシンプルなTEXT型で管理
    - 複雑性を排除し、保守性を向上
3. **関心の分離**
    - ユーザー管理（`users`）← Google Sheetsから同期
    - 分析実行と結果（`analysis_runs`）
    - 配信方法（`deliveries`）
4. **プラットフォーム非依存**
    - GitHub Actions専用の設計を排除
    - Cron、手動実行、API経由など将来の拡張に対応
5. **コンテンツと表現の分離**
    - 配信用レポートは`analysis_runs.content`に1回だけ保存
    - `deliveries`は配信方法のメタデータのみ保持

---

## 📊 テーブル設計

### 1. `users` テーブル（ユーザー管理・UUID変換）

```sql
create table public.users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,  -- Google Sheetsとの照合キー
    user_name text not null,

    -- データソース情報（Google Sheetsから同期）
    notion_api_key text,
    google_docs_url text,
    source_type text check (source_type in ('notion', 'gdocs', 'both')),

    -- メタデータ
    language text default 'japanese',
    is_active boolean default true,  -- Sheetsから削除時false

    -- タイムスタンプ
    created_at timestamptz default now(),    -- UUID付与日時
    updated_at timestamptz default now(),    -- 最終同期日時
    last_analysis_at timestamptz             -- 最終分析実行日時
);

-- インデックス
create index idx_users_email on public.users(email);
create index idx_users_active on public.users(is_active) where is_active = true;
create index idx_users_last_analysis_at on public.users(last_analysis_at);
```

**目的**: Google Sheetsから同期されるユーザー情報のキャッシュ + UUID管理

**フィールドの役割**:

| フィールド | 役割 | 更新タイミング |
| --- | --- | --- |
| `id` | UUID（永続的な識別子） | 初回登録時に自動生成 |
| `email` | Google Sheetsとの照合キー | - |
| `user_name` | ユーザー名 | 毎回同期時に更新 |
| `notion_api_key` | Notion API Key | 毎回同期時に更新 |
| `google_docs_url` | Google Docs URL | 毎回同期時に更新 |
| `source_type` | データソース種別 | 毎回同期時に判定 |
| `language` | 言語設定 | 毎回同期時に更新 |
| `is_active` | アクティブ状態 | Sheetsから削除時false |
| `created_at` | UUID付与日時 | 初回登録時のみ |
| `updated_at` | 最終同期日時 | 毎回同期時に更新 |
| `last_analysis_at` | 最終分析日時 | main.py実行完了時に更新 |

**重要なポイント**:

1. **UUIDの永続性**: 一度付与されたUUIDは変更されない
2. **Google Sheetsが真実の源泉**: usersテーブルはキャッシュに過ぎない
3. **削除は論理削除**: `is_active = false`にして履歴を保持

---

### 2. `analysis_runs` テーブル（分析実行と結果）

```sql
create table public.analysis_runs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,

    -- 分析パラメータ
    analysis_type text not null check (analysis_type in ('domi', 'aga')),
    days_analyzed integer not null,
    source_used text not null check (source_used in ('notion', 'gdocs')),

    -- 分析結果（配信用レポート）
    content text,          -- ユーザーに配信したレポート本文（Markdown形式）
    stats_summary text,    -- 統計サマリー（例: "直近7日間: 21件、平均5092文字"）

    -- 実行メタデータ
    status text not null check (status in ('pending', 'running', 'completed', 'failed')),
    error_message text,
    trigger_type text check (trigger_type in ('github_actions', 'manual', 'cron', 'api')),
    trigger_id text,

    -- タイムスタンプ
    created_at timestamptz default now(),
    completed_at timestamptz
);

-- インデックス
create index idx_analysis_runs_user_id on public.analysis_runs(user_id);
create index idx_analysis_runs_status on public.analysis_runs(status);
create index idx_analysis_runs_created_at on public.analysis_runs(created_at desc);
```

**目的**:

- **何を**（analysis_type, days_analyzed）
- **どう**分析したか（source_used）
- **結果**はどうだったか（content, stats_summary, status）

**重要ポイント**:

- `content`: ユーザーに配信したレポート本文（Markdown形式）
    - DOMI/AGA分析結果を含む完成形
    - 配信履歴として保持（「何を送ったか」の記録）
    - 再送機能やエラー調査に使用
- `trigger_type` + `trigger_id`: 実行トリガーを構造化して記録

**`trigger_type` と `trigger_id` の記録例**:

```python
# GitHub Actions実行時
trigger_type = 'github_actions'
trigger_id = os.getenv('GITHUB_RUN_ID')  # 例: '123456'

# 手動実行時
trigger_type = 'manual'
trigger_id = 'user@example.com'

# Cron実行時
trigger_type = 'cron'
trigger_id = 'weekly_monday_7am'

# API経由時
trigger_type = 'api'
trigger_id = 'webhook_xyz'
```

---

### 3. `deliveries` テーブル（配信履歴）

```sql
create table public.deliveries (
    id uuid primary key default gen_random_uuid(),
    analysis_run_id uuid not null references public.analysis_runs(id) on delete cascade,

    -- 配信方法
    delivery_method text not null check (delivery_method in (
        'email_html', 'email_text', 'console', 'file_text', 'file_html'
    )),
    email_to text,  -- 配信先メールアドレス（email配信時のみ）

    -- 配信結果
    status text not null check (status in ('pending', 'sent', 'failed')),
    error_message text,

    -- タイムスタンプ
    created_at timestamptz default now(),
    sent_at timestamptz
);

-- インデックス
create index idx_deliveries_analysis_run_id on public.deliveries(analysis_run_id);
create index idx_deliveries_status on public.deliveries(status);
create index idx_deliveries_created_at on public.deliveries(created_at desc);
```

**目的**:

- **どの方法で**（delivery_method）
- **誰に**（email_to）
- **届けたか**（status）

**重要ポイント**:

- コンテンツは保存せず、`analysis_run_id`で参照するのみ
- 1つの分析結果を複数の方法で配信可能（例: email_html + email_text）
- JSONB不使用

---

## 🔄 自動同期の仕組み

### 同期タイミング

`read_spreadsheet_and_execute.py`実行時に毎回自動同期されます:

```
GitHub Actions実行（週次）
    ↓
Google Sheets読み込み
    ↓
Supabaseと自動同期（メールアドレスで照合）
    ├─ 新規ユーザー → UUID付与して登録
    ├─ 既存ユーザー → 情報更新（API key変更対応）
    └─ 削除ユーザー → 検出して非アクティブ化
    ↓
各ユーザーに対して分析実行（user_id付き）
    ↓
analysis_runs保存（実行履歴）
deliveries保存（配信履歴）
```

### データフロー詳細

```
Google Sheets（真実の源泉）
    ↓ メールアドレスをキーに照合
Supabase users（UUID管理 + 同期キャッシュ）
    ├─ 新規ユーザー → 自動作成してUUID付与
    └─ 既存ユーザー → UUID取得、情報更新
    ↓
main.py実行（--user-id渡す）
    ↓
┌─────────────────────────┐
│ analysis_runs テーブル   │
│ - analysis_type: 'domi'│
│ - days_analyzed: 7     │
│ - content: "今週の..."  │
│ - stats_summary: "21件"│
│ - status: 'completed'  │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│ deliveries テーブル      │
│ - delivery_method:     │
│   'email_html'         │
│ - email_to:            │
│   'user@example.com'   │
│ - status: 'sent'       │
└─────────────────────────┘
```

---

## 🚀 運用フロー

### ユーザー追加

```
1. Google Sheetsに新しい行を追加
   EMAIL_TO | NOTION_API_KEY | ... | USER_NAME | LANGUAGE
   new@example.com | ntn_xxx... | ... | 新規ユーザー | japanese

2. 次回のGitHub Actions実行を待つ（毎週月曜7:00）
   または手動実行

3. 自動的にSupabaseにUUID付きで登録される
   ✨ 新規ユーザー登録: new@example.com (12345678-...)

4. 分析が実行され、レポートが配信される
```

### ユーザー情報変更

```
1. Google Sheetsで該当行を編集
   例: Notion API Keyを変更

2. 次回実行時に自動的に反映
   ✓ 既存ユーザー更新: user@example.com
```

### ユーザー削除

```
1. Google Sheetsから該当行を削除

2. 次回実行時に非アクティブ化
   ⚠️  ユーザー非アクティブ化: removed@example.com

3. 過去の分析履歴は保持される（is_active = false）

4. 再度追加すれば、既存のUUIDで復活
   ✓ 既存ユーザー更新: removed@example.com (is_active: true)
```

---

## 📁 ディレクトリ構成

ドメインモデルを中心とした構造で、再利用性と保守性を向上させます:

```
pickles/
├── models/                    # ドメインモデル（ビジネスロジック）
│   ├── __init__.py
│   ├── user.py               # Userドメインモデル
│   ├── analysis_run.py       # AnalysisRunドメインモデル
│   └── delivery.py           # Deliveryドメインモデル
│
├── db/                        # データベース関連
│   ├── migrations/           # マイグレーションファイル
│   │   ├── 20241215000000_create_users_table.sql
│   │   ├── 20241215000001_create_analysis_runs_table.sql
│   │   ├── 20241215000002_create_deliveries_table.sql
│   │   └── 20241215000003_create_execution_history_view.sql
│   └── client.py             # Supabaseクライアント初期化
│
├── inputs/                    # データソース読み込み
│   ├── notion_reader.py      # models.user.get_entries() を使用
│   └── gdocs_reader.py       # models.user.get_entries() を使用
│
├── throughput/                # 分析ロジック
│   ├── domi_analyzer.py      # models.analysis_run を使用
│   └── aga_analyzer.py       # models.analysis_run を使用
│
├── outputs/                   # 配信ロジック
│   ├── email_sender.py       # models.delivery を使用
│   └── file_writer.py        # models.delivery を使用
│
├── main.py                    # エントリポイント（単一ユーザー実行）
├── read_spreadsheet_and_execute.py  # マルチユーザー実行
└── utils/
    ├── logger.py
    └── google_service.py
```

**設計思想**:

- **ドメインモデル**: ビジネスロジックと永続化ロジックを集約
- **レイヤー分離**: inputs/throughput/outputsは各ドメインモデルをimportして使用
- **再利用性**: ドメインモデルのメソッドを複数箇所から呼び出し可能
- **保守性**: ビジネスロジック変更時はmodels/内を修正するのみ

---

## 🛠️ 実装手順

### Step 1: Supabaseプロジェクト作成（10分）

1. [https://supabase.com](https://supabase.com/) にアクセス
2. 新規プロジェクト作成
3. プロジェクト名: `pickles-production`
4. データベースパスワード設定
5. リージョン選択: `Northeast Asia (Tokyo)`
6. Project URLとAPI Keyを取得:
    - Settings > API タブを開く
    - **Project URL** → `SUPABASE_URL` として使用
    - **Secret Key** (`sb_secret_...` で始まるキー) → `SUPABASE_KEY` として使用
    
    注: サーバーサイドアプリケーションなのでSecret Keyを使用します
    

---

### Step 2: マイグレーションファイル作成（10分）

Supabaseの最大活用のため、マイグレーションファイルで管理します。

**ディレクトリ作成**:

```bash
mkdir -p db/migrations
```

**1. `db/migrations/20241215000000_create_users_table.sql`**:

```sql
-- usersテーブル作成
create table public.users (
    id uuid primary key default gen_random_uuid(),
    email text unique not null,
    user_name text not null,

    -- データソース情報
    notion_api_key text,
    google_docs_url text,
    source_type text check (source_type in ('notion', 'gdocs', 'both')),

    -- メタデータ
    language text default 'japanese',
    is_active boolean default true,

    -- タイムスタンプ
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    last_analysis_at timestamptz
);

-- インデックス
create index idx_users_email on public.users(email);
create index idx_users_active on public.users(is_active) where is_active = true;
create index idx_users_last_analysis_at on public.users(last_analysis_at);

-- RLS (Row Level Security) 有効化
alter table public.users enable row level security;

-- ポリシー: サービスロールのみアクセス可能
create policy "Enable all access for service role"
  on public.users
  for all
  using (true);

-- コメント
comment on table public.users is 'ユーザー管理（Google Sheetsから同期）';
comment on column public.users.id is 'ユーザーUUID（永続的な識別子）';
comment on column public.users.email is 'Google Sheetsとの照合キー';
comment on column public.users.is_active is 'アクティブ状態（Sheetsから削除時false）';
```

**2. `db/migrations/20241215000001_create_analysis_runs_table.sql`**:

```sql
-- analysis_runsテーブル作成
create table public.analysis_runs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,

    -- 分析パラメータ
    analysis_type text not null check (analysis_type in ('domi', 'aga')),
    days_analyzed integer not null,
    source_used text not null check (source_used in ('notion', 'gdocs')),

    -- 分析結果
    content text,
    stats_summary text,

    -- 実行メタデータ
    status text not null check (status in ('pending', 'running', 'completed', 'failed')),
    error_message text,
    trigger_type text check (trigger_type in ('github_actions', 'manual', 'cron', 'api')),
    trigger_id text,

    -- タイムスタンプ
    created_at timestamptz default now(),
    completed_at timestamptz
);

-- インデックス
create index idx_analysis_runs_user_id on public.analysis_runs(user_id);
create index idx_analysis_runs_status on public.analysis_runs(status);
create index idx_analysis_runs_created_at on public.analysis_runs(created_at desc);

-- RLS有効化
alter table public.analysis_runs enable row level security;

-- ポリシー
create policy "Enable all access for service role"
  on public.analysis_runs
  for all
  using (true);

-- コメント
comment on table public.analysis_runs is '分析実行履歴';
comment on column public.analysis_runs.content is 'ユーザーに配信したレポート本文（Markdown形式）';
comment on column public.analysis_runs.stats_summary is '統計サマリー（例: 直近7日間: 21件、平均5092文字）';
```

**3. `db/migrations/20241215000002_create_deliveries_table.sql`**:

```sql
-- deliveriesテーブル作成
create table public.deliveries (
    id uuid primary key default gen_random_uuid(),
    analysis_run_id uuid not null references public.analysis_runs(id) on delete cascade,

    -- 配信方法
    delivery_method text not null check (delivery_method in (
        'email_html', 'email_text', 'console', 'file_text', 'file_html'
    )),
    email_to text,

    -- 配信結果
    status text not null check (status in ('pending', 'sent', 'failed')),
    error_message text,

    -- タイムスタンプ
    created_at timestamptz default now(),
    sent_at timestamptz
);

-- インデックス
create index idx_deliveries_analysis_run_id on public.deliveries(analysis_run_id);
create index idx_deliveries_status on public.deliveries(status);
create index idx_deliveries_created_at on public.deliveries(created_at desc);

-- RLS有効化
alter table public.deliveries enable row level security;

-- ポリシー
create policy "Enable all access for service role"
  on public.deliveries
  for all
  using (true);

-- コメント
comment on table public.deliveries is '配信履歴（配信方法のメタデータのみ）';
```

**4. `db/migrations/20241215000003_create_execution_history_view.sql`**:

```sql
-- 実行履歴ビュー作成
create or replace view public.execution_history as
select
    u.email,
    u.user_name,
    ar.analysis_type,
    ar.days_analyzed,
    ar.source_used,
    ar.status as analysis_status,
    ar.trigger_type,
    ar.trigger_id,
    ar.created_at as analysis_started_at,
    ar.completed_at as analysis_completed_at,
    d.delivery_method,
    d.email_to,
    d.status as delivery_status,
    d.sent_at as delivery_sent_at,
    d.error_message as delivery_error
from public.analysis_runs ar
join public.users u on ar.user_id = u.id
left join public.deliveries d on d.analysis_run_id = ar.id
order by ar.created_at desc;

-- コメント
comment on view public.execution_history is '実行履歴の統合ビュー（分析 + 配信）';
```

**マイグレーション適用方法**:

```bash
# Supabase CLIインストール（初回のみ）
brew install supabase/tap/supabase

# Supabaseプロジェクトにログイン
supabase login

# プロジェクトリンク
supabase link --project-ref YOUR_PROJECT_REF

# マイグレーション適用
supabase db push

# または、Supabase Dashboard > SQL Editorで各ファイルの内容を順番に実行
```

---

### Step 3: Supabaseクライアント作成（5分）

**`db/client.py`**:

```python
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
```

---

**`models/__init__.py`**:

```python
"""ドメインモデル"""
from models.user import User
from models.analysis_run import AnalysisRun
from models.delivery import Delivery

__all__ = ['User', 'AnalysisRun', 'Delivery']
```

**`models/user.py`**:

```python
"""Userドメインモデル"""
from typing import Optional, List, Dict
from datetime import datetime
from db.client import get_supabase_client
from utils.logger import logger

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

            logger.info(f"✓ ユーザー更新: {self.email}", "user")
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
            logger.success(f"✨ ユーザー作成: {self.email} ({self.id})", "user")

        return self

    def deactivate(self):
        """ユーザーを非アクティブ化"""
        self.is_active = False
        self.save()
        logger.warning(f"⚠️  ユーザー非アクティブ化: {self.email}", "user")

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
```

**`models/analysis_run.py`**:

```python
"""AnalysisRunドメインモデル"""
from typing import Optional
import os
from db.client import get_supabase_client
from utils.logger import logger

class AnalysisRun:
    """分析実行ドメインモデル

    責務:
    - 分析実行履歴の永続化
    - 分析結果の保存
    - ステータス管理
    """

    def __init__(
        self,
        user_id: str,
        analysis_type: str,
        days_analyzed: int,
        source_used: str,
        content: Optional[str] = None,
        stats_summary: Optional[str] = None,
        status: str = 'pending',
        error_message: Optional[str] = None,
        trigger_type: Optional[str] = None,
        trigger_id: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.user_id = user_id
        self.analysis_type = analysis_type
        self.days_analyzed = days_analyzed
        self.source_used = source_used
        self.content = content
        self.stats_summary = stats_summary
        self.status = status
        self.error_message = error_message
        self.trigger_type = trigger_type or self._detect_trigger_type()
        self.trigger_id = trigger_id or self._detect_trigger_id()

    def _detect_trigger_type(self) -> str:
        """トリガータイプを検出"""
        if os.getenv('GITHUB_ACTIONS'):
            return 'github_actions'
        return 'manual'

    def _detect_trigger_id(self) -> Optional[str]:
        """トリガーIDを検出"""
        if os.getenv('GITHUB_ACTIONS'):
            return os.getenv('GITHUB_RUN_ID')
        return None

    @classmethod
    def create(
        cls,
        user_id: str,
        analysis_type: str,
        days_analyzed: int,
        source_used: str
    ) -> 'AnalysisRun':
        """分析実行を開始（pendingステータスで作成）"""
        run = cls(
            user_id=user_id,
            analysis_type=analysis_type,
            days_analyzed=days_analyzed,
            source_used=source_used,
            status='pending'
        )
        run.save()
        return run

    def save(self) -> 'AnalysisRun':
        """分析実行を保存"""
        supabase = get_supabase_client()

        if self.id:
            # 更新
            result = supabase.table('analysis_runs').update({
                'status': self.status,
                'content': self.content,
                'stats_summary': self.stats_summary,
                'error_message': self.error_message,
                'completed_at': 'now()' if self.status in ['completed', 'failed'] else None
            }).eq('id', self.id).execute()
        else:
            # 新規作成
            result = supabase.table('analysis_runs').insert({
                'user_id': self.user_id,
                'analysis_type': self.analysis_type,
                'days_analyzed': self.days_analyzed,
                'source_used': self.source_used,
                'content': self.content,
                'stats_summary': self.stats_summary,
                'status': self.status,
                'error_message': self.error_message,
                'trigger_type': self.trigger_type,
                'trigger_id': self.trigger_id
            }).execute()

            self.id = result.data[0]['id']
            logger.info(f"分析実行開始: {self.id}", "analysis")

        return self

    def mark_running(self):
        """実行中に変更"""
        self.status = 'running'
        self.save()

    def mark_completed(self, content: str, stats_summary: str):
        """完了に変更"""
        self.status = 'completed'
        self.content = content
        self.stats_summary = stats_summary
        self.save()
        logger.success(f"✅ 分析完了: {self.id}", "analysis")

    def mark_failed(self, error_message: str):
        """失敗に変更"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
        logger.error(f"❌ 分析失敗: {self.id}", "analysis", error=error_message)
```

**`models/delivery.py`**:

```python
"""Deliveryドメインモデル"""
from typing import Optional
from db.client import get_supabase_client
from utils.logger import logger

class Delivery:
    """配信ドメインモデル

    責務:
    - 配信履歴の永続化
    - 配信ステータス管理
    """

    def __init__(
        self,
        analysis_run_id: str,
        delivery_method: str,
        email_to: Optional[str] = None,
        status: str = 'pending',
        error_message: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs
    ):
        self.id = id
        self.analysis_run_id = analysis_run_id
        self.delivery_method = delivery_method
        self.email_to = email_to
        self.status = status
        self.error_message = error_message

    @classmethod
    def create(
        cls,
        analysis_run_id: str,
        delivery_method: str,
        email_to: Optional[str] = None
    ) -> 'Delivery':
        """配信を作成"""
        delivery = cls(
            analysis_run_id=analysis_run_id,
            delivery_method=delivery_method,
            email_to=email_to,
            status='pending'
        )
        delivery.save()
        return delivery

    def save(self) -> 'Delivery':
        """配信を保存"""
        supabase = get_supabase_client()

        if self.id:
            # 更新
            result = supabase.table('deliveries').update({
                'status': self.status,
                'error_message': self.error_message,
                'sent_at': 'now()' if self.status == 'sent' else None
            }).eq('id', self.id).execute()
        else:
            # 新規作成
            result = supabase.table('deliveries').insert({
                'analysis_run_id': self.analysis_run_id,
                'delivery_method': self.delivery_method,
                'email_to': self.email_to,
                'status': self.status
            }).execute()

            self.id = result.data[0]['id']
            logger.info(f"配信開始: {self.delivery_method}", "delivery")

        return self

    def mark_sent(self):
        """送信完了に変更"""
        self.status = 'sent'
        self.save()
        logger.success(f"✅ 配信完了: {self.delivery_method}", "delivery")

    def mark_failed(self, error_message: str):
        """送信失敗に変更"""
        self.status = 'failed'
        self.error_message = error_message
        self.save()
        logger.error(f"❌ 配信失敗: {self.delivery_method}", "delivery",
                    error=error_message)
```

---

### Step 5: 環境変数設定（5分）

**ローカル開発用（`.env`）**:

```bash
# Supabase設定
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=sb_secret_xxxxx...

# 既存の環境変数
OPENAI_API_KEY=sk-...
NOTION_API_KEY=ntn_...
# ...
```

**GitHub Actions用（Secrets設定）**:

Settings > Secrets and variables > Actions > New repository secret

- `SUPABASE_URL`
- `SUPABASE_KEY`

---

### Step 6: 依存関係追加（5分）

`pyproject.toml`に追加:

```toml
[project]
dependencies = [
    "notion-client>=2.3.0",
    "openai>=1.84.0",
    "python-dotenv>=1.1.0",
    "google-auth>=2.29.0",
    "google-api-python-client>=2.137.0",
    "supabase>=2.0.0",  # 🆕 追加
]
```

インストール:

```bash
uv sync
```

---

### Step 7: read_spreadsheet_and_execute.py の実装（30分）

**ドメインモデルを活用した実装**:

```python
# read_spreadsheet_and_execute.py

import argparse
import sys
import os
import subprocess
from typing import List, Dict
from utils.logger import logger
from utils.google_service import get_google_service
from models.user import User

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

    logger.info(f"🎯 {user.user_name} の分析開始", "execution",
               email=user.email)

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
            logger.success(f"✅ {user.user_name} 完了", "execution")
            return True
        else:
            logger.error(f"❌ {user.user_name} 失敗", "execution",
                        error=result.stderr)
            return False

    except Exception as e:
        logger.error(f"❌ {user.user_name} エラー", "execution",
                    error=str(e))
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
            logger.info(f"[{i}/{total_count}] {user.user_name}", "execution")

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
```

**変更ポイント**:

- `SupabaseUserSync`クラスを削除 → `User.sync_from_google_sheets()` に統合
- `execute_pickles_for_user`は`User`オブジェクトを受け取る
- ドメインモデルのメソッドを活用（`user.to_dict()`, `user.update_last_analysis_at()`）
- ビジネスロジックがmodels/内に集約され、スクリプトはシンプルに

---

### Step 8: [main.py](http://main.py/) の修正（20分）

**ドメインモデルを活用した実装**:

```python
# main.py

import argparse
from models.analysis_run import AnalysisRun
from models.delivery import Delivery
from utils.logger import logger

# ... 既存のimport

def main():
    parser = argparse.ArgumentParser(
        description="Pickles - Personal Journal Analysis System"
    )

    # ユーザーID引数追加
    parser.add_argument("--user-id", help="User UUID from Supabase")

    # 既存の引数
    parser.add_argument("--source", choices=["notion", "gdocs"], default="notion")
    parser.add_argument("--analysis", choices=["domi", "aga"], default="domi")
    parser.add_argument("--delivery", default="console")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--email-to", help="Email address")
    # ... 他の引数

    args = parser.parse_args()

    analysis_run = None

    try:
        # ドメインモデルで分析実行を記録開始
        if args.user_id:
            analysis_run = AnalysisRun.create(
                user_id=args.user_id,
                analysis_type=args.analysis,
                days_analyzed=args.days,
                source_used=args.source
            )
            analysis_run.mark_running()

        # PicklesSystemで分析実行
        system = PicklesSystem(
            source_type=args.source,
            analysis_type=args.analysis,
            # ...
        )

        result = system.run_analysis()

        if result.success:
            # 分析完了を記録
            if analysis_run:
                analysis_run.mark_completed(
                    content=result.report_text,
                    stats_summary=result.stats_summary
                )

                # 配信履歴を記録
                delivery_methods = args.delivery.split(',')
                for method in delivery_methods:
                    delivery = Delivery.create(
                        analysis_run_id=analysis_run.id,
                        delivery_method=method.strip(),
                        email_to=args.email_to if 'email' in method else None
                    )

                    # 配信実行（既存のoutputs/ロジック）
                    try:
                        # ... 配信処理 ...
                        delivery.mark_sent()
                    except Exception as e:
                        delivery.mark_failed(str(e))

                logger.success(f"✅ 分析完了: {analysis_run.id}", "main")
        else:
            if analysis_run:
                analysis_run.mark_failed(result.error_message)

    except Exception as e:
        logger.error("分析エラー", "main", error=str(e))
        if analysis_run:
            analysis_run.mark_failed(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**変更ポイント**:

- `AnalysisRun.create()` で分析開始を記録
- `analysis_run.mark_running()` → `mark_completed()` でステータス遷移
- `Delivery.create()` で配信履歴を記録
- エラー時は `mark_failed()` で記録
- ドメインモデルがビジネスロジックを担当し、main.pyはオーケストレーションのみ

---

###Step 9: ローカルテスト（10分）

```bash
# 1. 環境変数確認
cat .env | grep SUPABASE

# 2. read_spreadsheet_and_execute.pyをテスト実行
python read_spreadsheet_and_execute.py \\
  --spreadsheet-id YOUR_SHEET_ID \\
  --analysis domi \\
  --delivery console

# 3. Supabaseで確認
# Dashboard > Table Editor > users
# 新規ユーザーがUUID付きで登録されているか確認

# 4. 分析実行履歴を確認
# Dashboard > Table Editor > analysis_runs
# ステータスがcompletedになっているか確認
```

---

### Step 10: GitHub Actions更新（5分）

`.github/workflows/pickles-report-production.yml`:

```yaml
name: Pickles Report Production

on:
  schedule:
    - cron: "0 22 * * 0"  # 毎週日曜22:00 UTC (月曜7:00 JST)
  workflow_dispatch:

jobs:
  analyze-users:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run analysis for all users
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_SERVICE_ACCOUNT_KEY: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_KEY }}
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_HOST: ${{ secrets.EMAIL_HOST }}
          EMAIL_PORT: ${{ secrets.EMAIL_PORT }}
          SPREADSHEET_ID_USERS_LIST: ${{ secrets.SPREADSHEET_ID_USERS_LIST }}
        run: |
          python read_spreadsheet_and_execute.py \\
            --spreadsheet-id $SPREADSHEET_ID_USERS_LIST \\
            --analysis domi \\
            --delivery email_html \\
            --days 7
```

---

## 🎯 トラブルシューティング

### Q: Google Sheetsに追加したのに分析が実行されない

**A**: 次のいずれかを確認:

1. 次回のGitHub Actions実行を待つ（毎週月曜7:00 JST）
2. 手動実行: Actions > pickles-report-production > Run workflow
3. ログを確認: ✨ 新規ユーザー登録のメッセージがあるか

### Q: Notion API Keyを変更したのに反映されない

**A**: 次回実行時に自動で更新されます。即座に反映したい場合は手動実行。

### Q: 誤って削除してしまった

**A**: Google Sheetsに再度追加すれば、既存のUUIDで復活します（is_active: true）。

### Q: ドメインモデルのimportエラーが出る

**A**: `models/__init__.py`が正しく作成されているか確認:

```python
from models.user import User
from models.analysis_run import AnalysisRun
from models.delivery import Delivery

__all__ = ['User', 'AnalysisRun', 'Delivery']
```

---

## 📈 将来の拡張（Phase 1以降）

### Phase 1で追加予定のテーブル

```sql
-- Phase 1a: 生ジャーナル蓄積
journals (
    id, user_id, source_type, raw_content,
    embedding vector(1536), created_at
)

-- Phase 1b: 発酵システム
fermentation_nodes (
    id, user_id, title, fermented_content,
    layer_type, embedding vector(1536)
)

fermentation_lineage (
    parent_id, child_id, relationship_type
)
```

**互換性**:

- `users.id` を外部キーとして参照可能
- `analysis_runs` は配信履歴として継続使用
- `fermentation_nodes` は発酵原料として新規追加

詳細は `FERMENTATION_DESIGN.md` を参照。

---

## 💡 設計判断の根拠

### 1. なぜGoogle Sheetsを継続使用するのか

**理由**:

- 使い慣れたUI（非技術者でも編集可能）
- 即座に変更可能（Supabase UIより手軽）
- 既存のワークフローを維持

**Supabaseの役割**:

- 実行履歴の永続化（分析ログ）
- UUID管理（将来の発酵システム用）

### 2. なぜドメインモデルアーキテクチャを採用したか

**理由**:

- **再利用性**: 同じビジネスロジックを複数箇所で使用可能
- **保守性**: ロジック変更時はmodels/内のみ修正
- **テスタビリティ**: ドメインモデルを独立してテスト可能
- **関心の分離**: 永続化ロジック（models/）と実行フロー（[main.py](http://main.py/), read_spreadsheet_and_execute.py）が分離

**例**:

```python
# ❌ 以前（ロジック分散）
# read_spreadsheet_and_execute.py内にSupabaseUserSyncクラス
# main.py内にsave_analysis_run関数

# ✅ 現在（ドメインモデル集約）
from models.user import User
from models.analysis_run import AnalysisRun

users = User.sync_from_google_sheets(sheets_data)
analysis_run = AnalysisRun.create(...)
```

### 3. なぜマイグレーションファイルで管理するか

**理由**:

- **バージョン管理**: スキーマ変更履歴をGitで追跡
- **再現性**: 新しい環境でも同じスキーマを構築可能
- **チーム協業**: スキーマ変更を明示的に共有
- **Supabase CLI連携**: `supabase db push`で一括適用

---

*最終更新: 2025-12-15バージョン: 3.0（ドメインモデル + マイグレーション版）*
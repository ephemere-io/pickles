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

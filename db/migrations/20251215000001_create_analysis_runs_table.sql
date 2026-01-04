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

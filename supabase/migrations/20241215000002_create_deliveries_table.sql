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

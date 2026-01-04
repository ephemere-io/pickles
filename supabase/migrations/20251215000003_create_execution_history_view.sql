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

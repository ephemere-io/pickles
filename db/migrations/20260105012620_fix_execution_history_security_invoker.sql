-- execution_historyをSecurity Invokerに変更（RLSが適用される）
DROP VIEW IF EXISTS public.execution_history;

CREATE VIEW public.execution_history
WITH (security_invoker = true)
AS
SELECT
    u.email,
    u.user_name,
    ar.analysis_type,
    ar.days_analyzed,
    ar.source_used,
    ar.status as analysis_status,
    ar.raw_data_count,
    ar.filtered_data_count,
    ar.avg_text_length,
    ar.trigger_type,
    ar.trigger_id,
    ar.created_at as analysis_started_at,
    ar.completed_at as analysis_completed_at,
    d.delivery_method,
    d.email_to,
    d.status as delivery_status,
    d.sent_at as delivery_sent_at,
    d.error_message as delivery_error
FROM public.analysis_runs ar
JOIN public.users u ON ar.user_id = u.id
LEFT JOIN public.deliveries d ON d.analysis_run_id = ar.id
ORDER BY ar.created_at DESC;

COMMENT ON VIEW public.execution_history IS '実行履歴の統合ビュー（Security Invoker - RLS適用）';

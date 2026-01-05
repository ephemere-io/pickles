-- analysis_runsをservice_roleのみアクセス可能に制限
-- anon keyが漏れてもcontentにはアクセスできない

-- 既存のポリシーを削除
DROP POLICY IF EXISTS "Enable all access for service role" ON analysis_runs;

-- service_roleのみ全操作可能
CREATE POLICY "Service role only" ON analysis_runs
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

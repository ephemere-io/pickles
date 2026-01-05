-- stats_summary (TEXT) を数値カラムに置き換え
-- 理由: クエリ・集計がしやすい形式に変更

ALTER TABLE analysis_runs
  ADD COLUMN raw_data_count INTEGER,
  ADD COLUMN filtered_data_count INTEGER,
  ADD COLUMN avg_text_length INTEGER;

-- コメント追加
COMMENT ON COLUMN analysis_runs.raw_data_count IS '取得データ数';
COMMENT ON COLUMN analysis_runs.filtered_data_count IS 'フィルタ後データ数（実際の分析対象）';
COMMENT ON COLUMN analysis_runs.avg_text_length IS '平均文字数';

-- 注: stats_summary カラムは後方互換性のため一旦残す
-- 将来的に削除する場合:
-- ALTER TABLE analysis_runs DROP COLUMN stats_summary;

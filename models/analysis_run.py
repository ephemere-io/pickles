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

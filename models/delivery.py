"""Deliveryドメインモデル"""
from typing import Optional
from supabase.client import get_supabase_client
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

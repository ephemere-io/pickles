"""
Outputs パッケージ - データ出力層

レポート生成、フォーマット、配信を担当
"""

from .report_generator import ReportDelivery, OutputError

__all__ = ["ReportDelivery", "OutputError"]

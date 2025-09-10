import os
import datetime
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils import logger, get_google_service, GoogleAPIError

load_dotenv()


class GdocsInputError(Exception):
    """Google Docs入力時のエラー"""
    pass


class GdocsInput:
    """Google Docsからデータを取得するInputクラス"""
    
    def __init__(self, service_account_key: str = None):
        # 統一されたGoogle APIサービスを使用
        try:
            self._google_service = get_google_service(service_account_key)
            self._service = self._google_service.get_docs_service()
            logger.info("Google Docs統合サービス初期化完了", "gdocs")
        except GoogleAPIError as e:
            logger.error("Google Docs統合サービス初期化失敗", "gdocs", error=str(e))
            raise GdocsInputError(f"Google Docs初期化エラー: {e}")
    
    
    def fetch_gdocs_documents(self, doc_url: str, days: int = 7) -> List[Dict[str, str]]:
        """Google Docsから日誌エントリを取得"""
        doc_id = self._extract_doc_id_from_url(doc_url)
        cutoff_date = self._calculate_cutoff_date(days)
        logger.start("Google Docs文書取得", "gdocs", doc_id=doc_id[:12]+"...", days=days, cutoff_date=cutoff_date)
        
        try:
            # アクセステストを実行
            if not self._google_service.test_docs_access(doc_id):
                raise GdocsInputError(f"Google Docsへのアクセスが拒否されました。ドキュメント共有設定を確認してください: {doc_id}")
            
            # ドキュメント内容を取得
            document = self._service.documents().get(documentId=doc_id).execute()
            logger.success("Google Docsアクセス成功", "gdocs", title=document.get('title', 'Unknown'))
            
            # ドキュメントをパースして日誌エントリを抽出
            entries = self._parse_document_content(document, cutoff_date)
            logger.complete("Google Docs文書取得", "gdocs", count=len(entries))
            
            return entries
            
        except GoogleAPIError as e:
            raise GdocsInputError(f"Google API統合エラー: {e}")
        except Exception as e:
            raise GdocsInputError(f"Google Docsデータ取得エラー: {e}")
    
    def _extract_doc_id_from_url(self, doc_url: str) -> str:
        """Google Docs URLからドキュメントIDを抽出"""
        # https://docs.google.com/document/d/DOCUMENT_ID/edit... の形式
        pattern = r'/document/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, doc_url)
        
        if match:
            doc_id = match.group(1)
            return doc_id
        else:
            raise GdocsInputError(f"無効なGoogle Docs URL: {doc_url}")
    
    def _parse_document_content(self, document: dict, cutoff_date: str) -> List[Dict[str, str]]:
        """ドキュメント内容をパースして日誌エントリを抽出"""
        content = document.get('body', {}).get('content', [])
        entries = []
        current_entry = None
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                text_content = self._extract_paragraph_text(paragraph)
                
                if not text_content.strip():
                    continue
                
                # 日付ヘッダーを検出（例: # 2025-01-15）
                date_match = re.match(r'^#\s*(\d{4}-\d{2}-\d{2})', text_content.strip())
                
                if date_match:
                    # 前のエントリを保存
                    if current_entry and self._is_recent_entry(current_entry['date'], cutoff_date):
                        entries.append(current_entry)
                    
                    # 新しいエントリを開始
                    entry_date = date_match.group(1)
                    current_entry = {
                        'date': entry_date,
                        'title': f"Journal Entry {entry_date}",
                        'text': ""
                    }
                
                elif current_entry:
                    # 現在のエントリにテキストを追加
                    if current_entry['text']:
                        current_entry['text'] += "\n"
                    current_entry['text'] += text_content
        
        # 最後のエントリを保存
        if current_entry and self._is_recent_entry(current_entry['date'], cutoff_date):
            entries.append(current_entry)
        
        # 日付の新しい順でソート
        entries.sort(key=lambda x: x['date'], reverse=True)
        
        logger.info("日誌エントリパース完了", "gdocs", 
                   total_entries=len(entries),
                   date_range=f"{entries[-1]['date']} ~ {entries[0]['date']}" if entries else "なし")
        
        return entries
    
    def _extract_paragraph_text(self, paragraph: dict) -> str:
        """段落からテキストを抽出"""
        elements = paragraph.get('elements', [])
        text_parts = []
        
        for element in elements:
            if 'textRun' in element:
                text_run = element['textRun']
                text_content = text_run.get('content', '')
                text_parts.append(text_content)
        
        return ''.join(text_parts)
    
    def _is_recent_entry(self, entry_date: str, cutoff_date: str) -> bool:
        """エントリが指定期間内かどうかを判定"""
        try:
            entry_datetime = datetime.datetime.strptime(entry_date, '%Y-%m-%d')
            cutoff_datetime = datetime.datetime.strptime(cutoff_date, '%Y-%m-%d')
            return entry_datetime >= cutoff_datetime
        except ValueError as e:
            logger.warning("日付パースエラー", "gdocs", 
                         entry_date=entry_date, error=str(e))
            return False
    
    @staticmethod
    def _calculate_cutoff_date(days: int) -> str:
        """カットオフ日付を計算"""
        return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
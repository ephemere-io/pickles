import os
import datetime
from typing import List, Dict, Optional
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()


class NotionInputError(Exception):
    """Notion入力時のエラー"""
    pass


class NotionInput:
    """Notionからデータを取得するInputクラス"""
    
    def __init__(self):
        self._client = Client(auth=os.getenv("NOTION_API_KEY"))
    
    
    def fetch_notion_documents(self, days: int = 7) -> List[Dict[str, str]]:
        """Notionから最近のドキュメントを取得（データベース優先、フォールバック付き）"""
        cutoff_date = self._calculate_cutoff_date(days)
        
        try:
            # まずデータベースからの取得を試行
            database_entries = self._try_fetch_database_entries(cutoff_date)
            if database_entries:
                return database_entries
            
            # データベースが見つからない場合は通常の検索を実行
            return self._fetch_page_search_results(cutoff_date)
            
        except Exception as e:
            raise NotionInputError(f"データ取得エラー: {e}")
    
    def _try_fetch_database_entries(self, cutoff_date: str) -> List[Dict[str, str]]:
        """データベースからエントリ取得を試行"""
        try:
            # 利用可能なデータベースを検索
            search_response = self._client.search(
                filter={"value": "database", "property": "object"}
            )
            
            databases = search_response.get("results", [])
            if not databases:
                return []
            
            # 最初に見つかったデータベースからエントリを取得
            database_id = databases[0].get("id")
            if not database_id:
                return []
            
            # データベースからエントリを取得
            return self._fetch_database_entries(database_id, cutoff_date)
            
        except Exception:
            return []  # データベースアクセスに失敗した場合は空リストを返す
    
    def _fetch_database_entries(self, database_id: str, cutoff_date: str) -> List[Dict[str, str]]:
        """指定されたデータベースからエントリを取得"""
        try:
            response = self._client.databases.query(
                database_id=database_id,
                filter={
                    "property": "Date",
                    "date": {"on_or_after": cutoff_date}
                },
                sorts=[{"property": "Date", "direction": "ascending"}]
            )
            
            pages = response.get("results", [])
            entries = []
            
            for page in pages:
                entry = self._extract_database_entry(page)
                if entry:
                    entries.append(entry)
            
            return entries
            
        except Exception:
            # Dateプロパティがない場合は、作成日でフィルタリング
            return self._fetch_database_entries_by_created_time(database_id, cutoff_date)
    
    def _fetch_database_entries_by_created_time(self, database_id: str, cutoff_date: str) -> List[Dict[str, str]]:
        """作成日でデータベースエントリを取得（Dateプロパティがない場合の代替）"""
        try:
            response = self._client.databases.query(
                database_id=database_id,
                sorts=[{"property": "Created time", "direction": "ascending"}]
            )
            
            pages = response.get("results", [])
            entries = []
            
            for page in pages:
                if self._is_recent_page(page, cutoff_date):
                    entry = self._extract_database_entry(page)
                    if entry:
                        entries.append(entry)
            
            return entries
            
        except Exception:
            return []
    
    def _fetch_page_search_results(self, cutoff_date: str) -> List[Dict[str, str]]:
        """通常のページ検索結果を取得"""
        response = self._client.search(
            filter={"value": "page", "property": "object"},
            sort={"direction": "descending", "timestamp": "last_edited_time"}
        )
        
        pages = response.get("results", [])
        documents = []
        
        for page in pages:
            if self._is_recent_page(page, cutoff_date):
                doc = self._extract_document_info(page)
                if doc:
                    documents.append(doc)
        
        return documents
    
    def _extract_date_property(self, page: dict) -> Optional[str]:
        """ページから日付プロパティを抽出"""
        properties = page.get("properties", {})
        
        # 日付プロパティをチェック
        if "Date" in properties and properties["Date"].get("date"):
            return properties["Date"]["date"]["start"]
        
        return None
    
    def _extract_document_info(self, page: dict) -> Optional[Dict[str, str]]:
        """ページから文書情報を抽出"""
        page_id = page.get("id", "")
        if not page_id:
            return None
        
        title = self._extract_page_title(page)
        content = self._get_page_content(page_id)
        
        # データベースエントリの場合は日付プロパティを優先
        date = self._extract_date_property(page) or page.get("created_time", "")[:10]
        
        return {
            "date": date,
            "title": title,
            "text": content
        }
    
    def _extract_database_entry(self, page: dict) -> Optional[Dict[str, str]]:
        """データベースページからエントリを抽出"""
        page_id = page.get("id", "")
        if not page_id:
            return None
        
        title = self._extract_page_title(page)
        content = self._get_page_content(page_id)
        
        # データベースエントリの日付プロパティを優先的に取得
        date = self._extract_date_property(page) or page.get("created_time", "")[:10]
        
        return {
            "date": date,
            "title": title,
            "text": content
        }
    
    def _extract_page_title(self, page: dict) -> str:
        """ページタイトルを抽出"""
        properties = page.get("properties", {})
        
        for prop_value in properties.values():
            if prop_value.get("type") == "title":
                title_array = prop_value.get("title", [])
                return "".join([t.get("plain_text", "") for t in title_array])
        
        return page.get("title", "Untitled")
    
    def _get_page_content(self, page_id: str) -> str:
        """ページのコンテンツを取得"""
        try:
            blocks_response = self._client.blocks.children.list(page_id)
            blocks = blocks_response.get("results", [])
            
            content_parts = []
            for block in blocks:
                text = self._extract_text_from_block(block)
                if text:
                    content_parts.append(text)
            
            return "\n".join(content_parts)
            
        except Exception:
            return ""  # エラー時は空文字を返す
    
    def _extract_text_from_block(self, block: dict) -> str:
        """ブロックからテキストを抽出"""
        block_type = block.get("type", "")
        text_blocks = ["paragraph", "heading_1", "heading_2", "heading_3", 
                       "bulleted_list_item", "numbered_list_item", "quote"]
        
        if block_type in text_blocks:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            return "".join([rt.get("plain_text", "") for rt in rich_text])
        
        return ""
    
    def _is_recent_page(self, page: dict, cutoff_date: str) -> bool:
        """ページが指定日以降に作成されたかチェック"""
        created_time = page.get("created_time", "")
        if not created_time:
            return False
        return created_time[:10] >= cutoff_date
    
    @staticmethod
    def _calculate_cutoff_date(days: int) -> str:
        """カットオフ日付を計算"""
        return (datetime.date.today() - datetime.timedelta(days=days)).isoformat() 
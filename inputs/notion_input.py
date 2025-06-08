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
    
    def fetch_database_entries(self, days: int = 7) -> List[Dict[str, str]]:
        """データベースから日誌エントリを取得"""
        database_id = os.getenv("NOTION_PAGE_ID")
        if not database_id:
            raise NotionInputError("NOTION_PAGE_IDが設定されていません")
        
        cutoff_date = self._calculate_cutoff_date(days)
        
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
            
        except Exception as e:
            raise NotionInputError(f"データベース取得エラー: {e}")
    
    def fetch_recent_documents(self, days: int = 7) -> List[Dict[str, str]]:
        """最近作成された全ドキュメントを取得"""
        cutoff_date = self._calculate_cutoff_date(days)
        
        try:
            response = self._client.search(
                filter={"value": "page", "property": "object"},
                sort={"direction": "descending", "timestamp": "created_time"}
            )
            
            pages = response.get("results", [])
            documents = []
            
            for page in pages:
                if self._is_recent_page(page, cutoff_date):
                    doc = self._extract_document_info(page)
                    if doc:
                        documents.append(doc)
            
            return documents
            
        except Exception as e:
            raise NotionInputError(f"検索エラー: {e}")
    
    def _extract_database_entry(self, page: dict) -> Optional[Dict[str, str]]:
        """データベースページからエントリデータを抽出"""
        properties = page.get("properties", {})
        
        # 日付プロパティをチェック
        if "Date" not in properties or not properties["Date"].get("date"):
            return None
        
        date = properties["Date"]["date"]["start"]
        
        # エントリテキストを探す
        content = ""
        if "Entry" in properties and "rich_text" in properties["Entry"]:
            texts = properties["Entry"]["rich_text"]
            content = ''.join([rt.get("plain_text", "") for rt in texts])
        else:
            # 他のリッチテキストプロパティを探す
            for name, prop in properties.items():
                if name != "Date" and "rich_text" in prop:
                    texts = prop["rich_text"]
                    content = ''.join([rt.get("plain_text", "") for rt in texts])
                    break
        
        return {"date": date, "text": content} if content else None
    
    def _extract_document_info(self, page: dict) -> Optional[Dict[str, str]]:
        """ページから文書情報を抽出"""
        page_id = page.get("id", "")
        if not page_id:
            return None
        
        title = self._extract_page_title(page)
        content = self._get_page_content(page_id)
        
        return {
            "date": page.get("created_time", "")[:10],
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
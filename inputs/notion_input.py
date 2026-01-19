import os
import datetime
from typing import List, Dict, Optional
from notion_client import Client
from dotenv import load_dotenv
from utils import logger
from models.user import mask_name

load_dotenv()


class NotionInputError(Exception):
    """Notion入力時のエラー"""
    pass


class NotionInput:
    """Notionからデータを取得するInputクラス"""
    
    def __init__(self, api_key: str = None):
        self._api_key = api_key or os.getenv("NOTION_API_KEY")
        
        # デバッグ: APIキーの状態を確認
        if self._api_key:
            api_key_masked = f"{self._api_key[:4]}...{self._api_key[-4:]}"
            logger.info("Notion APIキー設定確認", "notion", key_length=len(self._api_key), masked_key=api_key_masked)
        else:
            logger.warning("Notion APIキーが設定されていません", "notion")
        
        # テストモードの場合はモックを使用
        if os.getenv('PICKLES_TEST_MODE') == '1':
            from tests.fixtures.mock_handlers import mock_notion_api
            self._client = mock_notion_api()(auth=self._api_key)
        else:
            self._client = Client(auth=self._api_key)
        
        self._check_api_connection()
    
    
    def fetch_notion_documents(self, days: int = 7) -> List[Dict[str, str]]:
        """Notionから最近のドキュメントを取得（データベース優先、フォールバック付き）"""
        cutoff_date = self._calculate_cutoff_date(days)
        logger.start("Notion文書取得", "notion", days=days, cutoff_date=cutoff_date)
        
        try:
            # まずデータベースからの取得を試行
            database_entries = self._try_fetch_database_entries(cutoff_date)
            if database_entries:
                logger.complete("データベースエントリ取得", "notion", count=len(database_entries))
                return database_entries
            
            # データベースが見つからない場合は通常の検索を実行
            logger.info("データベース未発見、ページ検索にフォールバック", "notion")
            page_results = self._fetch_page_search_results(cutoff_date)
            logger.complete("ページ検索結果取得", "notion", count=len(page_results))
            return page_results
            
        except Exception as e:
            raise NotionInputError(f"データ取得エラー: {e}")
    
    def _try_fetch_database_entries(self, cutoff_date: str) -> List[Dict[str, str]]:
        """データベースからエントリ取得を試行"""
        try:
            # 利用可能なデータベースを検索
            logger.debug("データベース検索開始", "notion")
            search_response = self._client.search(
                filter={"value": "database", "property": "object"}
            )
            
            databases = search_response.get("results", [])
            logger.info("データベース検索完了", "notion", found_count=len(databases))
            
            if not databases:
                logger.warning("データベースが見つからない", "notion")
                return []
            
            # 最初に見つかったデータベースからエントリを取得
            database_id = databases[0].get("id")
            database_title = databases[0].get("title", [])
            db_name = database_title[0].get("plain_text", "Unknown") if database_title else "Unknown"
            logger.info("データベース選択", "notion", db_name=db_name, db_id=database_id[:12]+"...")
            
            if not database_id:
                return []
            
            # データベースからエントリを取得
            return self._fetch_database_entries(database_id, cutoff_date)
            
        except Exception as e:
            logger.error("データベースアクセスエラー", "notion", error=str(e))
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
        """通常のページ検索結果を取得（日付による早期終了付き）"""
        logger.debug("ページ検索開始", "notion", cutoff_date=cutoff_date)
        
        all_pages = []
        has_more = True
        start_cursor = None
        consecutive_old_pages = 0  # 連続して古いページの数
        max_consecutive_old = 50   # 連続して古いページがこの数を超えたら終了
        max_total_pages = 500      # 最大取得ページ数
        
        while has_more and len(all_pages) < max_total_pages:
            params = {
                "filter": {"value": "page", "property": "object"},
                "sort": {"direction": "descending", "timestamp": "last_edited_time"},
                "page_size": 100  # 最大値
            }
            
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = self._client.search(**params)
            pages = response.get("results", [])
            
            # 各ページの日付をチェックして早期終了判定
            recent_pages_in_batch = 0
            for page in pages:
                is_recent = self._is_recent_page(page, cutoff_date)
                if is_recent:
                    recent_pages_in_batch += 1
                    consecutive_old_pages = 0  # 最近のページが見つかったらカウンターリセット
                else:
                    consecutive_old_pages += 1
                
                # 連続して古いページが続いたら早期終了
                if consecutive_old_pages >= max_consecutive_old:
                    logger.info("連続古ページによる早期終了", "notion", 
                              consecutive_old=consecutive_old_pages, 
                              total_fetched=len(all_pages) + len(pages[:pages.index(page)]))
                    all_pages.extend(pages[:pages.index(page) + 1])
                    has_more = False
                    break
            
            if has_more:  # 早期終了していない場合のみページを追加
                all_pages.extend(pages)
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
                
                logger.debug("ページ検索進捗", "notion", 
                           current_count=len(all_pages), 
                           recent_in_batch=recent_pages_in_batch,
                           consecutive_old=consecutive_old_pages,
                           has_more=has_more)
        
        # 最大ページ数に達した場合の警告
        if len(all_pages) >= max_total_pages:
            logger.warning("最大取得ページ数に到達", "notion", max_pages=max_total_pages)
        
        logger.info("ページ検索完了", "notion", total_pages=len(all_pages))
        
        documents = []
        filtered_count = 0
        recent_but_no_content = 0
        
        for i, page in enumerate(all_pages):
            page_title = self._extract_page_title(page)
            created_time = page.get("created_time", "")
            last_edited = page.get("last_edited_time", "")
            is_recent = self._is_recent_page(page, cutoff_date)
            
            # 最初の10件と最近のページの詳細を表示
            if i < 10 or is_recent:
                logger.debug("ページ詳細情報", "notion", 
                           page_num=i+1, title=page_title[:30], 
                           created=created_time[:10], edited=last_edited[:10], 
                           is_recent=is_recent)
            
            if is_recent:
                doc = self._extract_document_info(page)
                if doc:
                    # コンテンツが空でないかチェック
                    if doc.get("text", "").strip():
                        documents.append(doc)
                        logger.debug("ドキュメント追加", "notion", chars=len(doc['text']))
                    else:
                        recent_but_no_content += 1
                        logger.debug("コンテンツ空により除外", "notion")
                else:
                    logger.debug("ドキュメント情報抽出失敗", "notion")
            else:
                filtered_count += 1
        
        logger.info("Notion文書取得統計", "notion", 
                   total_pages=len(all_pages),
                   filtered_by_date=filtered_count, 
                   recent_no_content=recent_but_no_content, 
                   final_documents=len(documents))
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
        
        # ページタイプを確認
        parent = page.get("parent", {})
        parent_type = parent.get("type", "")
        logger.debug("ページタイプ確認", "notion", type=parent_type, page_id=page_id[:12]+"...")
        
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
        
        # データベースページのタイトル抽出（プロパティから）
        title = self._extract_database_title(page)
        
        # まずプロパティからコンテンツを抽出
        property_content = self._extract_database_content_from_properties(page)
        
        # 次にページ本体のコンテンツを取得
        page_content = self._get_page_content(page_id)
        
        # プロパティとページ本体のコンテンツを結合
        content = ""
        if property_content:
            content = property_content
        if page_content:
            content = f"{content}\n\n{page_content}" if content else page_content
        
        # デバッグ情報
        if not content.strip():
            logger.warning("データベースエントリのコンテンツが空", "notion", 
                          page_id=page_id[:12]+"...", 
                          has_property_content=bool(property_content), 
                          has_page_content=bool(page_content))
        
        # データベースエントリの日付プロパティを優先的に取得
        date = self._extract_date_property(page) or page.get("created_time", "")[:10]
        
        return {
            "date": date,
            "title": title,
            "text": content
        }
    
    def _extract_database_title(self, page: dict) -> str:
        """データベースページのタイトルを抽出"""
        properties = page.get("properties", {})
        
        # まずタイトルプロパティを探す
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title" and prop_value.get("title"):
                title_array = prop_value.get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_array])
                if title.strip():
                    return title
        
        # タイトルプロパティがない場合は他のテキストプロパティを探す
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "rich_text" and prop_value.get("rich_text"):
                rich_text_array = prop_value.get("rich_text", [])
                text = "".join([t.get("plain_text", "") for t in rich_text_array])
                if text.strip():
                    return f"{prop_name}: {text}"
        
        # プロパティから何も取得できない場合はデフォルト
        return "データベースエントリ"
    
    def _extract_database_content_from_properties(self, page: dict) -> str:
        """データベースページのプロパティからコンテンツを抽出"""
        properties = page.get("properties", {})
        content_parts = []
        
        # すべてのプロパティをチェック
        for prop_name, prop_value in properties.items():
            prop_type = prop_value.get("type", "")
            
            # タイトル以外のテキスト系プロパティからコンテンツを抽出
            if prop_type == "rich_text" and prop_value.get("rich_text"):
                rich_text_array = prop_value.get("rich_text", [])
                text = "".join([rt.get("plain_text", "") for rt in rich_text_array])
                if text.strip():
                    content_parts.append(f"{prop_name}: {text}")
            
            # セレクトプロパティ
            elif prop_type == "select" and prop_value.get("select"):
                select_value = prop_value.get("select", {}).get("name", "")
                if select_value:
                    content_parts.append(f"{prop_name}: {select_value}")
            
            # マルチセレクトプロパティ
            elif prop_type == "multi_select" and prop_value.get("multi_select"):
                values = [opt.get("name", "") for opt in prop_value.get("multi_select", [])]
                if values:
                    content_parts.append(f"{prop_name}: {', '.join(values)}")
            
            # URLプロパティ
            elif prop_type == "url" and prop_value.get("url"):
                url = prop_value.get("url", "")
                if url:
                    content_parts.append(f"{prop_name}: {url}")
            
            # メールプロパティ
            elif prop_type == "email" and prop_value.get("email"):
                email = prop_value.get("email", "")
                if email:
                    content_parts.append(f"{prop_name}: {email}")
            
            # 電話番号プロパティ
            elif prop_type == "phone_number" and prop_value.get("phone_number"):
                phone = prop_value.get("phone_number", "")
                if phone:
                    content_parts.append(f"{prop_name}: {phone}")
            
            # 数値プロパティ
            elif prop_type == "number" and prop_value.get("number") is not None:
                number = prop_value.get("number")
                content_parts.append(f"{prop_name}: {number}")
            
            # チェックボックスプロパティ
            elif prop_type == "checkbox":
                checked = prop_value.get("checkbox", False)
                content_parts.append(f"{prop_name}: {'✓' if checked else '✗'}")
        
        # デバッグ: プロパティの内容
        if content_parts:
            logger.debug("プロパティからコンテンツ抽出", "notion", property_count=len(content_parts))
        
        return "\n".join(content_parts)
    
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
                if text.strip():  # 空白のみのテキストを除外
                    content_parts.append(text.strip())
            
            content = "\n".join(content_parts)
            
            # デバッグ: コンテンツの取得状況をログ出力
            if not content.strip():
                logger.debug("ページコンテンツが空", "notion", page_id=page_id[:12]+"...")
                if blocks:
                    logger.debug("ブロック詳細", "notion", 
                               block_count=len(blocks), 
                               first_block_type=blocks[0].get('type', 'unknown'))
            else:
                logger.debug("ページコンテンツ取得成功", "notion", 
                           page_id=page_id[:12]+"...", content_length=len(content))
            
            return content
            
        except Exception as e:
            logger.error("ページコンテンツ取得エラー", "notion", 
                        page_id=page_id[:12]+"...", error=str(e))
            return ""  # エラー時は空文字を返す
    
    def _extract_text_from_block(self, block: dict) -> str:
        """ブロックからテキストを抽出（拡張版）"""
        block_type = block.get("type", "")
        
        # サポートするブロック型を拡張
        text_blocks = [
            "paragraph", "heading_1", "heading_2", "heading_3", 
            "bulleted_list_item", "numbered_list_item", "quote",
            "callout", "code", "divider", "toggle"
        ]
        
        if block_type in text_blocks:
            block_data = block.get(block_type, {})
            rich_text = block_data.get("rich_text", [])
            text = "".join([rt.get("plain_text", "") for rt in rich_text])
            
            # calloutの場合はアイコンも含める
            if block_type == "callout" and block_data.get("icon"):
                icon = block_data.get("icon", {})
                if icon.get("type") == "emoji":
                    text = f"{icon.get('emoji', '')} {text}"
            
            return text
        
        # テーブル行の処理
        elif block_type == "table_row":
            cells = block.get("table_row", {}).get("cells", [])
            cell_texts = []
            for cell in cells:
                cell_text = "".join([rt.get("plain_text", "") for rt in cell])
                cell_texts.append(cell_text)
            return " | ".join(cell_texts)
        
        # 他のブロック型も処理
        elif block_type in ["bookmark", "link_preview"]:
            url = block.get(block_type, {}).get("url", "")
            return f"[Link: {url}]" if url else ""
        
        return ""
    
    def _is_recent_page(self, page: dict, cutoff_date: str) -> bool:
        """ページが指定日以降に作成または編集されたかチェック"""
        # 日付プロパティがある場合はそれを優先
        date_prop = self._extract_date_property(page)
        if date_prop:
            return date_prop >= cutoff_date
        
        # 作成日と最終編集日のどちらかが最近ならOK
        created_time = page.get("created_time", "")
        last_edited_time = page.get("last_edited_time", "")
        
        if not created_time and not last_edited_time:
            logger.warning("ページに時刻情報なし", "notion")
            return False
        
        created_date = created_time[:10] if created_time else "1900-01-01"
        edited_date = last_edited_time[:10] if last_edited_time else "1900-01-01"
        
        # どちらかの日付がカットオフ以降なら含める
        is_recent = created_date >= cutoff_date or edited_date >= cutoff_date
        
        # デバッグ: 日付比較の詳細（除外される場合のみ）
        if not is_recent and created_date != "1900-01-01":
            logger.debug("ページを日付で除外", "notion", 
                        created=created_date, edited=edited_date, cutoff=cutoff_date)
        
        return is_recent
    
    def _check_api_connection(self):
        """API接続を確認"""
        try:
            # ユーザー情報を取得してAPIキーが有効か確認
            user_info = self._client.users.me()
            logger.success("Notion API接続成功", "notion", user=mask_name(user_info.get('name', 'Unknown User')))
            
            # 簡単な検索を実行してアクセス権限を確認
            test_search = self._client.search(
                filter={"value": "page", "property": "object"},
                page_size=1
            )
            accessible_pages = len(test_search.get("results", []))
            logger.info("Notionアクセス権限確認", "notion", accessible_pages=f"{accessible_pages}+")
            
        except Exception as e:
            logger.error("Notion API接続エラー", "notion", error=str(e))
            raise NotionInputError(f"Notion API接続エラー: {e}")
    
    @staticmethod
    def _calculate_cutoff_date(days: int) -> str:
        """カットオフ日付を計算"""
        return (datetime.date.today() - datetime.timedelta(days=days)).isoformat() 
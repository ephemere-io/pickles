"""テスト用モックハンドラー"""
import os
import json
from unittest.mock import Mock
from functools import lru_cache


@lru_cache(maxsize=10)
def _load_cached_mock_data(file_path: str):
    """モックデータJSONファイルをキャッシュ付きで読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_available_mock_data():
    """tests/fixtures/mock_data/notion/ にある利用可能なモックデータを読み込み"""
    
    notion_dir = os.path.join(os.path.dirname(__file__), "mock_data", "notion")
    
    # ディレクトリ存在チェック（早期リターン）
    if not os.path.exists(notion_dir):
        raise FileNotFoundError(
            f"Mock data directory not found: {notion_dir}. "
            "Please run 'uv run python capture_mock.py' to generate test data."
        )
    
    # JSONファイル取得
    json_files = [f for f in os.listdir(notion_dir) if f.endswith('.json')]
    
    # ファイル存在チェック（早期リターン）
    if not json_files:
        raise FileNotFoundError(
            f"No mock data files found in {notion_dir}. "
            "Please run 'uv run python capture_mock.py' to generate test data."
        )
    
    # モックファイル選択（環境変数優先）
    specific_file = os.environ.get('PICKLES_TEST_SPECIFIC_MOCK_FILE')
    mock_file = specific_file if specific_file and specific_file in json_files else sorted(json_files)[0]
    
    # ファイル読み込み
    file_path = os.path.join(notion_dir, mock_file)
    mock_data = _load_cached_mock_data(file_path)
    
    print(f"[MOCK] Using available mock data: {mock_file} ({len(mock_data.get('documents', []))} documents)")
    return mock_data

def mock_notion_api():
    """Notion APIのモック - 利用可能なモックデータを使用"""
    # 利用可能なモックデータを使用（シンプル）
    mock_data = load_available_mock_data()
    
    class MockNotionClient:
        def __init__(self, auth=None):
            self.auth = auth
            self.users = Mock()
            self.search = Mock()
            self.databases = Mock()
            self.blocks = Mock()
            self._mock_data = mock_data
            
            # users.me()のモック - 実際のPicklesユーザー情報を使用
            self.users.me = Mock(return_value={
                "id": "test-user-pickles",
                "name": "Pickles", 
                "type": "person",
                "person": {
                    "email": "pickles@example.com"
                }
            })
            
            # search()のモック
            def mock_search(**kwargs):
                filter_obj = kwargs.get('filter', {})
                
                # データベース検索の場合（早期リターン）
                if filter_obj.get('value') == 'database':
                    return self._mock_data.get("api_responses", {}).get("search_databases", {
                        "results": [],
                        "has_more": False
                    })
                
                # ページ検索の場合
                documents = self._mock_data.get("documents", [])
                page_size = kwargs.get('page_size', 100)
                
                # ドキュメントをページ形式に変換
                results = [
                    {
                        "object": "page",
                        "id": f"page-{hash(doc['title'])}",
                        "created_time": doc.get("date", "2024-01-01") + "T00:00:00.000Z",
                        "last_edited_time": doc.get("date", "2024-01-01") + "T12:00:00.000Z",
                        "properties": {
                            "title": {
                                "type": "title",
                                "title": [{"plain_text": doc["title"]}]
                            }
                        }
                    }
                    for doc in documents
                ]
                
                return {
                    "results": results[:page_size],
                    "has_more": len(results) > page_size
                }
            
            self.search = Mock(side_effect=mock_search)
            
            # databases.query()のモック
            self.databases.query = Mock(return_value={
                "results": [],
                "has_more": False
            })
            
            # blocks.children.list()のモック
            def mock_blocks_list(page_id):
                # 対応するドキュメントを検索
                matching_doc = None
                for doc in self._mock_data.get("documents", []):
                    if f"page-{hash(doc['title'])}" == page_id:
                        matching_doc = doc
                        break
                
                # ドキュメントが見つからない場合（早期リターン）
                if not matching_doc:
                    return {"results": []}
                
                # テキストをブロックに変換
                text_lines = matching_doc["text"].split("\n")
                blocks = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"plain_text": line}]
                        }
                    }
                    for line in text_lines
                    if line.strip()
                ]
                
                return {"results": blocks}
            
            self.blocks.children = Mock()
            self.blocks.children.list = Mock(side_effect=mock_blocks_list)
    
    return MockNotionClient


def mock_openai_api():
    """OpenAI APIのモック"""
    class MockOpenAI:
        def __init__(self, api_key=None):
            self.api_key = api_key
            
            # responses.create のモックレスポンス
            self.responses = Mock()
            
            # モックレスポンスオブジェクト
            mock_response = Mock()
            
            # to_dict() メソッドのモック
            mock_response.to_dict = Mock(return_value={
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "text": "• モックデータでの分析結果\n• 実際のNotionデータが使用されています\n• テストが正常に動作しています\n\n統計情報:\n- ドキュメント数: 10件\n- 平均文字数: 350文字\n- カテゴリ: ライフスタイル, テクノロジー"
                            }
                        ]
                    }
                ]
            })
            
            # createメソッドのモック
            self.responses.create = Mock(return_value=mock_response)
    
    return MockOpenAI



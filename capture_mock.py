"""複数のAPIキーに対応したモックテストデータ生成スクリプト"""
import os
import sys
import json
import datetime
from typing import Dict, List

# プロジェクトのパスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inputs.notion_input import NotionInput
from utils import logger

def generate_mock_data_for_api_key(api_key: str):
    """指定されたAPIキーのモックデータを生成"""
    
    print(f"Generating mock data for API key: {api_key[:8]}...{api_key[-4:]}")
    
    # notionディレクトリを作成
    notion_dir = "tests/fixtures/mock_data/notion"
    os.makedirs(notion_dir, exist_ok=True)
    
    try:
        # 環境変数にAPIキーを一時的に設定
        original_key = os.environ.get("NOTION_API_KEY")
        os.environ["NOTION_API_KEY"] = api_key
        
        try:
            # 実際のAPIを使用
            print("Fetching data from Notion API...")
            notion = NotionInput()
            documents = notion.fetch_notion_documents(days=7)
            
            if not documents:
                print("⚠️ No documents found, creating sample data...")
                documents = [
                    {
                        "date": "2025-08-10",
                        "title": f"Sample Document for {api_key[-8:]}",
                        "text": "This is a sample document for testing."
                    }
                ]
        except Exception as e:
            print(f"⚠️ API call failed ({e}), creating sample data...")
            documents = [
                {
                    "date": "2025-08-10",
                    "title": f"Sample Document for {api_key[-8:]}",
                    "text": "This is a sample document for testing."
                },
                {
                    "date": "2025-08-09", 
                    "title": f"Another Sample for {api_key[-8:]}",
                    "text": "Another sample document."
                }
            ]
        finally:
            # 元の環境変数を復元
            if original_key:
                os.environ["NOTION_API_KEY"] = original_key
            else:
                os.environ.pop("NOTION_API_KEY", None)
        
        # データ構造
        mock_data = {
            "metadata": {
                "captured_at": datetime.datetime.now().isoformat(),
                "api_key_suffix": api_key[-8:],
                "document_count": len(documents)
            },
            "documents": documents
        }
        
        # APIキー名でJSONファイルに保存
        output_file = os.path.join(notion_dir, f"{api_key}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Mock data saved: {len(documents)} documents -> {output_file}")
        return mock_data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def generate_all_mock_data():
    """全てのAPIキーのモックデータを生成"""
    
    # 環境変数からAPIキーを取得
    api_key = os.getenv('NOTION_API_KEY')
    if not api_key:
        print("Error: NOTION_API_KEY not found in environment variables")
        return []
    
    api_keys = [api_key]
    
    print(f"Generating mock data for {len(api_keys)} API keys...\n")
    
    results = []
    for i, api_key in enumerate(api_keys, 1):
        print(f"[{i}/{len(api_keys)}] Processing API key...")
        result = generate_mock_data_for_api_key(api_key)
        if result:
            results.append(result)
        print()
    
    print(f"✅ Generated {len(results)} mock data files")
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 特定のAPIキーのみ生成
        api_key = sys.argv[1]
        data = generate_mock_data_for_api_key(api_key)
        if data:
            print(f"\n✅ Mock data generation complete for {api_key[-8:]}")
            print(f"Generated {data['metadata']['document_count']} documents")
    else:
        # 全てのAPIキーで生成
        results = generate_all_mock_data()
        if results:
            print("\n✅ All mock data generation complete")
            total_docs = sum(r['metadata']['document_count'] for r in results)
            print(f"Generated {len(results)} files with {total_docs} total documents")
            print("\nGenerated files:")
            for result in results:
                suffix = result['metadata']['api_key_suffix']
                count = result['metadata']['document_count']
                print(f"  - {suffix}: {count} documents")
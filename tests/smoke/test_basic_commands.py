"""基本コマンドの動作確認テスト"""
import pytest
import os
from tests.fixtures.test_config import (
    run_main_command, 
    assert_command_success, 
    get_all_mock_files,
    mock_environment,
    assert_mock_data_used,
    assert_system_initialization
)


@pytest.mark.smoke
def test_help_command():
    """ヘルプコマンドが正常に動作する（モックデータ非依存）"""
    result = run_main_command(["--help"], use_mocks=False)
    assert_command_success(result, "使用方法")


@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
def test_basic_console_execution(mock_file):
    """基本起動と完全な実行確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command(["--delivery", "console", "--days", "45"], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert_mock_data_used(result, mock_file)
        assert_system_initialization(result)
        
        # モックを使用しているため、分析完了まで確認可能
        assert "Notion API接続成功" in result.stdout, "Notion API connection not successful"
        assert "レポート配信処理開始" in result.stdout, "Report delivery not started"
        
        print(f"\n✅ Basic console test passed for {mock_file}")


@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
def test_file_output_execution(mock_file):
    """ファイル出力オプションの完全動作確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command(["--delivery", "file_text", "--days", "45"], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert_mock_data_used(result, mock_file)
        assert_system_initialization(result)
        
        # ファイル出力の完了確認
        assert "レポート配信処理開始" in result.stdout, "Report delivery not started"
        assert "file_text" in result.stdout, "File output method not used"
        
        print(f"\n✅ File output test passed for {mock_file}")



@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
def test_days_option(mock_file):
    """日数指定オプションの完全動作確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command(["--days", "45", "--delivery", "console"], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert_mock_data_used(result, mock_file)
        assert_system_initialization(result)
        
        # 日数指定が反映されているか確認
        assert "days=45" in result.stdout, "Days parameter not logged correctly"
        
        print(f"\n✅ Days option test passed for {mock_file}")


@pytest.mark.smoke
def test_mock_data_availability():
    """全モックデータファイルの利用可能性確認"""
    import json
    import glob
    
    notion_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             "fixtures", "mock_data", "notion")
    json_files = sorted(glob.glob(os.path.join(notion_dir, "*.json")))
    
    print("\n📊 Mock Data Summary:")
    print("-" * 60)
    
    total_documents = 0
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mock_file = os.path.splitext(os.path.basename(json_file))[0]
        doc_count = data['metadata']['document_count']
        total_documents += doc_count
        
        print(f"Mock File: {mock_file}")
        print(f"  Documents: {doc_count}")
        print(f"  Captured: {data['metadata']['captured_at'][:10]}")
        
        # 最初のドキュメントのタイトルを表示
        if data['documents']:
            first_title = data['documents'][0]['title']
            print(f"  First doc: {first_title[:50]}...")
        print()
    
    print(f"Total mock data files: {len(json_files)}")
    print(f"Total documents: {total_documents}")
    print("-" * 60)
    
    # テストとして成功を返す
    assert len(json_files) > 0, "No mock data files found"
    assert total_documents > 0, "No documents in mock data"
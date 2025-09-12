"""エラーハンドリングテスト"""
import pytest
from tests.fixtures.test_config import (
    run_main_command, 
    get_all_mock_files,
    mock_environment,
    assert_mock_data_used,
    assert_command_failure_with_message
)


@pytest.mark.smoke
def test_invalid_analysis_type():
    """無効な分析タイプを指定した場合のエラーハンドリング（モック使用）"""
    # 最初のモックファイルを使用してエラーテストを実行
    mock_files = get_all_mock_files()
    if not mock_files:
        pytest.skip("No mock data available")
    
    with mock_environment(mock_files[0]):
        result = run_main_command([
            "--analysis", "invalid_type",
            "--delivery", "console"
        ], timeout=10, use_mocks=True)
        
        assert_command_failure_with_message(result, ["error", "エラー", "invalid", "無効"])
        print("\n✅ Invalid analysis type error handling test passed")


@pytest.mark.smoke
def test_invalid_delivery_method():
    """無効な配信方法を指定した場合のエラーハンドリング（モック使用）"""
    mock_files = get_all_mock_files()
    if not mock_files:
        pytest.skip("No mock data available")
    
    with mock_environment(mock_files[0]):
        result = run_main_command([
            "--analysis", "domi",
            "--delivery", "invalid_method"
        ], timeout=10, use_mocks=True)
        
        assert_command_failure_with_message(result, ["error", "エラー", "invalid", "無効"])
        print("\n✅ Invalid delivery method error handling test passed")


@pytest.mark.smoke
def test_invalid_days_value():
    """無効な日数を指定した場合のエラーハンドリング（モック使用）"""
    mock_files = get_all_mock_files()
    if not mock_files:
        pytest.skip("No mock data available")
    
    with mock_environment(mock_files[0]):
        result = run_main_command([
            "--analysis", "domi",
            "--delivery", "console",
            "--days", "invalid"
        ], timeout=5, use_mocks=True)
        
        assert_command_failure_with_message(result, ["error", "エラー", "invalid", "無効"])
        print("\n✅ Invalid days value error handling test passed")




@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
def test_error_resilience_with_all_mock_files(mock_file):
    """全モックデータで基本的なエラーリジリエンスを確認"""
    with mock_environment(mock_file):
        # 正常実行を確認（エラーが発生しないことを確認）
        result = run_main_command([
            "--analysis", "domi",
            "--delivery", "console",
            "--days", "45"
        ], timeout=30, use_mocks=True)
        
        # 正常終了することを確認
        assert result.returncode == 0, f"Command should succeed: {result.stderr}"
        assert_mock_data_used(result)
        
        # エラーが発生していないことを確認
        output = result.stdout.lower() + result.stderr.lower()
        assert not any(word in output for word in ["error", "exception", "failed"]), \
            f"Unexpected error found in output for {mock_file}"
        
        print(f"\n✅ Error resilience test passed for {mock_file}")
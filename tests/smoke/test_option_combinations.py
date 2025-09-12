"""オプション組み合わせテスト"""
import pytest
from tests.fixtures.test_config import (
    run_main_command, 
    get_all_mock_files,
    mock_environment,
    assert_mock_data_used,
    assert_system_initialization,
    assert_analysis_started,
    assert_delivery_started
)


@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
@pytest.mark.parametrize("analysis", ["domi", "aga"])
def test_analysis_types(mock_file, analysis):
    """各分析タイプの完全動作確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command([
            "--analysis", analysis,
            "--delivery", "console",
            "--days", "45"
        ], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed with {analysis}: {result.stderr}"
        assert_mock_data_used(result)
        assert_system_initialization(result)
        assert_analysis_started(result, analysis)
        
        print(f"\n✅ Analysis {analysis} test passed for {mock_file}")


@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
@pytest.mark.parametrize("delivery", ["console", "file_text", "file_html"])
def test_delivery_methods(mock_file, delivery):
    """各配信方法の完全動作確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command([
            "--delivery", delivery,
            "--analysis", "domi",
            "--days", "45"
        ], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed with {delivery}: {result.stderr}"
        assert_mock_data_used(result)
        assert_system_initialization(result)
        assert_delivery_started(result, delivery)
        
        # 配信方法が使用されているか確認
        assert f"methods=['{delivery}']" in result.stdout, f"Delivery method {delivery} not used"
        
        print(f"\n✅ Delivery {delivery} test passed for {mock_file}")


@pytest.mark.smoke
@pytest.mark.parametrize("mock_file", get_all_mock_files())
@pytest.mark.parametrize("analysis,delivery", [
    ("domi", "console"),
    ("aga", "file_text"), 
    ("domi", "file_html"),
])
def test_option_combinations(mock_file, analysis, delivery):
    """主要なオプション組み合わせの完全動作確認（全モックデータで実行）"""
    with mock_environment(mock_file):
        result = run_main_command([
            "--analysis", analysis,
            "--delivery", delivery,
            "--days", "45"
        ], timeout=30, use_mocks=True)
        
        assert result.returncode == 0, f"Command failed with {analysis}/{delivery}: {result.stderr}"
        assert_mock_data_used(result)
        assert_system_initialization(result)
        assert_analysis_started(result, analysis)
        assert_delivery_started(result, delivery)
        
        print(f"\n✅ Combination {analysis}/{delivery} test passed for {mock_file}")
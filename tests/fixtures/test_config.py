"""テスト用設定とヘルパー関数"""
import subprocess
import os
import glob
from typing import List
from contextlib import contextmanager
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()


def run_main_command(args: List[str], timeout: int = 30, use_mocks: bool = True) -> subprocess.CompletedProcess:
    """
    main.pyを指定された引数で実行する
    
    Args:
        args: コマンドライン引数のリスト
        timeout: タイムアウト秒数（デフォルト30秒）
        use_mocks: モックを使用するかどうか（デフォルトTrue）
        
    Returns:
        subprocess.CompletedProcess: 実行結果
    """
    # Use virtual environment Python directly if uv is not available
    venv_python = "/Users/yuki.agatsuma@sa-nu.com/Desktop/pickles/.venv/bin/python"
    if os.path.exists(venv_python):
        cmd = [venv_python, "main.py"] + args
    else:
        cmd = ["python3", "main.py"] + args
    
    # 現在の環境変数を使用（.envファイルから読み込み済み）
    env = os.environ.copy()
    
    # モックモードを有効化
    if use_mocks:
        env['PICKLES_TEST_MODE'] = '1'
    
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd="/Users/yuki.agatsuma@sa-nu.com/Desktop/pickles"
    )


def assert_command_success(result: subprocess.CompletedProcess, expected_in_output: str = None):
    """
    コマンドが成功したことをアサートする
    
    Args:
        result: subprocess.CompletedProcess
        expected_in_output: 出力に含まれるべき文字列
    """
    assert result.returncode == 0, f"Command failed with exit code {result.returncode}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    
    if expected_in_output:
        assert expected_in_output in result.stdout, f"Expected '{expected_in_output}' in output, but got: {result.stdout}"




def get_all_mock_files():
    """モックデータファイル名のリストを取得（pytest parametrize用）"""
    notion_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                             "fixtures", "mock_data", "notion")
    json_files = sorted(glob.glob(os.path.join(notion_dir, "*.json")))
    return [os.path.splitext(os.path.basename(f))[0] for f in json_files]




@contextmanager
def mock_environment(mock_file: str = None):
    """テストモード用コンテキストマネージャー（特定のモックファイルを使用）"""
    # モックファイル指定がない場合は早期リターン
    if not mock_file:
        yield
        return
    
    # 現在の環境変数を保存
    original_mock_file = os.environ.get('PICKLES_TEST_SPECIFIC_MOCK_FILE')
    os.environ['PICKLES_TEST_SPECIFIC_MOCK_FILE'] = f"{mock_file}.json"
    
    try:
        yield
    finally:
        # 環境変数を復元
        if original_mock_file:
            os.environ['PICKLES_TEST_SPECIFIC_MOCK_FILE'] = original_mock_file
        else:
            os.environ.pop('PICKLES_TEST_SPECIFIC_MOCK_FILE', None)


def assert_mock_data_used(result: subprocess.CompletedProcess, mock_file: str = None):
    """Assert that mock data was used"""
    assert "[MOCK] Using available mock data:" in result.stdout, \
        "Expected mock data to be used but not found"
    
    # 特定のモックファイル確認が不要な場合は早期リターン
    if not mock_file:
        return
    
    expected_msg = f"[MOCK] Using available mock data: {mock_file}.json"
    assert expected_msg in result.stdout, \
        f"Expected to use {mock_file}.json but got different mock file"


def assert_system_initialization(result: subprocess.CompletedProcess):
    """Assert basic system initialization occurred"""
    assert "Picklesシステム開始" in result.stdout, "System initialization log not found"
    assert any(word in result.stdout for word in ["Notion APIキー設定確認", "Notion APIキーが設定されていません"]), \
        "Notion API key status not found"


def assert_analysis_started(result: subprocess.CompletedProcess, analysis_type: str):
    """Assert that specific analysis type was started"""
    assert f"analysis={analysis_type}" in result.stdout, f"Analysis type '{analysis_type}' not found in output"
    # Check for both regular and context analysis mode
    analysis_started = f"{analysis_type}分析処理開始" in result.stdout or f"{analysis_type}分析処理（" in result.stdout
    assert analysis_started, f"Analysis processing not started for {analysis_type}"


def assert_delivery_started(result: subprocess.CompletedProcess, delivery_method: str):
    """Assert that delivery method was used"""
    assert f"delivery={delivery_method}" in result.stdout, f"Delivery method '{delivery_method}' not found in output"
    assert "レポート配信処理開始" in result.stdout, "Report delivery not started"


def assert_command_failure_with_message(result: subprocess.CompletedProcess, expected_error_keywords: List[str] = None):
    """Enhanced failure assertion with flexible error message checking"""
    assert result.returncode != 0, f"Command should have failed but succeeded\nSTDOUT: {result.stdout}"
    
    # エラーキーワードの確認が不要な場合は早期リターン
    if not expected_error_keywords:
        return
    
    error_output = (result.stdout + result.stderr).lower()
    assert any(keyword.lower() in error_output for keyword in expected_error_keywords), \
        f"Expected one of {expected_error_keywords} in error output, but got: {error_output}"



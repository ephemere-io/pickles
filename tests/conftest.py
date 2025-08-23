"""pytest設定"""

def pytest_configure(config):
    """pytest設定時のフック"""
    config.addinivalue_line(
        "markers", "smoke: 基本的な動作確認のためのスモークテスト"
    )
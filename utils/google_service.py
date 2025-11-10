import os
from typing import Optional
from google.auth import default
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils import logger


class GoogleAPIError(Exception):
    """Google API操作時のエラー"""
    pass


class GoogleAPIService:
    """統一されたGoogle APIサービスクラス"""
    
    # 必要なスコープをすべて定義
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',  # Google Sheets読み取り
        'https://www.googleapis.com/auth/documents.readonly'      # Google Docs読み取り
    ]
    
    def __init__(self, service_account_key: str = None):
        """
        Args:
            service_account_key: サービスアカウントキーのJSON文字列
                               環境変数GOOGLE_SERVICE_ACCOUNT_KEYから自動的に読み込まれます
        """
        # JSON文字列形式で認証情報を取得
        self._service_account_json = service_account_key or os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
        
        # デバッグ: 認証情報の状態を確認
        if self._service_account_json:
            logger.info("Google API認証設定確認", "google", key_type="service_account_json", 
                       json_length=len(self._service_account_json))
        else:
            logger.warning("Google API認証が設定されていません（GOOGLE_SERVICE_ACCOUNT_KEYを設定してください）", "google")
        
        # テストモードの場合はモックを使用
        if os.getenv('PICKLES_TEST_MODE') == '1':
            from tests.fixtures.mock_handlers import mock_google_api
            mock_service = mock_google_api()
            self._sheets_service = mock_service()
            self._docs_service = mock_service()
        else:
            self._credentials = self._build_credentials()
            self._sheets_service = None
            self._docs_service = None
        
        self._check_api_connection()
    
    def _build_credentials(self):
        """Google API認証を構築（JSON文字列形式）"""
        import json
        try:
            if self._service_account_json:
                # Service Account JSON文字列から認証
                service_account_info = json.loads(self._service_account_json)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=self.SCOPES
                )
                logger.info("Service Account認証成功", "google",
                           scopes_count=len(self.SCOPES),
                           project_id=service_account_info.get('project_id'))
            else:
                # デフォルト認証を試行
                credentials, _ = default(scopes=self.SCOPES)
                logger.info("デフォルト認証成功", "google", scopes_count=len(self.SCOPES))
            
            return credentials
        except json.JSONDecodeError as e:
            logger.error("Service Account JSON解析失敗", "google", error=str(e))
            raise GoogleAPIError(f"Service Account JSON形式エラー - GOOGLE_SERVICE_ACCOUNT_KEYを確認してください: {e}")
        except Exception as e:
            logger.error("Google API認証構築失敗", "google", error=str(e))
            raise GoogleAPIError(f"Google API認証エラー: {e}")
    
    def _check_api_connection(self):
        """Google API接続を確認"""
        try:
            # 軽量なAPI呼び出しで接続をテスト
            # テストモードでない場合のみ実行
            if not os.getenv('PICKLES_TEST_MODE') == '1':
                # 実際のAPI接続テストは各サービス取得時に行う
                logger.info("Google API接続設定完了", "google", status="ready")
            else:
                logger.info("Google APIモックモード", "google", status="mock")
        except Exception as e:
            logger.warning("Google API接続確認失敗", "google", error=str(e))
    
    def get_sheets_service(self):
        """Google Sheets APIサービスを取得"""
        if self._sheets_service is None:
            try:
                self._sheets_service = build('sheets', 'v4', credentials=self._credentials)
            except Exception as e:
                logger.error("Google Sheets APIサービス構築失敗", "google", error=str(e))
                raise GoogleAPIError(f"Google Sheets API構築エラー: {e}")
        
        return self._sheets_service
    
    def get_docs_service(self):
        """Google Docs APIサービスを取得"""
        if self._docs_service is None:
            try:
                self._docs_service = build('docs', 'v1', credentials=self._credentials)
            except Exception as e:
                logger.error("Google Docs APIサービス構築失敗", "google", error=str(e))
                raise GoogleAPIError(f"Google Docs API構築エラー: {e}")
        
        return self._docs_service
    
    def test_sheets_access(self, spreadsheet_id: str) -> bool:
        """Google Sheetsへのアクセスをテスト"""
        try:
            service = self.get_sheets_service()
            # メタデータのみ取得してアクセステスト
            service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='properties.title'
            ).execute()
            logger.info("Google Sheetsアクセステスト成功", "google", spreadsheet_id=spreadsheet_id[:12]+"...")
            return True
        except HttpError as e:
            logger.warning("Google Sheetsアクセステスト失敗", "google", 
                         error=str(e), spreadsheet_id=spreadsheet_id[:12]+"...")
            return False
        except Exception as e:
            logger.error("Google Sheetsアクセステスト中にエラー", "google", error=str(e))
            return False
    
    def test_docs_access(self, document_id: str) -> bool:
        """Google Docsへのアクセスをテスト"""
        try:
            service = self.get_docs_service()
            # メタデータのみ取得してアクセステスト
            service.documents().get(
                documentId=document_id,
                fields='title'
            ).execute()
            logger.info("Google Docsアクセステスト成功", "google", document_id=document_id[:12]+"...")
            return True
        except HttpError as e:
            logger.warning("Google Docsアクセステスト失敗", "google", 
                         error=str(e), document_id=document_id[:12]+"...")
            return False
        except Exception as e:
            logger.error("Google Docsアクセステスト中にエラー", "google", error=str(e))
            return False


# シングルトンインスタンス（オプション）
_google_service_instance: Optional[GoogleAPIService] = None


def get_google_service(service_account_key: str = None) -> GoogleAPIService:
    """統一されたGoogle APIサービスインスタンスを取得"""
    global _google_service_instance
    
    if _google_service_instance is None:
        _google_service_instance = GoogleAPIService(service_account_key)
    
    return _google_service_instance


def reset_google_service():
    """Google APIサービスインスタンスをリセット（主にテスト用）"""
    global _google_service_instance
    _google_service_instance = None
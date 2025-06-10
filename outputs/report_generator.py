import os
import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv

# 定数をインポート
from utils import DeliveryMethods

load_dotenv()


class OutputError(Exception):
    """出力処理時のエラー"""
    pass


class ReportDelivery:
    """レポート配信統合クラス"""
    
    def __init__(self):
        # メール設定
        self.smtp_host = os.getenv("EMAIL_HOST")
        self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
        self.username = os.getenv("EMAIL_USER")
        self.password = os.getenv("EMAIL_PASS")
        self.to_email = os.getenv("EMAIL_TO")
    
    def deliver_report(self, 
                      analysis_result: Dict[str, str],
                      delivery_methods: List[str] = [DeliveryMethods.CONSOLE],
                      report_format: str = "comprehensive") -> Dict[str, str]:
        """レポートを指定された方法で配信"""
        
        results = {}
        
        # レポート生成
        if report_format == "comprehensive":
            text_report = self._format_comprehensive_report(analysis_result)
            html_report = self._format_html_report(analysis_result)
        else:
            text_report = analysis_result.get("insights", "分析結果なし")
            html_report = text_report
        
        # 配信実行
        for method in delivery_methods:
            try:
                if method == DeliveryMethods.CONSOLE:
                    print(text_report)
                    results[DeliveryMethods.CONSOLE] = "成功"
                
                elif method == DeliveryMethods.EMAIL_TEXT:
                    success = self._send_text_email("Pickles Weekly Report", text_report)
                    results[DeliveryMethods.EMAIL_TEXT] = "成功" if success else "失敗"
                
                elif method == DeliveryMethods.EMAIL_HTML:
                    success = self._send_html_email("Pickles Weekly Report", html_report)
                    results[DeliveryMethods.EMAIL_HTML] = "成功" if success else "失敗"
                
                elif method == DeliveryMethods.FILE_TEXT:
                    filename = self._save_text_file(text_report)
                    results[DeliveryMethods.FILE_TEXT] = f"保存完了: {filename}"
                
                elif method == DeliveryMethods.FILE_HTML:
                    filename = self._save_html_file(html_report)
                    results[DeliveryMethods.FILE_HTML] = f"保存完了: {filename}"
                
                else:
                    results[method] = f"未対応の配信方法: {method}"
                    
            except Exception as e:
                results[method] = f"エラー: {e}"
        
        return results
    
    def _format_comprehensive_report(self, analysis_result: Dict[str, str]) -> str:
        """包括的なレポートをフォーマット"""
        current_date = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        report_parts = [
            "=" * 50,
            f"📊 Pickles Weekly Report - {current_date}",
            "=" * 50,
            "",
            "📈 データ統計",
            "-" * 20,
            analysis_result.get("statistics", "統計情報なし"),
            "",
            "🧠 AI分析インサイト",
            "-" * 20,
            analysis_result.get("insights", "分析結果なし"),
            "",
            "=" * 50,
            f"分析対象データ数: {analysis_result.get('data_count', 0)}件",
            f"生成日時: {current_date}",
            "=" * 50
        ]
        
        return "\n".join(report_parts)
    
    def _format_html_report(self, analysis_result: Dict[str, str]) -> str:
        """HTML形式のレポートをフォーマット"""
        current_date = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        return f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Pickles Weekly Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                .section {{ margin: 20px 0; }}
                .stats {{ background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; }}
                .insights {{ padding: 15px; }}
                .footer {{ text-align: center; color: #666; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Pickles Weekly Report</h1>
                <p>{current_date}</p>
            </div>
            
            <div class="section">
                <h2>📈 データ統計</h2>
                <div class="stats">
                    <pre>{analysis_result.get("statistics", "統計情報なし")}</pre>
                </div>
            </div>
            
            <div class="section">
                <h2>🧠 AI分析インサイト</h2>
                <div class="insights">
                    <pre>{analysis_result.get("insights", "分析結果なし")}</pre>
                </div>
            </div>
            
            <div class="footer">
                <p>分析対象データ数: {analysis_result.get('data_count', 0)}件</p>
                <p>生成日時: {current_date}</p>
            </div>
        </body>
        </html>
        """
    
    def _send_text_email(self, subject: str, body: str) -> bool:
        """テキストメールを送信"""
        if not self._check_email_config():
            raise OutputError("メール設定が不完全です。環境変数を確認してください。")
        
        try:
            msg = MIMEText(body, _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = self.to_email
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            raise OutputError(f"テキストメール送信エラー: {e}")
    
    def _send_html_email(self, subject: str, html_body: str) -> bool:
        """HTMLメールを送信"""
        if not self._check_email_config():
            raise OutputError("メール設定が不完全です。環境変数を確認してください。")
        
        try:
            msg = MIMEText(html_body, "html", _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = self.to_email
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            raise OutputError(f"HTMLメール送信エラー: {e}")
    
    def _save_text_file(self, content: str, filename: Optional[str] = None) -> str:
        """テキストファイルに保存"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pickles_report_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
            
        except Exception as e:
            raise OutputError(f"ファイル保存エラー: {e}")
    
    def _save_html_file(self, content: str, filename: Optional[str] = None) -> str:
        """HTMLファイルに保存"""
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"pickles_report_{timestamp}.html"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
            
        except Exception as e:
            raise OutputError(f"HTMLファイル保存エラー: {e}")
    
    def _check_email_config(self) -> bool:
        """メール設定が完全かチェック"""
        return all([self.smtp_host, self.username, self.password, self.to_email]) 
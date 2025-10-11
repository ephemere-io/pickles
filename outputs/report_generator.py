import os
import datetime
import html
import calendar
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import smtplib
from dotenv import load_dotenv

# 定数をインポート
from utils import DeliveryMethods, logger

load_dotenv()


class OutputError(Exception):
    """出力処理時のエラー"""
    pass


class ReportDelivery:
    """レポート配信統合クラス"""
    
    def __init__(self, email_config: Dict[str, str] = None):
        # メール設定（環境変数またはuser_configから取得）
        if email_config and email_config.get('email_to'):
            self.smtp_host = os.getenv("EMAIL_HOST")
            self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
            self.username = os.getenv("EMAIL_USER")
            self.password = os.getenv("EMAIL_PASS")
            self.to_email = email_config.get('email_to')
            self.from_email = os.getenv("EMAIL_FROM", self.username)  # デフォルトはusernameを使用
            self.user_name = email_config.get('user_name')
        else:
            # デフォルトの環境変数設定
            self.smtp_host = os.getenv("EMAIL_HOST")
            self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
            self.username = os.getenv("EMAIL_USER")
            self.password = os.getenv("EMAIL_PASS")
            self.to_email = os.getenv("EMAIL_TO")
            self.from_email = os.getenv("EMAIL_FROM", self.username)  # デフォルトはusernameを使用
            self.user_name = None
    
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
    
    def _get_week_of_month(self, date: datetime.datetime = None) -> int:
        """その月の第何週目かを取得（1-5）"""
        if date is None:
            date = datetime.datetime.now()
        
        # その月の1日を取得
        first_day = date.replace(day=1)
        # 第1週目の開始日を計算（月曜日基準）
        first_monday = first_day - datetime.timedelta(days=first_day.weekday())
        
        # 現在の日付が第何週目かを計算
        days_diff = (date - first_monday).days
        week_number = (days_diff // 7) + 1
        
        # 1-5の範囲に制限
        return min(max(week_number, 1), 5)
    
    def _get_image_paths(self, week: int) -> Dict[str, str]:
        """週に応じた画像パスを取得"""
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        
        # カバー画像（週に応じて変化）
        cover_image = f"cover-image-{week}.png"
        
        # アイコン（固定アサイン）
        icon_numbers = [1, 2, 3, 4]  # icon.png, icon-2.png, icon-3.png, icon-4.png
        main_icon = f"icon{'-' + str(icon_numbers[(week - 1) % len(icon_numbers)]) if (week - 1) % len(icon_numbers) > 0 else ''}.png"
        stats_icon = "icon-2.png"  # 記録の統計は常にicon-2.png
        insights_icon = "icon.png"  # 発酵した洞察は常にicon.png
        
        return {
            "cover": os.path.join(base_path, cover_image),
            "main": os.path.join(base_path, main_icon),
            "stats": os.path.join(base_path, stats_icon),
            "insights": os.path.join(base_path, insights_icon)
        }
    
    def _format_html_report(self, analysis_result: Dict[str, str]) -> str:
        """HTML形式のレポートをフォーマット（週刊お手紙デザイン）"""
        current_date = datetime.datetime.now()
        date_str = current_date.strftime("%Y年%m月%d日")
        week_num = self._get_week_of_month(current_date)
        
        # HTMLエスケープ処理
        statistics = html.escape(analysis_result.get("statistics", "統計情報なし"))
        insights = html.escape(analysis_result.get("insights", "分析結果なし"))
        
        return f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Pickles: to Ferment our Lives - Weekly Letter</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
</head>
<body style="margin: 0; padding: 0; background-color: #F8F7FA; font-family: 'Helvetica Neue', Arial, sans-serif; color: #1A1A1A;">
    <!-- Main container table -->
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #F8F7FA;">
        <tr>
            <td align="center" valign="top">
                <!-- Responsive container -->
                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 800px; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(45, 27, 55, 0.1); overflow: hidden;">
                    
                    <!-- Top cover image -->
                    <tr>
                        <td align="center" valign="top" style="padding: 0;">
                            <img src="cid:cover_image" alt="Pickles Cover" width="100%" height="100" style="border: none; display: block; width: 100%; height: 100px; object-fit: cover;" />
                        </td>
                    </tr>
                    
                    <!-- Header with title only -->
                    <tr>
                        <td align="center" valign="top" style="background: linear-gradient(135deg, #1A0F20 0%, #2D1B37 100%); padding: 20px 20px;">
                            <h1 style="color: #FFFFFF; font-size: 24px; font-weight: 300; margin: 0 0 15px 0; letter-spacing: 0.5px; line-height: 1.2;">
                                Pickles: to Ferment our Lives
                            </h1>
                            <p style="color: rgba(255, 255, 255, 0.9); font-size: 16px; margin: 0; font-weight: 300;">
                                Weekly Letter · {date_str} · Week {week_num}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Letter content wrapper -->
                    <tr>
                        <td align="left" valign="top" style="padding: 20px 15px 10px 15px;">
                            <p style="color: #2D1B37; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0; font-style: italic;">
                                あなたの日々の記録から発酵した洞察をお届けします。
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Statistics Section -->
                    <tr>
                        <td align="left" valign="top" style="padding: 0 15px 25px 15px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="left" valign="middle" style="padding-bottom: 12px;">
                                        <img src="cid:stats_icon" alt="Stats" width="26" height="26" style="border: none; vertical-align: middle; margin-right: 5px; opacity: 0.8;" />
                                        <span style="color: #1A1A1A; font-size: 18px; font-weight: 500; vertical-align: middle;">記録の統計</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="left" valign="top" style="background: linear-gradient(135deg, #F8F7FA 0%, #F3F1F6 100%); border: 1px solid #E8E5ED; padding: 18px; border-radius: 8px;">
                                        <pre style="font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace; font-size: 14px; color: #1A1A1A; margin: 0; white-space: pre-wrap; line-height: 1.6;">{statistics}</pre>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Insights Section -->
                    <tr>
                        <td align="left" valign="top" style="padding: 0 15px 30px 15px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="left" valign="middle" style="padding-bottom: 12px;">
                                        <img src="cid:insights_icon" alt="Insights" width="26" height="26" style="border: none; vertical-align: middle; margin-right: 5px; opacity: 0.8;" />
                                        <span style="color: #1A1A1A; font-size: 18px; font-weight: 500; vertical-align: middle;">発酵した洞察</span>
                                    </td>
                                </tr>
                                <tr>
                                    <td align="left" valign="top" style="background-color: #FFFFFF; border: 1px solid #E8E5ED; padding: 18px; border-radius: 8px; box-shadow: 0 2px 8px rgba(45, 27, 55, 0.05);">
                                        <pre style="font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace; font-size: 14px; color: #1A1A1A; margin: 0; white-space: pre-wrap; line-height: 1.7;">{insights}</pre>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Letter closing -->
                    <tr>
                        <td align="center" valign="top" style="padding: 0 15px 30px 15px;">
                            <p style="color: #2D1B37; font-size: 16px; line-height: 1.6; margin: 0; font-style: italic; text-align: center;">
                                また来週、新たな発見をお楽しみに。
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer with info -->
                    <tr>
                        <td align="center" valign="top" style="background: linear-gradient(135deg, #1A0F20 0%, #2D1B37 100%); padding: 25px 20px;">
                            <table border="0" cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <td align="center" valign="top">
                                        <p style="color: #FFFFFF; font-size: 14px; margin: 0 0 8px 0;">
                                            分析対象: <strong>{analysis_result.get('data_count', 0)}件</strong> の記録
                                        </p>
                                        <p style="color: #FFFFFF; font-size: 14px; margin: 0 0 15px 0;">
                                            発酵完了: {date_str}
                                        </p>
                                        <p style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin: 0; letter-spacing: 0.5px;">
                                            POWERED BY PICKLES AI FERMENTATION SYSTEM
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Bottom cover image -->
                    <tr>
                        <td align="center" valign="top" style="padding: 0;">
                            <img src="cid:cover_image_bottom" alt="Pickles Cover Bottom" width="100%" height="100" style="border: none; display: block; width: 100%; height: 100px; object-fit: cover; border-radius: 0 0 12px 12px;" />
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
    
    def _send_text_email(self, subject: str, body: str) -> bool:
        """テキストメールを送信"""
        # テストモードの場合はモックを使用
        if os.getenv('PICKLES_TEST_MODE') == '1':
            logger.info("テストモード: メール送信をスキップ", "email", 
                       subject=subject, to=self.to_email)
            return True
        
        if not self._check_email_config():
            raise OutputError("メール設定が不完全です。環境変数を確認してください。")
        
        try:
            msg = MIMEText(body, _charset="utf-8")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            raise OutputError(f"テキストメール送信エラー: {e}")
    
    def _send_html_email(self, subject: str, html_body: str) -> bool:
        """HTMLメールを送信（CID画像埋め込み対応）"""
        # テストモードの場合はモックを使用
        if os.getenv('PICKLES_TEST_MODE') == '1':
            logger.info("テストモード: HTMLメール送信をスキップ", "email", 
                       subject=subject, to=self.to_email)
            return True
        
        if not self._check_email_config():
            raise OutputError("メール設定が不完全です。環境変数を確認してください。")
        
        try:
            logger.start("HTMLメール送信処理", "email", 
                        to_email=self.to_email, 
                        subject=subject,
                        from_user=self.username, 
                        smtp_server=f"{self.smtp_host}:{self.smtp_port}")
            
            # マルチパートメッセージを作成
            msg = MIMEMultipart('related')
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = self.to_email
            
            # HTMLコンテンツを作成
            html_part = MIMEText(html_body, "html", _charset="utf-8")
            msg.attach(html_part)
            
            # 画像を埋め込み
            self._attach_images(msg)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                logger.debug("SMTPサーバーに接続", "email")
                server.starttls()
                logger.debug("TLS暗号化開始", "email")
                server.login(self.username, self.password)
                logger.debug("ログイン成功", "email")
                server.send_message(msg)
                logger.complete("HTMLメール送信", "email", to_email=self.to_email)
            
            return True
            
        except Exception as e:
            logger.error("HTMLメール送信エラー", "email", error=str(e))
            raise OutputError(f"HTMLメール送信エラー: {e}")

    def _attach_images(self, msg: MIMEMultipart) -> None:
        """画像をCIDとしてメールに添付（週刊デザイン対応）"""
        try:
            week_num = self._get_week_of_month()
            image_paths = self._get_image_paths(week_num)
            
            # CIDと画像パスのマッピング
            image_mappings = [
                ("cover_image", image_paths["cover"]),
                ("cover_image_bottom", image_paths["cover"]),  # 上下同じカバー画像
                ("main_icon", image_paths["main"]),
                ("stats_icon", image_paths["stats"]),
                ("insights_icon", image_paths["insights"])
            ]
            
            attached_count = 0
            for cid, image_path in image_mappings:
                if os.path.exists(image_path):
                    with open(image_path, 'rb') as img_file:
                        img_data = img_file.read()
                    
                    # MIMEImageオブジェクトを作成
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', f'<{cid}>')
                    img.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                    msg.attach(img)
                    
                    attached_count += 1
                    logger.debug("画像を添付", "email", 
                                image_path=image_path, 
                                cid=cid,
                                week=week_num)
                else:
                    logger.warning("画像ファイルが見つかりません", "email", 
                                  image_path=image_path, cid=cid)
            
            logger.info("画像添付完了", "email", 
                       attached_count=attached_count, 
                       total_images=len(image_mappings),
                       week=week_num)
                
        except Exception as e:
            logger.error("画像添付エラー", "email", error=str(e))
    
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
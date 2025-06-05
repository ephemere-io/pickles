import os
import datetime
from notion_client import Client
from openai import OpenAI
from apscheduler.schedulers.blocking import BlockingScheduler
from email.mime.text import MIMEText
import smtplib
from dotenv import load_dotenv

# 環境変数のロード
load_dotenv()

def fetch_entries():
    """
    Notionデータベースから過去1週間分の日誌エントリを取得する
    DateプロパティとEntryプロパティを持つデータベースを想定
    """
    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_PAGE_ID")
    one_week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()

    # クエリで日付フィルタリング
    response = notion.databases.query(
        **{
            "database_id": database_id,
            "filter": {
                "property": "Date",
                "date": {"on_or_after": one_week_ago}
            },
            "sorts": [{"property": "Date", "direction": "ascending"}]
        }
    )

    entries = []
    results = response.get("results", [])
    
    # Debug: Print available properties for the first page
    if results:
        print("Available properties in the first page:")
        for prop_name in results[0].get("properties", {}).keys():
            print(f"- {prop_name}")
    
    for page in results:
        properties = page.get("properties", {})
        
        # Check if Date property exists and has the expected structure
        if "Date" not in properties or not properties["Date"].get("date"):
            print(f"Warning: Page {page.get('id')} missing Date property or unexpected format")
            continue
            
        date = properties["Date"]["date"]["start"]
        
        # Look for text content in either "Entry" or another rich_text property
        content = ""
        text_property_found = False
        
        # Try "Entry" first (the original expected property)
        if "Entry" in properties and "rich_text" in properties["Entry"]:
            texts = properties["Entry"]["rich_text"]
            content = ''.join([rt.get("plain_text", "") for rt in texts])
            text_property_found = True
        else:
            # If "Entry" not found, look for any property with rich_text type
            for prop_name, prop_value in properties.items():
                if prop_name != "Date" and "rich_text" in prop_value:
                    print(f"Found alternative text property: {prop_name}")
                    texts = prop_value["rich_text"]
                    content = ''.join([rt.get("plain_text", "") for rt in texts])
                    text_property_found = True
                    break
        
        if text_property_found:
            entries.append({"date": date, "text": content})
        else:
            print(f"Warning: No suitable text property found for page {page.get('id')}")
    
    return entries


def analyze(entries):
    """
    OpenAI ChatGPT APIを使って感情・思考の分析レポートを生成する
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    # 日付と本文をまとめてプロンプト化
    diary_text = "\n".join([f"{e['date']}: {e['text']}" for e in entries])
    prompt = (
        "次の一週間の日誌の内容を、感情と思考の観点から分析し、"
        "要約と感情の傾向を含むレポートを作成してください。\n" + diary_text
    )

    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return resp.choices[0].message.content


def send_report(report: str):
    """
    SMTPを使ってレポートをメール送信する
    """
    msg = MIMEText(report, _charset="utf-8")
    msg["Subject"] = "Pickles Weekly Report"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")

    with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        server.send_message(msg)


def job():
    entries = fetch_entries()
    if not entries:
        print("No entries in the past week.")
        return
    report = analyze(entries)
    print(report)
    # send_report(report)
    print("Weekly report sent.")


if __name__ == "__main__":
    # Asia/Tokyoタイムゾーンで毎週月曜7:00にジョブ実行
    # scheduler = BlockingScheduler(timezone="Asia/Tokyo")
    # scheduler.add_job(job, trigger="cron", day_of_week="mon", hour=7, minute=0)
    # print("Scheduler started: Every Monday at 07:00 JST")
    # scheduler.start()
    entries = fetch_entries()
    if not entries:
        print("No entries in the past week.")
    else:
        report = analyze(entries)
        print(report)
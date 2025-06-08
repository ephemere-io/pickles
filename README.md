# Pickles 🥒

> Pickling everyday thoughts and feelings

NotionデータベースとOpenAI APIを使用して、日記エントリから感情・思考の分析レポートを自動生成し、定期的にメール送信するPythonアプリケーションです。

## 🚀 クイックスタート

> [!NOTE]
> このプロジェクトは[uv](https://github.com/astral-sh/uv)を使用して依存関係を管理しています。

### 1. uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. プロジェクトのセットアップ

```bash
# プロジェクトクローン
git clone git@github.com:dominickchen/pickles.git
cd pickles

# 依存関係のインストール
uv sync
```

### 3. 環境変数の設定

`.env`ファイルを作成し、以下の値を設定してください：

```bash
# Notion API設定
NOTION_API_KEY=your_notion_api_key_here
NOTION_PAGE_ID=your_notion_database_id_here

# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# メール設定
EMAIL_USER=your_email@example.com
EMAIL_PASS=your_email_password_here
EMAIL_TO=recipient@example.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

### 4. 実行

```bash
# 手動実行
uv run python main.py

# スケジューラー実行（毎週月曜7:00）
# main.pyのスケジューラー部分のコメントアウトを解除してから実行
```

## 📋 必要なAPI設定

<details>
<summary>🔧 Notion API設定</summary>

1. [Notion Developers](https://developers.notion.com/)でintegrationを作成
2. APIキーを取得して`NOTION_API_KEY`に設定
3. 日記データベースをintegrationに共有
4. データベースIDを`NOTION_PAGE_ID`に設定

**必要なデータベース構造:**
- `Date`プロパティ（日付型）
- `Entry`プロパティ（リッチテキスト型）

</details>

<details>
<summary>🤖 OpenAI API設定</summary>

1. [OpenAI Platform](https://platform.openai.com/)でAPIキーを作成
2. `OPENAI_API_KEY`に設定
3. 現在はo4-miniモデルを使用（要課金）

</details>

<details>
<summary>📧 メール設定</summary>

Gmail使用時の設定例：
- `EMAIL_HOST`: smtp.gmail.com
- `EMAIL_PORT`: 587
- `EMAIL_PASS`: アプリパスワードを使用（通常のパスワードではない）

[Googleアプリパスワードの設定方法](https://support.google.com/accounts/answer/185833)

</details>

## 🛠️ 開発環境

### 依存関係の追加

```bash
# 新しいパッケージを追加
uv add package-name

# 開発用依存関係を追加
uv add --dev package-name
```

### Python バージョン

```bash
# 使用中のPythonバージョン確認
uv run python --version

# 利用可能なPythonバージョン一覧
uv python list
```

## 📊 プロジェクト構成

```
pickles/
├── main.py              # メインアプリケーション
├── .env                 # 環境変数（要作成）
├── pyproject.toml       # プロジェクト設定
├── uv.lock              # 依存関係ロックファイル
└── README.md            # このファイル
```

## 🔄 スケジューラー

デフォルトでは毎週月曜日の午前7時（JST）に実行されます。

```python
scheduler.add_job(job, trigger="cron", day_of_week="mon", hour=7, minute=0)
```

<details>
<summary>⚡ なぜ **uv** を使用するのか？</summary>

### **uv** が **pip** より速く・軽く・再現性が高い理由

| 項目           | uv のしくみ                                                                                       | pip のしくみ                              | 効果                                               |
| ------------ | --------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------ |
| 実装           | **Rust 製バイナリ**（ネイティブ速度）                                                      | 純 Python スクリプト                        | 依存解決・ダウンロード・展開が 10-100× 高速⚡ |
| 依存解決         | **PubGrub** アルゴリズムで一括計算（衝突原因も提示）                                                              | 従来の逐次バックトラック                          | 解決が determinisitic＋失敗理由が分かりやすい                   |
| キャッシュ        | １か所 `~/.cache/uv` に wheel と Python 本体を保存 → 各 `.venv` へ **ハードリンク/CoW** 展開 | wheel は共通だが毎 `.venv` にフルコピー           | ディスク重複ゼロ；.venv 削除しても他プロジェクト無事                    |
| Python バージョン | `uv install python 3.12` で同キャッシュに共存                                                           | 外部ツール（pyenv など）が必要                    | バージョン切替も１コマンド                                    |
| ロックファイル      | `uv.lock` を自動生成・使用                                                                            | 手動 `requirements.txt` or 外部 pip-tools | CI／本番で完全再現 (`uv sync`)                           |
| スクリプト実行      | PEP 723: ファイル冒頭に `# dependencies = [...]` → `uv run` で即席環境                                    | venv 作成＋pip install が必須               | 単発ツールをすぐ共有できる                                    |

#### **Pickles プロジェクト** への具体的メリット

1. **初回セットアップ３行**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   uv run python main.py
   ```

2. **週次ジョブの依存更新が秒単位** — Notion-client や OpenAI などを追加しても解決が即完了。

3. **環境事故ゼロ** — `uv run main.py` が venv を自動管理、システム Python を汚さない。

4. **チーム／CI での再現性** — `uv.lock` をコミット → サーバで `uv sync && uv run main.py` でそのまま稼働。

> **まとめ**  
> uv は *Rust × PubGrub × グローバルキャッシュ* という構造で「速い・ディスクを食わない・再現性が高い」を実現。  
> Pickles のような API 連携＋定期実行アプリでも導入は数分、得られるメンテコスト削減は長期。pip で困っていなくても一度 `uv init` で体感する価値があります。

</details>

## 🔒 セキュリティ

> [!WARNING]
> `.env`ファイルにはAPIキーなどの機密情報が含まれます。**絶対にGitにコミットしないでください**。

`.gitignore`で以下がブロックされていることを確認してください：
```
.env
```
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
# デフォルト実行（notion + domi分析 + console出力）
uv run python main.py

# カスタマイズ実行
uv run python main.py --source notion --analysis domi --delivery console
uv run python main.py --source notion --analysis aga --delivery file_html
uv run python main.py --source notion --analysis domi --delivery console,email_text
uv run python main.py --days 14 --delivery email_html,file_text

# 履歴機能の使用例
uv run python main.py --history on --delivery email_html    # 過去の分析を参考にした継続的分析（デフォルト）
uv run python main.py --history off --delivery console     # 履歴なしの独立分析

# 定期実行モード
uv run python main.py --schedule

# ヘルプ表示
uv run python main.py --help

# スケジューラー実行（毎週月曜7:00）
# main.pyのスケジューラー部分のコメントアウトを解除してから実行
```

#### 📝 コマンドライン引数

| 引数          | 説明               | 選択肢                        | デフォルト |
| ----------- | ---------------- | -------------------------- | ----- |
| `--source`  | データソース         | `notion` | notion |
| `--analysis` | 分析タイプ          | `domi`, `aga` | domi |
| `--delivery` | 配信方法           | `console`, `email_text`, `email_html`, `file_text`, `file_html` | console |
| `--days`    | 取得日数          | 整数値                        | 7 |
| `--history` | 分析履歴使用       | `on`, `off`                  | on |
| `--schedule` | 定期実行モード       | フラグ                        | false |

## 🧠 AI分析履歴機能

Picklesは**OpenAI o4-miniのResponses API履歴機能**を活用し、過去の分析結果を踏まえた継続的な洞察を提供します。

### 機能概要
- **継続的コンテキスト**: 過去3回分の分析履歴をAIに送信
- **パターン認識**: 時系列での変化や傾向の発見
- **個人最適化**: ユーザー固有のパターンに特化した分析

### 履歴データ管理
- **保存場所**: プロジェクトルートの`analysis_history.json`
- **最大履歴数**: 10件（自動削除）
- **分析タイプ別**: `domi`と`aga`で独立管理

### 使用例
```bash
# 履歴ありで継続的分析（推奨）
uv run python main.py --history on

# 従来通りの独立分析
uv run python main.py --history off

# 特定分析タイプで履歴活用
uv run python main.py --analysis domi --history on
```

## 📋 必要なAPI設定

<details>
<summary>🔧 Notion API設定</summary>

1. [Notion Developers](https://developers.notion.com/)でintegrationを作成
2. APIキーを取得して`NOTION_API_KEY`に設定
3. 分析したいワークスペースまたはデータベースをintegrationに共有

**データベースを使用する場合の推奨構造:**
- `Date`プロパティ（日付型） - 作成日以外の日付を使用したい場合

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
├── main.py                    # メインアプリケーション・エントリーポイント
├── inputs/
│   ├── __init__.py           # Notion入力モジュール
│   └── notion_input.py       # Notionデータ取得（統合クラス設計）
├── throughput/
│   ├── __init__.py           # 分析処理モジュール
│   ├── analyzer.py           # OpenAI感情・思考分析（統合クラス設計）
│   ├── analysis_history.py   # AI分析履歴管理
│   └── prompts/              # 分析プロンプト管理
│       ├── __init__.py
│       ├── domi_prompts.py
│       └── aga_prompts.py
├── outputs/
│   ├── __init__.py           # 出力・配信モジュール
│   └── report_generator.py   # レポート生成・メール送信（統合クラス設計）
├── utils/
│   ├── __init__.py           # ユーティリティ（定数管理含む）
│   ├── logger.py             # ログ出力（絵文字付き）
│   └── printer.py            # ヘルプ表示・定数定義
├── .env                      # 環境変数（要作成）
├── analysis_history.json     # AI分析履歴データ（自動生成）
├── pyproject.toml            # プロジェクト設定
├── uv.lock                   # 依存関係ロックファイル
└── README.md                 # このファイル
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
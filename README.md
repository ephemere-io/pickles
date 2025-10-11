# Pickles 🥒

> Pickling everyday thoughts and feelings

NotionデータベースまたはGoogle DocsとOpenAI APIを使用して、日記エントリから感情・思考の分析レポートを自動生成・配信するPythonアプリケーションです。単体実行とマルチユーザー対応のGitHub Actions実行に対応しています。

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
# Notion API設定（Notionを使用する場合）
NOTION_API_KEY=your_notion_api_key_here

# Google Docs API設定（Google Docsを使用する場合）
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# メール設定
EMAIL_USER=your_smtp_username_here        # SMTP認証用ユーザー名（IAMユーザーIDなど）
EMAIL_PASS=your_email_password_here       # SMTP認証用パスワード
EMAIL_FROM=pickles@ephemere.io           # メール送信者として表示されるアドレス
EMAIL_TO=recipient@example.com           # 送信先メールアドレス
EMAIL_HOST=smtp.gmail.com                # SMTPサーバーホスト
EMAIL_PORT=587                           # SMTPポート番号
```

## 📋 コマンドライン引数リファレンス

<table>
<tr>
<th>オプション</th>
<th>説明</th>
<th>値</th>
<th>デフォルト</th>
<th>備考</th>
</tr>
<tr>
<td><code>--source</code></td>
<td>データソース</td>
<td><code>notion</code> | <code>gdocs</code></td>
<td><code>notion</code></td>
<td>-</td>
</tr>
<tr>
<td><code>--analysis</code></td>
<td>分析タイプ</td>
<td><code>domi</code> | <code>aga</code></td>
<td><code>domi</code></td>
<td>-</td>
</tr>
<tr>
<td><code>--delivery</code></td>
<td>配信方法</td>
<td><code>console</code> | <code>email_html</code> | <code>email_text</code> | <code>file_html</code> | <code>file_text</code></td>
<td><code>console</code></td>
<td>複数指定可（カンマ区切り）</td>
</tr>
<tr>
<td><code>--days</code></td>
<td>分析日数</td>
<td>整数値（最小7）</td>
<td><code>7</code></td>
<td>7日超でコンテキスト分析</td>
</tr>
<tr>
<td><code>--language</code></td>
<td>出力言語</td>
<td><code>japanese</code> | <code>english</code></td>
<td><code>english</code></td>
<td>-</td>
</tr>
<tr>
<td><code>--gdocs-url</code></td>
<td>Google Docs URL</td>
<td>Google DocsのURL</td>
<td>-</td>
<td><code>--source gdocs</code>時のみ必要</td>
</tr>
<tr>
<td><code>--user-name</code></td>
<td>ユーザー名</td>
<td>文字列</td>
<td>-</td>
<td>未指定時は環境変数<code>USER_NAME</code></td>
</tr>
<tr>
<td><code>--email-to</code></td>
<td>送信先メール</td>
<td>メールアドレス</td>
<td>-</td>
<td>未指定時は環境変数<code>EMAIL_TO</code></td>
</tr>
<tr>
<td><code>--notion-api-key</code></td>
<td>Notion APIキー</td>
<td>APIキー文字列</td>
<td>-</td>
<td><code>--source notion</code>時、未指定は環境変数<code>NOTION_API_KEY</code></td>
</tr>
<tr>
<td><code>--help</code></td>
<td>ヘルプ表示</td>
<td>フラグ</td>
<td>-</td>
<td>詳細な使用例も表示</td>
</tr>
</table>

## 💡 実行例

```bash
# 基本実行（Notion + DOMI + コンソール出力）
uv run python main.py

# 英語でメール送信
uv run python main.py --delivery email_html --language english

# Google Docsから分析
uv run python main.py --source gdocs

# 30日コンテキストでAGA分析
uv run python main.py --analysis aga --days 30

# 複数配信方法
uv run python main.py --delivery console,email_html,file_text

# 指定実行（Notion）
uv run python main.py --user-name "田中太郎" --email-to "tanaka@example.com" --notion-api-key "secret_xxx"

# 指定実行（Google Docs）
uv run python main.py --source gdocs --gdocs-url "https://docs.google.com/document/d/DOC_ID" --user-name "田中太郎"


# 詳細ヘルプ表示
uv run python main.py --help
```

## ⚡ 機能紹介

<details>
<summary><strong>📝 データソース連携</strong> - NotionデータベースとGoogle Docsから日記データを取得</summary>

### Notion連携
- **データベース自動検索**: 日記エントリが含まれるデータベースを自動発見
- **フォールバック検索**: データベースが見つからない場合はページ検索
- **豊富なプロパティ対応**: rich_text, select, multi_select, url, email, phone_number, number, checkbox

### Google Docs連携
- **日付ヘッダー形式**: `# YYYY-MM-DD`で構造化された日記エントリを解析
- **マークダウン対応**: 構造化テキストから日記内容を抽出

</details>

<details>
<summary><strong>🧠 AI分析機能</strong> - OpenAI APIを使用した感情・思考分析</summary>

### DOMI分析
- **ゆらぎ**: 内面と他者との関係性の変化
- **ゆだね**: 自律性と他律性のバランス
- **ゆとり**: 目的達成主義からの脱却と余白の創出

### AGA分析
- **行動パターン**: 日常の習慣と変化の分析
- **感情の流れ**: 気持ちの変遷と要因の特定
- **成長ポイント**: 個人的成長の機会の発見

### コンテキスト分析
- **7日以上の期間指定**: 長期的な傾向と短期的な変化を同時分析
- **継続的洞察**: 過去データとの比較による深い理解

</details>

<details>
<summary><strong>📤 多様な配信方法</strong> - 分析結果を様々な形式で出力</summary>

- **console**: ターミナルに直接表示
- **email_html/email_text**: HTMLまたはテキスト形式でメール送信
- **file_html/file_text**: ファイルとして保存
- **複数同時配信**: カンマ区切りで複数方法を指定可能

</details>


<details>
<summary><strong>🤖 GitHub Actions マルチユーザー実行</strong> - 複数ユーザーの自動分析・配信</summary>

- **Google Sheets連携**: スプレッドシートからユーザー情報を一括読み込み
- **定期実行**: 毎週月曜7:00に自動実行
- **個別設定**: ユーザーごとに言語・APIキー・送信先を設定可能
- **手動実行**: 任意のタイミングで実行可能

</details>

<details>
<summary><strong>🌍 多言語対応</strong> - 日本語・英語での分析結果出力</summary>

- **japanese**: 日本語での分析結果
- **english**: 英語での分析結果
- **ユーザー別設定**: マルチユーザー実行時に個別言語設定

</details>

## 📋 環境構築

### 必要なAPI設定

<details>
<summary>🔧 Notion API設定</summary>

1. [Notion Developers](https://developers.notion.com/)でintegrationを作成
2. APIキーを取得して`NOTION_API_KEY`に設定
3. 分析したいワークスペースまたはデータベースをintegrationに共有

**データベースを使用する場合の推奨構造:**
- `Date`プロパティ（日付型） - 作成日以外の日付を使用したい場合

</details>

<details>
<summary>📄 Google Docs API設定</summary>

1. [Google Cloud Console](https://console.cloud.google.com/)で新しいプロジェクトを作成
2. Google Docs APIを有効化
3. Service Accountを作成し、JSONキーをダウンロード
4. Service AccountのメールアドレスをGoogle Docsの**閲覧者として共有**
5. JSONキーのパスを`GOOGLE_APPLICATION_CREDENTIALS`に設定

**Google Docs構造要件:**
```
# 2025-01-15
朝から雨だったが、室内で集中して作業できた。
新しいプロジェクトのアイデアが浮かんだ。

# 2025-01-14
友人とのランチで刺激的な話を聞けた。
```
- 日付ヘッダーは`# YYYY-MM-DD`形式で記述
- 各ヘッダー以下が該当日の日誌エントリになる

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
- `EMAIL_USER`: Gmailアドレスまたは認証用ユーザー名
- `EMAIL_PASS`: アプリパスワードを使用（通常のパスワードではない）
- `EMAIL_FROM`: 送信者として表示したいメールアドレス（通常は`EMAIL_USER`と同じ）

AWS SES使用時の設定例：
- `EMAIL_HOST`: email-smtp.us-east-1.amazonaws.com
- `EMAIL_PORT`: 587
- `EMAIL_USER`: SMTP認証用IAMユーザーのAccess Key ID
- `EMAIL_PASS`: SMTP認証用IAMユーザーのSecret Access Key
- `EMAIL_FROM`: 検証済みドメインのメールアドレス（例: pickles@ephemere.io）

**重要**: `EMAIL_USER`（認証）と`EMAIL_FROM`（表示）は別の概念です。
- `EMAIL_USER`: SMTP認証に使用（IAMユーザーIDやGmailアドレス）
- `EMAIL_FROM`: メール受信者に表示される送信者アドレス

[Googleアプリパスワードの設定方法](https://support.google.com/accounts/answer/185833)

</details>

## 📊 プロジェクト構成

```
pickles/
├── main.py                    # メインアプリケーション・エントリーポイント
├── read_spreadsheet_and_execute.py  # マルチユーザー実行スクリプト
├── inputs/
│   ├── __init__.py           # データ入力モジュール
│   ├── notion_input.py       # Notionデータ取得（統合クラス設計）
│   └── gdocs_input.py        # Google Docsデータ取得
├── throughput/
│   ├── __init__.py           # 分析処理モジュール
│   ├── analyzer.py           # OpenAI感情・思考分析（統合クラス設計）
│   └── prompts/              # 分析プロンプト管理
│       ├── __init__.py
│       ├── domi_prompts.py
│       └── aga_prompts.py
├── outputs/
│   ├── __init__.py           # 出力・配信モジュール
│   └── report_generator.py   # レポート生成・メール送信（統合クラス設計）
├── utils/
│   ├── __init__.py           # ユーティリティ（定数管理含む）
│   ├── logger.py             # ログ出力（テキストレベル表示）
│   └── printer.py            # ヘルプ表示・定数定義
├── tests/                    # テストスイート
│   ├── README.md             # テストドキュメント
│   ├── __init__.py
│   ├── fixtures/             # テスト用ヘルパー
│   │   ├── __init__.py
│   │   ├── test_config.py    # テスト共通設定
│   │   ├── mock_handlers.py  # モックデータ管理
│   │   └── mock_data/        # モックデータディレクトリ
│   │       └── notion/       # Notion APIモックデータ
│   │           ├── mock_data_1.json  # サンプルモックデータ
│   └── smoke/                # スモークテスト
│       ├── __init__.py
│       ├── test_basic_commands.py    # 基本機能テスト（全モックデータ）
│       ├── test_option_combinations.py # オプション組み合わせテスト（全モックデータ）
│       └── test_error_handling.py   # エラーハンドリングテスト（全モックデータ）
├── .github/workflows/
│   ├── weekly-report.yml     # GitHub Actions マルチユーザー実行
│   └── setup-secrets.md      # GitHub Actions設定ガイド
├── .env                      # 環境変数（要作成）
├── pyproject.toml            # プロジェクト設定
├── pytest.ini                # pytest設定
├── capture_mock.py           # モックデータ生成スクリプト
├── uv.lock                   # 依存関係ロックファイル
└── README.md                 # このファイル
```

## 🧪 テスト

Picklesにはスモークテスト（基本動作確認テスト）とモックデータシステムが含まれています。

### モックデータシステム

テストでは、実際のNotion APIを呼び出す代わりに、`tests/fixtures/mock_data/notion/`ディレクトリに保存されたモックデータを使用します。

#### モックデータの仕組み
- 各APIキーに対応するJSONファイルが保存されています
- テスト実行時は`.env`のNOTION_API_KEYに基づいて対応するモックデータを自動選択
- 4つの異なるデータパターンで網羅的なテストが可能

#### モックデータの生成

```bash
# 全てのAPIキーのモックデータを生成
uv run python capture_mock.py --all

# 特定のAPIキーのモックデータを生成
uv run python capture_mock.py --api-key ntn_YOUR_API_KEY_HERE
```

### テストの実行

```bash
# テスト実行
uv sync --extra test
uv run pytest tests/smoke/ -m smoke
```

### テスト内容

**基本コマンドテスト** (`test_basic_commands.py`)
- ヘルプ表示、基本的な配信方法、履歴機能、日数指定オプション
- 全4つのモックデータで各機能をテスト
- モックデータの利用可能性確認

**オプション組み合わせテスト** (`test_option_combinations.py`)
- 分析タイプ（domi/aga）と配信方法の組み合わせ動作
- 全4つのモックデータで各組み合わせをテスト

**エラーハンドリングテスト** (`test_error_handling.py`)
- 無効なオプション指定時のエラー処理
- 全4つのモックデータでエラー耐性を確認


詳細は`tests/README.md`を参照してください。

## 🔒 セキュリティ

> [!WARNING]
> `.env`ファイルとAPIキーなどの機密情報は**絶対にGitにコミットしないでください**。

### 保護すべきファイル
`.gitignore`で以下がブロックされていることを確認：
```
.env
service_account_key.json
*.json # Google Service Accountキーファイル
```

### GitHub Actions セキュリティ
- 全てのAPIキーはGitHub Secretsで管理
- Google Service Accountは最小権限（Sheets読み取り、Docs読み取りのみ）
- 実行環境は`test`環境を使用


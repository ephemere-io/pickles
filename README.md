# Pickles 🥒

> Pickling everyday thoughts and feelings

NotionデータベースまたはGoogle DocsとOpenAI APIを使用して、日記エントリから感情・思考の分析レポートを自動生成・配信するPythonアプリケーションです。単体実行とマルチユーザー対応のGitHub Actions実行に対応しています。

**Phase 0実装**: Supabaseによる実行履歴管理とドメインモデルアーキテクチャを導入し、将来の発酵システム（多層ベクトル検索）への基盤を構築しました。

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

`example.env`をコピーして`.env`ファイルを作成し、以下の値を設定してください：

```bash
# example.envをコピー
cp example.env .env

# エディタで.envを開いて値を設定
```

#### 必須の環境変数

```bash
# Notion API設定（Notionを使用する場合は必須）
NOTION_API_KEY=your_notion_api_key_here

# OpenAI API設定（必須）
OPENAI_API_KEY=your_openai_api_key_here

# Supabase設定（Phase 0: 実行履歴管理）
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=sb_secret_your_key_here

# Google API設定（Google SheetsやGoogle Docsを使用する場合は必須）
# JSON全体を1行で記述してください
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"..."}

# メール設定（レポート送信に必須）
EMAIL_USER=your_email@gmail.com          # SMTP認証用ユーザー名
EMAIL_PASS=your_app_password_here        # SMTP認証用パスワード（Gmailの場合はアプリパスワード）
EMAIL_TO=recipient@example.com           # 送信先メールアドレス
EMAIL_FROM=sender@example.com            # メール送信者として表示されるアドレス
EMAIL_HOST=smtp.gmail.com                # SMTPサーバーホスト
EMAIL_PORT=587                           # SMTPポート番号
```

#### オプションの環境変数

```bash
# Google Docs入力（Notionの代わりにGoogle Docsを使用する場合）
GOOGLE_DOCS_URL=https://docs.google.com/document/d/your_document_id/edit

# テストモード（開発・テスト時のみ）
PICKLES_TEST_MODE=1                      # 1を設定するとモックデータを使用

# テスト用モックファイル指定
PICKLES_TEST_SPECIFIC_MOCK_FILE=mock_data_1.json
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
<td><code>--user-id</code></td>
<td>ユーザーID</td>
<td>UUID文字列</td>
<td>-</td>
<td>Phase 0: Supabase users テーブルのUUID（必須）</td>
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
# Phase 0: user-id指定が必須
# ユーザーIDはSupabase usersテーブルから取得

# 基本実行（Notion + DOMI + コンソール出力）
uv run python main.py --user-id "12345678-1234-1234-1234-123456789abc"

# 英語でメール送信
uv run python main.py --user-id "12345678-..." --delivery email_html --language english

# Google Docsから分析
uv run python main.py --user-id "12345678-..." --source gdocs

# 30日コンテキストでAGA分析
uv run python main.py --user-id "12345678-..." --analysis aga --days 30

# 複数配信方法
uv run python main.py --user-id "12345678-..." --delivery console,email_html,file_text

# 指定実行（Notion）
uv run python main.py --user-id "12345678-..." --user-name "田中太郎" --email-to "tanaka@example.com" --notion-api-key "secret_xxx"

# 指定実行（Google Docs）
uv run python main.py --user-id "12345678-..." --source gdocs --gdocs-url "https://docs.google.com/document/d/DOC_ID" --user-name "田中太郎"

# マルチユーザー実行（Google Sheets自動同期）
uv run python read_spreadsheet_and_execute.py --spreadsheet-id "YOUR_SHEET_ID" --analysis domi --delivery email_html

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

- **Google Sheets + Supabase自動同期**: スプレッドシートからユーザー情報を読み込み、Supabaseと自動同期
- **UUID管理**: メールアドレスをキーに永続的なUUIDを付与
- **定期実行**: 毎週月曜7:00に自動実行
- **個別設定**: ユーザーごとに言語・APIキー・送信先を設定可能
- **実行履歴記録**: 分析実行と配信の履歴をSupabaseに保存
- **手動実行**: 任意のタイミングで実行可能

</details>

<details>
<summary><strong>🗄️ Phase 0: 実行履歴管理とドメインモデル</strong> - Supabaseによる永続化</summary>

- **ユーザー管理**: Google Sheetsから自動同期、UUID管理
- **分析実行履歴**: 実行パラメータ、結果、ステータスを記録
- **配信履歴**: 配信方法、成功/失敗、エラーログを記録
- **ドメインモデルアーキテクチャ**: User, AnalysisRun, Delivery モデルで保守性向上
- **将来への準備**: Phase 1の発酵システム（多層ベクトル検索）への基盤

詳細は `docs/DATABASE_DESIGN.md` を参照

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
<summary>📄 Google API設定（Google SheetsとGoogle Docs）</summary>

1. [Google Cloud Console](https://console.cloud.google.com/)で新しいプロジェクトを作成
2. 必要なAPIを有効化:
   - Google Sheets API（マルチユーザー実行時に必要）
   - Google Docs API（Google Docs入力を使用する場合に必要）
3. Service Accountを作成し、JSONキーをダウンロード
4. Service AccountのメールアドレスをGoogle SheetsやGoogle Docsの**閲覧者として共有**
5. JSONキーの内容全体を`GOOGLE_SERVICE_ACCOUNT_KEY`環境変数に設定（1行のJSON文字列として）

**設定例:**
```bash
# JSONキー全体を1行で設定
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"...@....iam.gserviceaccount.com",...}
```

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

**Google Docs使用時の権限設定:**

Google Docsをデータソースとして使用する場合、使用する環境に応じて以下のService Accountメールアドレスを**閲覧者**として共有してください:

| 環境 | Service Accountメールアドレス |
|------|------------------------------|
| Prototype（テスト・開発） | `pickles-sheets-reader@pickles-467502.iam.gserviceaccount.com` |
| Production（本番運用） | `pickles-sheets-reader@pickles-reports.iam.gserviceaccount.com` |

**共有手順:**
1. Google Docsを開く
2. 右上の「共有」ボタンをクリック
3. 上記の該当するService Accountメールアドレスを入力
4. 権限を「閲覧者」に設定
5. 「送信」をクリック

</details>

<details>
<summary>🤖 OpenAI API設定</summary>

1. [OpenAI Platform](https://platform.openai.com/)でAPIキーを作成
2. `OPENAI_API_KEY`に設定
3. 現在はo4-miniモデルを使用（要課金）

</details>

<details>
<summary>🗄️ Supabase設定（Phase 0）</summary>

**目的**: 実行履歴管理とユーザーUUID管理

1. [Supabase](https://supabase.com/)で新規プロジェクトを作成
2. プロジェクト名: `pickles-production` (任意)
3. リージョン: `Northeast Asia (Tokyo)` を推奨
4. Settings > API タブから以下を取得:
   - **Project URL** → `SUPABASE_URL`
   - **Secret Key** (`sb_secret_...` で始まるキー) → `SUPABASE_KEY`

   注: サーバーサイド実行のためSecret Keyを使用します

**マイグレーションの適用**:

Option A: Supabase Dashboard（推奨・簡単）
```
1. Dashboard > SQL Editor を開く
2. supabase/migrations/ 配下のファイルを順番に実行:
   - 20241215000000_create_users_table.sql
   - 20241215000001_create_analysis_runs_table.sql
   - 20241215000002_create_deliveries_table.sql
   - 20241215000003_create_execution_history_view.sql
```

Option B: Supabase CLI
```bash
# CLI インストール（初回のみ）
brew install supabase/tap/supabase

# ログイン
supabase login

# プロジェクトリンク
supabase link --project-ref YOUR_PROJECT_REF

# マイグレーション適用
supabase db push
```

**確認方法**:
1. Dashboard > Table Editor を開く
2. `users`, `analysis_runs`, `deliveries` テーブルが作成されていることを確認

詳細は `docs/DATABASE_DESIGN.md` を参照

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
├── read_spreadsheet_and_execute.py  # マルチユーザー実行スクリプト（Google Sheets同期）
├── models/                    # ドメインモデル（Phase 0）
│   ├── __init__.py
│   ├── user.py               # Userドメインモデル（Google Sheets同期）
│   ├── analysis_run.py       # AnalysisRunドメインモデル（実行履歴）
│   └── delivery.py           # Deliveryドメインモデル（配信履歴）
├── supabase/                  # Supabase関連（Phase 0）
│   ├── migrations/           # マイグレーションファイル
│   │   ├── 20241215000000_create_users_table.sql
│   │   ├── 20241215000001_create_analysis_runs_table.sql
│   │   ├── 20241215000002_create_deliveries_table.sql
│   │   └── 20241215000003_create_execution_history_view.sql
│   └── client.py             # Supabaseクライアント初期化
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
│   ├── printer.py            # ヘルプ表示・定数定義
│   └── google_service.py     # Google API認証・サービス初期化
├── docs/                      # ドキュメント
│   ├── DATABASE_DESIGN.md    # Phase 0: データベース設計
│   └── FERMENTATION_DESIGN.md # Phase 1+: 発酵システム設計
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
│   ├── pickles-report-production.yml  # 本番環境マルチユーザー実行
│   ├── pickles-report-prototype.yml   # テスト環境マルチユーザー実行
│   ├── pickles-report-admin.yml       # 管理者環境実行
│   └── setup-secrets.md      # GitHub Actions設定ガイド
├── example.env               # 環境変数のテンプレート
├── .env                      # 環境変数（要作成、Gitにコミットしない）
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
**/service-account-*.json
```

### 環境変数のセキュリティ
- `.env`ファイルには本番用のAPIキーやパスワードを保存
- `example.env`はテンプレートとして公開可能（実際の値を含まない）
- `GOOGLE_SERVICE_ACCOUNT_KEY`にはJSON全体を1行で設定

### GitHub Actions セキュリティ
- 全てのAPIキーはGitHub Secretsで管理
- Google Service Accountは最小権限（Sheets読み取り、Docs読み取りのみ）
- 実行環境は`test`環境を使用

### 必要なGitHub Secrets
GitHub Actionsを使用する場合、以下のSecretsを設定してください：

**Phase 0で追加**:
- `SUPABASE_URL`: Supabaseプロジェクトの URL
- `SUPABASE_KEY`: Supabase Secret Key (`sb_secret_...` 形式)

**既存のSecrets**:
- `OPENAI_API_KEY`: OpenAI APIキー
- `GOOGLE_SERVICE_ACCOUNT_KEY`: Google Service AccountのJSON鍵（全体）
- `EMAIL_USER`: メール送信用ユーザー名
- `EMAIL_PASS`: メール送信用パスワード
- `EMAIL_FROM`: 送信者アドレス
- `EMAIL_HOST`: SMTPホスト
- `EMAIL_PORT`: SMTPポート
- `SPREADSHEET_ID_USERS_LIST`: ユーザーリストのGoogle Sheets ID（マルチユーザー実行用）
- `SPREADSHEET_ID_ADMIN_LIST`: 管理者リストのGoogle Sheets ID（管理者実行用）


# Pickles 🥒

> Pickling everyday thoughts and feelings

NotionデータベースとOpenAI APIを使用して、日記エントリから感情・思考の分析レポートを自動生成・配信するPythonアプリケーションです。単体実行とマルチユーザー対応のGitHub Actions実行に対応しています。

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
| `--user-name` | ユーザー名 | 文字列 | 環境変数 |
| `--email-to` | 送信先メールアドレス | メールアドレス | 環境変数 |
| `--notion-api-key` | Notion APIキー | APIキー文字列 | 環境変数 |
| `--help` | ヘルプ表示 | フラグ | false |

## 🔍 Notion分析処理の詳細フロー（2025/07/29時点）

Picklesがどのようにデータを取得・分析しているかを詳しく説明します。

### 処理の流れ（実行順序）

#### 1. **プログラム起動**（`main.py`）
```
uv run python main.py --analysis domi --delivery console
```
- コマンドライン引数を解析
- `PicklesSystem`クラスをインスタンス化
- `run_analysis()`メソッドを実行

#### 2. **データ取得フェーズ**（`inputs/notion_input.py`）

##### **2-0. API接続確認**（初期化時）
- ユーザー情報取得でAPIキー有効性を確認
- サンプル検索でアクセス権限を確認

`NotionInput.fetch_notion_documents(days=7)`が実行され、以下の優先順位でデータを取得：

1. **データベース検索を試行**
   - Notion APIで利用可能なデータベースを検索
   - 見つかった場合、最初のデータベースにアクセス
   
2. **データベースからエントリ取得**（データベースが見つかった場合）
   - `Date`プロパティでフィルタリング（過去7日分）
   - 失敗した場合は`Created time`でフィルタリング
   - 各エントリから以下を抽出：
     - **タイトル**: タイトルプロパティから
     - **日付**: Dateプロパティまたは作成日時
     - **コンテンツ**: 
       - データベースのプロパティ（rich_text, select, multi_select, url, email, phone_number, number, checkbox）
       - ページ本体のブロック（paragraph, heading_1-3, lists, quote, callout, code, toggle, table_row, bookmark, link_preview）

3. **通常のページ検索**（データベースが見つからない場合）
   - 最近編集されたページを検索（ページネーション対応）
   - 大規模ワークスペース対応（最大100件ずつ取得）
   - 各ページから同様にタイトル、日付、コンテンツを抽出

#### 3. **分析処理フェーズ**（`throughput/analyzer.py`）
`DocumentAnalyzer.analyze_documents(raw_data, analysis_type="domi")`が実行：

1. **データの前処理**
   - 取得したデータをそのまま使用（フィルタリングは無効化）
   - データを分析用フォーマットに整形

2. **分析履歴の取得**（`--history on`の場合）
   - `analysis_history.json`から過去3回分の分析を読み込み
   - 分析タイプ（domi/aga）別に履歴を管理

3. **プロンプト生成**
   - **domi分析**（`throughput/prompts/domi_prompts.py`）: 
     - 「ゆらぎ」「ゆだね」「ゆとり」の観点から分析
     - コード化・概念抽出・手紙形式での振り返り
   - **aga分析**（`throughput/prompts/aga_prompts.py`）:
     - より詩的で抽象的な分析アプローチ

4. **OpenAI API呼び出し**
   - モデル: `o1-mini`
   - 最大トークン数: 50,000
   - 分析履歴を含めてリクエスト送信

5. **結果の保存**
   - 分析結果を`analysis_history.json`に追加
   - 最新10件のみ保持（古い履歴は自動削除）

#### 4. **レポート生成・配信フェーズ**（`outputs/report_generator.py`）
`ReportDelivery.deliver_report(analysis_results, delivery_methods=["console"])`が実行：

1. **レポート生成**
   - データ統計（件数、平均文字数）を計算
   - AI分析結果を整形
   - 日付・時刻を付加

2. **配信方法別の処理**
   - **console**: ターミナルに表示
   - **email_text/email_html**: メールで送信
   - **file_text/file_html**: ファイルに保存

### 実際に分析される内容

#### Notionデータベースの場合
- **プロパティ情報**: rich_text, select, multi_select, url, email, phone_number, number, checkbox プロパティ
- **ページコンテンツ**: 各エントリのページ本体に書かれた内容
- **メタデータ**: 作成日時、タイトル

#### 通常のNotionページの場合
- **ページタイトル**
- **ページ本文**: paragraph, heading_1-3, lists, quote, callout, code, toggle, table_row, bookmark, link_preview ブロック
- **作成日時・編集日時**

### デバッグ情報
実行時に以下のようなデバッグ情報が表示されます：

#### API接続・権限確認
```
✅ Notion API接続成功: [ユーザー名]
📊 アクセス可能なページ数（サンプル）: 5+
```

#### データベース検索
```
🗄️  データベースを検索中...
📊 3個のデータベースが見つかりました
📂 データベース 'Daily Notes' (ID: abcd1234...) を使用
```

#### ページ検索（フォールバック時）
```
🔎 ページ検索を実行中...
📄 取得済み: 100件 (has_more: true)
📑 検索で合計145件のページが見つかりました
```

#### コンテンツ抽出
```
📋 プロパティから5項目のコンテンツを抽出
✅ ページ abcd1234... のコンテンツを取得（256文字）
⚠️  データベースエントリ efgh5678... のコンテンツが空です
📅 日付フィルタ: 作成2025-07-15, 編集2025-07-16 < 2025-07-22 (除外)
```

## 🧠 AI分析履歴機能

Picklesは**OpenAI o1-miniのResponses API履歴機能**を活用し、過去の分析結果を踏まえた継続的な洞察を提供します。

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
├── read_spreadsheet_and_execute.py  # マルチユーザー実行スクリプト
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
├── analysis_history.json     # AI分析履歴データ（自動生成）
├── pyproject.toml            # プロジェクト設定
├── pytest.ini                # pytest設定
├── capture_mock.py           # モックデータ生成スクリプト
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

## 🤖 GitHub Actions マルチユーザー実行

複数ユーザーの分析を自動化するGitHub Actions機能が利用できます。

### 機能概要
- Google Sheetsからユーザー情報を読み込み
- 各ユーザーに個別のレポートを配信
- 手動実行または定期実行（毎週月曜9時）
- デバッグモード対応

### 実行パラメータ
| パラメータ | 説明 | 選択肢 | デフォルト |
|-----------|------|--------|------------|
| `analysis_type` | 分析タイプ | `domi`, `aga` | `domi` |
| `delivery_method` | 配信方法 | `email_html`, `email_text`, `console`, `file_text`, `file_html` | `email_html` |
| `days_back` | 取得日数 | 整数値 | `7` |
| `debug_mode` | デバッグモード | `true`, `false` | `false` |

### 設定方法
詳細な設定手順は`.github/workflows/setup-secrets.md`を参照してください：
- GitHub Secrets設定
- Google Service Account作成
- Google Sheets API設定
- スプレッドシート構造
- 各ユーザーのNotion設定

### マルチユーザー実行コマンド
```bash
# Google Sheetsからマルチユーザー実行
python read_spreadsheet_and_execute.py --spreadsheet-id "SPREADSHEET_ID" --analysis domi --delivery email_html

# 単体ユーザー実行（マルチユーザー対応オプション付き）
python main.py --user-name "田中太郎" --email-to "tanaka@example.com" --notion-api-key "secret_xxx"
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
```

### GitHub Actions セキュリティ
- 全てのAPIキーはGitHub Secretsで管理
- Google Service Accountは最小権限（Sheets読み取りのみ）
- 実行環境は`test`環境を使用
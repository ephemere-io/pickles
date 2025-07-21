# GitHub Actions 環境変数設定ガイド

このガイドでは、Pickles Weekly ReportをGitHub Actionsで実行するために必要な環境変数の設定方法を説明します。

## ワークフロー

**weekly-report.yml**: テスト・本番両用のワークフロー
- **現在はスケジュール実行を無効化済み（手動実行のみ）**
- 手動実行時のデフォルトは`console`配信（テスト向け）
- テスト完了後、schedule部分のコメントを外して自動実行を有効化
- パラメータ変更可能：
  - **analysis_type**: 分析タイプ（`domi` または `aga`）
  - **delivery_method**: 配信方法（テスト時は`console`推奨）
  - **debug_mode**: デバッグ情報出力
  - **days_back**: 取得日数（テスト用）

## ⚠️ 自動実行の注意点

`weekly-report.yml`をpushすると、schedule設定がある場合は即座に自動実行が開始されます。
現在のファイルはschedule部分をコメントアウトしているため安全です。

## 1. GitHub リポジトリの設定

1. GitHubでPicklesリポジトリを開く
2. Settings → Environments に移動
3. "New environment" をクリックして `production` という名前で環境を作成

## 2. 必要なシークレットの設定

Settings → Secrets and variables → Actions から以下のシークレットを追加してください：

### Notion API設定
- **NOTION_API_KEY**: Notion Integration Token
  - [Notion Developers](https://www.notion.so/my-integrations) でIntegrationを作成
  - "Internal Integration Token"をコピー
  
- **NOTION_PAGE_ID**: 分析対象のNotionページID
  - NotionでページのURLからID部分をコピー
  - 例: `https://notion.so/xxxxx` の `xxxxx` 部分

### OpenAI API設定
- **OPENAI_API_KEY**: OpenAI APIキー
  - [OpenAI Platform](https://platform.openai.com/api-keys) で取得

### メール設定
- **EMAIL_USER**: 送信元メールアドレス
- **EMAIL_PASS**: メールパスワード（アプリパスワード推奨）
- **EMAIL_TO**: 送信先メールアドレス
- **EMAIL_HOST**: SMTPサーバーアドレス
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
- **EMAIL_PORT**: SMTPポート番号
  - 通常: `587` (TLS)
  - SSL: `465`

## 3. Gmailを使用する場合の追加設定

Gmailを使用する場合は、アプリパスワードの生成が必要です：

1. [Googleアカウント設定](https://myaccount.google.com/security) にアクセス
2. 2段階認証を有効化
3. "アプリパスワード"を検索して選択
4. アプリ名に"Pickles"と入力してパスワードを生成
5. 生成されたパスワードを**EMAIL_PASS**に設定

## 4. ワークフローの実行手順

### ステップ1: テスト実行
1. Actionsタブを開く
2. "Weekly Pickles Report"を選択
3. "Run workflow"をクリック
4. テスト用の設定：
   - **analysis_type**: `domi`（または `aga`）
   - **delivery_method**: `console`（ログに出力される）
   - **debug_mode**: `true`（環境変数確認）
   - **days_back**: `7`（テスト用）
5. "Run workflow"ボタンをクリック

### ステップ2: メール配信テスト
1. 上記と同じ手順で"Run workflow"をクリック
2. テスト用の設定：
   - **delivery_method**: `email_html`
   - 他は同じ
3. メールが正常に届くか確認

### ステップ3: 自動実行を有効化
テストが成功したら：
1. `.github/workflows/weekly-report.yml`の4-6行目のコメントを外す
2. コミット・プッシュ
3. 毎週月曜日午前9時に自動実行開始

## トラブルシューティング

### エラーが発生した場合
1. Actions タブでワークフローの実行ログを確認
2. 環境変数が正しく設定されているか確認
3. Notion IntegrationがデータベースにアクセスできるかNotionで確認
# GitHub Actions マルチユーザー実行設定ガイド

このガイドでは、Pickles Multi-User ReportをGitHub Actionsで実行するために必要な環境変数とGoogle Sheets設定を説明します。

## ワークフロー概要

**weekly-report.yml**: マルチユーザー対応のワークフロー
- Google Sheetsからユーザーデータを読み込み、各ユーザーに個別レポートを送信
- **現在はスケジュール実行を無効化済み（手動実行のみ）**
- 手動実行時のパラメータ：
  - **spreadsheet_id**: Google SpreadsheetsのID（必須）
  - **analysis_type**: 分析タイプ（`domi` または `aga`）
  - **delivery_method**: 配信方法（`email_html`推奨）
  - **days_back**: 取得日数
  - **debug_mode**: デバッグ情報出力

## ⚠️ 自動実行の注意点

`weekly-report.yml`をpushすると、schedule設定がある場合は即座に自動実行が開始されます。
現在のファイルはschedule部分をコメントアウトしているため安全です。

## 1. GitHub リポジトリの設定

1. GitHubでPicklesリポジトリを開く
2. Settings → Environments に移動
3. "New environment" をクリックして `production` という名前で環境を作成

## 2. 必要なシークレットの設定

Settings → Secrets and variables → Actions から以下のシークレットを追加してください：

### OpenAI API設定
- **OPENAI_API_KEY**: OpenAI APIキー
  - [OpenAI Platform](https://platform.openai.com/api-keys) で取得
  - o4-miniモデルを使用するため課金設定が必要

### メール設定（共通のメール送信設定）
- **EMAIL_USER**: 送信元メールアドレス
- **EMAIL_PASS**: メールパスワード（アプリパスワード推奨）
- **EMAIL_HOST**: SMTPサーバーアドレス
  - Gmail: `smtp.gmail.com`
  - Outlook: `smtp-mail.outlook.com`
- **EMAIL_PORT**: SMTPポート番号
  - 通常: `587` (TLS)
  - SSL: `465`

### Google Sheets API設定
- **GOOGLE_SERVICE_ACCOUNT_KEY**: Google Service Accountの認証情報（JSON形式）
  - 下記「Google Service Account設定」の手順で取得
- **SPREADSHEET_ID**: デフォルトのスプレッドシートID（オプション）
  - 手動実行時に毎回入力したくない場合に設定

## 3. Google Service Account設定

### ステップ1: Google Cloud Projectの作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. プロジェクト名: 例「pickles-reports」

### ステップ2: Google Sheets APIの有効化
1. 左メニューの「APIとサービス」→「ライブラリ」を選択
2. "Google Sheets API"を検索して選択
3. 「有効にする」をクリック

### ステップ3: Service Accountの作成
1. 左メニューの「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「サービスアカウント」をクリック
3. サービスアカウントの詳細：
   - **サービスアカウント名**: `pickles-sheets-reader`
   - **説明**: `Pickles用Google Sheets読み取り`
4. 「作成して続行」をクリック
5. 役割の設定は不要（「完了」をクリック）

### ステップ4: 認証キーの生成
1. 作成されたサービスアカウントをクリック
2. 「キー」タブを選択
3. 「鍵を追加」→「新しい鍵を作成」をクリック
4. 「JSON」を選択して「作成」をクリック
5. ダウンロードされたJSONファイルの内容をコピー
6. GitHubの**GOOGLE_SERVICE_ACCOUNT_KEY**シークレットに設定

## 4. Google Sheetsの準備

### スプレッドシートの構造
以下の構造でスプレッドシートを作成してください：

| A列（EMAIL_TO） | B列（NOTION_API_KEY） | C列（user name） | D列（備考） |
|---|---|---|---|
| tanaka@example.com | ntn_abc123... | 田中太郎 | （オプション） |
| sato@example.com | ntn_def456... | 佐藤花子 | （オプション） |
| yamada@example.com | ntn_ghi789... | 山田次郎 | （オプション） |

### スプレッドシートの共有設定
1. 作成したスプレッドシートを開く
2. 右上の「共有」ボタンをクリック
3. 作成したService Accountのメールアドレス（`pickles-sheets-reader@xxx.iam.gserviceaccount.com`）を追加
4. 権限を「閲覧者」に設定
5. 「送信」をクリック

### スプレッドシートIDの取得
スプレッドシートのURLから抽出：
```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
```
`[SPREADSHEET_ID]`の部分をコピーしてください。

## 5. Gmailを使用する場合の追加設定

Gmailを使用する場合は、アプリパスワードの生成が必要です：

1. [Googleアカウント設定](https://myaccount.google.com/security) にアクセス
2. 2段階認証を有効化
3. "アプリパスワード"を検索して選択
4. アプリ名に"Pickles"と入力してパスワードを生成
5. 生成されたパスワードを**EMAIL_PASS**に設定

## 6. 各ユーザーのNotion設定

スプレッドシートに登録する各ユーザーは以下の設定が必要です：

### Notion API設定
1. [Notion Developers](https://www.notion.so/my-integrations) でIntegrationを作成
2. "Internal Integration Token"をコピー
3. スプレッドシートのB列（NOTION_API_KEY）に設定

### Notionワークスペースの共有
1. 分析対象のNotionページまたはデータベースを開く
2. 右上の「共有」→「招待」をクリック
3. 作成したIntegrationを選択して招待

## 7. ワークフローの実行手順

### ステップ1: テスト実行（console出力）
1. Actionsタブを開く
2. "Multi-User Pickles Report"を選択
3. "Run workflow"をクリック
4. テスト用の設定：
   - **spreadsheet_id**: 作成したスプレッドシートのID
   - **analysis_type**: `domi`（または `aga`）
   - **delivery_method**: `console`（ログに出力される）
   - **debug_mode**: `true`（環境変数確認）
   - **days_back**: `7`
5. "Run workflow"ボタンをクリック

### ステップ2: メール配信テスト
1. 上記と同じ手順で"Run workflow"をクリック
2. 本番用の設定：
   - **delivery_method**: `email_html`
   - 他は同じ
3. 各ユーザーにメールが正常に届くか確認

### ステップ3: 自動実行を有効化
テストが成功したら：
1. `.github/workflows/weekly-report.yml`の4-6行目のコメントを外す
2. デフォルトのスプレッドシートIDを設定（環境変数 `SPREADSHEET_ID`）
3. コミット・プッシュ
4. 毎週月曜日午前9時に自動実行開始

## 8. セキュリティ考慮事項

### Google Service Account
- 最小限の権限（Google Sheets読み取りのみ）
- プロジェクト単位での権限管理

### Notion APIキー
- スプレッドシートに平文保存
- GitHub Actionsログに表示される可能性があるが、Notion APIキーはワークスペース単位の権限のため影響は限定的

### メール設定
- 共通の送信設定を使用
- 各ユーザーの送信先は個別に設定

## トラブルシューティング

### よくあるエラー

#### 1. Google Sheets APIエラー
```
❌ Google Sheets API エラー: 403 The caller does not have permission
```
**解決策**: Service Accountをスプレッドシートに共有しているか確認

#### 2. Notion APIエラー
```
❌ Notion API接続エラー: unauthorized
```
**解決策**: 各ユーザーのNotion APIキーとIntegration共有設定を確認

#### 3. メール送信エラー
```
❌ HTMLメール送信エラー: authentication failed
```
**解決策**: EMAIL_PASSにアプリパスワードを設定しているか確認

### デバッグ手順
1. Actions タブでワークフローの実行ログを確認
2. `debug_mode: true` で環境変数の設定状況を確認
3. 1ユーザーずつテストして問題を特定

### サポート情報
- Google Cloud Console: Service Account設定の確認
- Notion Developers: Integration設定の確認
- GitHub Actions: 実行ログとエラー詳細の確認
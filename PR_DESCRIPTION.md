# プルリクエスト: コマンドライン引数の整理とドキュメント改善

## Why

このPRは、Picklesシステムのコマンドライン引数とドキュメントを整理・改善するために作成されました。

### 背景と課題
1. **重複ファイルの存在**: `setup-secrets.md`とREADMEで同じ設定情報が重複していた
2. **非一貫な言語指定**: 言語オプションで`日本語`/`English`という混在した形式を使用
3. **廃止機能の残存**: 使用されなくなった`--schedule`（定期実行）と`--history`（分析履歴）機能がコードに残っていた
4. **ヘルプシステムの改善要求**: より分かりやすい使用方法の表示が必要

### 解決すべき問題
- ユーザビリティの向上（認知負荷の軽減）
- 一貫性のあるオプション体系の確立
- 不要なコードの除去とメンテナンス性の向上

## What

以下の修正を実施しました：

### 1. ファイル整理・統合 📄

#### 削除されたファイル
- `.github/workflows/setup-secrets.md` - READMEに統合したため削除

#### 統合・改善されたファイル
- `README.md` - 視覚的なコマンドリファレンステーブルを追加、アコーディオン形式の説明を導入

### 2. 言語オプションの標準化 🌐

**変更前:**
```bash
# 混在した形式（非推奨）
python main.py --language 日本語
python main.py --language English
```

**変更後:**
```bash
# 統一されたアルファベット形式（推奨）
python main.py --language japanese
python main.py --language english
```

#### 影響を受けるファイル
- `main.py` - 引数解析ロジックの更新
- `throughput/analyzer.py` - 言語マッピング機能追加
- `utils/printer.py` - ヘルプシステムの表示更新
- `.github/workflows/pickles-report.yml` - GitHub Actions設定の更新

### 3. 廃止機能の完全削除 🗑️

#### 削除された機能
- **`--schedule`オプション**: 定期実行モード
  - APSchedulerライブラリの依存関係を削除
  - 関連するすべてのスケジューリングコードを除去
- **`--history`オプション**: 分析履歴機能
  - `throughput/analysis_history.py`ファイルを完全削除
  - 履歴管理に関するすべてのロジックを除去

### 4. ヘルプシステムの改善 📖

#### 新しいヘルプ構造
```
🥒 Pickles - Personal Insight Analytics System

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 基本オプション
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  --analysis <type>      分析タイプ (domi/aga)
  --delivery <method>    配信方法 (console/email_*/file_*)
  --days <number>        分析日数 (デフォルト: 7)
  --language <lang>      出力言語 (japanese/english)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 指定実行設定
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  --user-name <name>     ユーザー名
  --email-to <email>     送信先メールアドレス
  --notion-api-key <key> Notion APIキー
  --gdocs-url <url>      Google Docs URL
```

### 5. テストシステムの改善 ✅

#### テスト設定の修正
- **実行環境の修正**: `uv`コマンド依存から仮想環境Python直接実行に変更
- **パス設定の修正**: 正しいプロジェクトパスに更新
- **廃止機能テストの削除**: `--history`関連テストを完全除去
- **日付範囲の調整**: モックデータとの互換性を改善（45日間に拡大）

#### テスト結果
```
============================= 17 passed in 3.76s ==============================
```

### 6. コマンド実行方法の変更 🔧

#### GitHub Actions実行コマンド
```yaml
# .github/workflows/pickles-report.yml
# 変更前
- language: 日本語

# 変更後  
- language: japanese
```

#### ローカル実行コマンド例

**基本実行（変更なし）:**
```bash
python main.py
```

**言語指定実行（変更あり）:**
```bash
# 変更前（非推奨）
python main.py --language 日本語

# 変更後（推奨）
python main.py --language japanese
python main.py --language english
```

**廃止されたコマンド:**
```bash
# これらのオプションは削除されました
python main.py --schedule daily          # ❌ 削除
python main.py --history on              # ❌ 削除
```

**新しい推奨コマンド例:**
```bash
# 日本語で30日分のDOMI分析をメール送信
python main.py --analysis domi --days 30 --delivery email_html --language japanese

# 英語で7日分のAGA分析をファイル出力
python main.py --analysis aga --delivery file_text --language english

# Google Docsから分析
python main.py --source gdocs --gdocs-url "https://docs.google.com/document/d/DOC_ID"
```

### 7. 技術的改善点 🔧

#### コードの簡素化
- 不要なimportの削除（APScheduler関連）
- 条件分岐の簡素化（履歴機能削除による）
- エラーハンドリングの改善

#### メンテナンス性の向上
- 一貫性のあるオプション命名規則
- 明確な機能分離
- テストカバレッジの改善

## 初学者向けの理解ポイント 📚

### このPRで学べること
1. **コマンドライン引数の設計**: ユーザビリティを考慮したオプション設計
2. **国際化対応**: 言語オプションの適切な実装方法
3. **レガシーコード削除**: 廃止機能の安全な除去手法
4. **テスト駆動開発**: リファクタリング時のテスト重要性
5. **ドキュメント保守**: ユーザーフレンドリーな説明の書き方

### 実用的な学習ポイント
- Python argparseの活用方法
- 設定ファイルと環境変数の使い分け
- GitHub Actionsでのパラメータ渡し
- pytestを使った統合テスト

## 影響範囲 🎯

### 破壊的変更
- `--language`オプションの値変更（`日本語`→`japanese`、`English`→`english`）
- `--schedule`、`--history`オプションの完全削除

### 非破壊的変更  
- その他の基本的な実行コマンドは変更なし
- 既存の設定ファイル（.env等）への影響なし

## 今後の課題 🚀

1. **ユーザーへの移行案内**: 既存ユーザーへの言語オプション変更通知
2. **ドキュメント更新**: 関連ドキュメントの最新情報反映
3. **エラーメッセージ改善**: 廃止オプション使用時の親切な案内追加

---

このPRは、システムの使いやすさと保守性を大幅に向上させる重要な改善です。特にコマンドライン引数の整理により、新規ユーザーの学習コストを削減し、既存ユーザーの作業効率を向上させます。
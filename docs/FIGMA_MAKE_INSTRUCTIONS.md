# Figma Make 指示書: WYSIWYG マークダウンエディタ

> 本ドキュメントは Figma Make の AI チャットに入力するプロンプトを段階別に整理したものです。
> 各フェーズのプロンプトを順番に入力してください。

---

## 事前準備

### Guidelines.md に設定する内容

Figma Make のファイル内 `guidelines/` フォルダに以下の `Guidelines.md` を作成してください。

```markdown
# プロジェクトガイドライン

## 概要
日記・ジャーナルの分析アプリケーション「pickles」のフロントエンドです。
ユーザーが WYSIWYG エディタでテキストを入力し、マークダウン形式で保存します。

## デザイン原則
- 日本語をメインの表示言語とする
- 落ち着いた配色（ダークモード対応を前提）
- 書くことに集中できるミニマルな UI
- モバイルファーストのレスポンシブデザイン

## 技術スタック
- React + TypeScript
- Tiptap（WYSIWYG エディタ）
- Supabase（バックエンド）
- CSS Modules またはインラインスタイル

## カラートークン
- `--color-bg-primary`: #FAFAFA (ライト) / #1A1A2E (ダーク)
- `--color-bg-secondary`: #FFFFFF (ライト) / #16213E (ダーク)
- `--color-text-primary`: #2D2D2D (ライト) / #E8E8E8 (ダーク)
- `--color-text-secondary`: #6B7280 (ライト) / #9CA3AF (ダーク)
- `--color-accent`: #6366F1 (インディゴ)
- `--color-accent-hover`: #4F46E5
- `--color-border`: #E5E7EB (ライト) / #374151 (ダーク)
- `--color-surface`: #F9FAFB (ライト) / #1F2937 (ダーク)

## タイポグラフィ
- フォントファミリー: "Noto Sans JP", "Inter", sans-serif
- 本文: 16px / line-height 1.75
- 見出し H1: 28px / font-weight 700
- 見出し H2: 22px / font-weight 600
- 見出し H3: 18px / font-weight 600
- エディタ内テキスト: 16px / line-height 1.8

## スペーシング
- 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px

## コンポーネントルール
- ボタンは角丸 8px
- カードは角丸 12px、shadow: 0 1px 3px rgba(0,0,0,0.1)
- エディタエリアは最大幅 720px、中央揃え
- ツールバーアイコンは 20x20px
```

---

## フェーズ 1: エディタ画面の基本レイアウト

以下のプロンプトを Figma Make に入力してください。

### プロンプト 1-1: 全体レイアウト

```
WYSIWYGマークダウンエディタのメイン画面を作成してください。

【レイアウト構成】
- 画面上部: 固定ヘッダーバー（高さ 56px）
  - 左側: アプリロゴ「pickles」テキスト（accent カラー、font-weight 700）
  - 中央: ドキュメントタイトル（編集可能なテキストフィールド、プレースホルダー「無題のドキュメント」）
  - 右側: ユーザーアバター（32x32px 丸形）と保存状態インジケーター（「保存済み」「保存中...」）
- ヘッダー直下: エディタツールバー（高さ 44px、ボーダーボトム付き）
- メインエリア: エディタ本体（最大幅 720px、左右 auto マージンで中央揃え、上下パディング 48px）
- エディタ本体にはプレースホルダーテキスト「ここに書き始めましょう...」を表示

【スタイル】
- 背景: --color-bg-primary
- ヘッダー背景: --color-bg-secondary
- ツールバー背景: --color-bg-secondary
- 全体的にクリーンでミニマルなデザイン
- フォントは Noto Sans JP を使用
```

### プロンプト 1-2: エディタツールバー

```
エディタツールバーの詳細を実装してください。

【ツールバー構成（左から順に）】
グループ1（テキストスタイル）:
- 段落/見出しドロップダウン（「本文」「見出し1」「見出し2」「見出し3」を選択可能）
- セパレーター（縦線 1px、高さ 24px、color-border）

グループ2（インライン書式）:
- 太字ボタン（B アイコン、太字）
- 斜体ボタン（I アイコン、斜体）
- 取り消し線ボタン（S アイコン、取り消し線付き）
- コードボタン（</> アイコン）
- セパレーター

グループ3（ブロック要素）:
- 箇条書きリストボタン
- 番号付きリストボタン
- チェックリストボタン
- 引用ボタン
- コードブロックボタン
- セパレーター

グループ4（挿入）:
- リンク挿入ボタン（鎖アイコン）
- 画像挿入ボタン
- テーブル挿入ボタン
- 水平線挿入ボタン

【動作】
- 各ボタンは hover で背景色が --color-surface に変化
- アクティブ状態（現在のカーソル位置で適用中の書式）のボタンは背景色 --color-accent、テキスト色 白
- ボタンサイズ: 32x32px、角丸 6px
- ボタン間の間隔: 2px
- ツールバー左右パディング: 16px
- ツールバーは上部に固定（sticky）
```

---

## フェーズ 2: エディタ内のリッチテキスト表示

### プロンプト 2-1: エディタ内コンテンツのスタイリング

```
エディタ本体内でマークダウン要素が WYSIWYG 表示されるスタイルを実装してください。

【各要素のスタイル】
見出し1:
- font-size: 28px, font-weight: 700, margin-top: 32px, margin-bottom: 16px
- color: --color-text-primary

見出し2:
- font-size: 22px, font-weight: 600, margin-top: 24px, margin-bottom: 12px
- color: --color-text-primary

見出し3:
- font-size: 18px, font-weight: 600, margin-top: 20px, margin-bottom: 8px
- color: --color-text-primary

段落:
- font-size: 16px, line-height: 1.8, margin-bottom: 12px
- color: --color-text-primary

太字: font-weight: 700
斜体: font-style: italic
取り消し線: text-decoration: line-through, opacity: 0.7

リンク:
- color: --color-accent, text-decoration: underline
- hover で --color-accent-hover

箇条書きリスト:
- padding-left: 24px, list-style-type: disc
- ネストは indent 追加、circle → square

番号付きリスト:
- padding-left: 24px, list-style-type: decimal

チェックリスト:
- チェックボックス（18x18px）+ テキスト
- 完了項目は opacity: 0.5、取り消し線

引用ブロック:
- 左ボーダー: 4px solid --color-accent
- padding: 12px 16px, background: --color-surface
- font-style: italic, color: --color-text-secondary

コードブロック:
- background: #1E1E1E (ダーク固定), color: #D4D4D4
- font-family: "JetBrains Mono", "Fira Code", monospace
- font-size: 14px, padding: 16px, border-radius: 8px
- 右上に言語ラベル表示（小さいバッジ）

インラインコード:
- background: --color-surface, border: 1px solid --color-border
- padding: 2px 6px, border-radius: 4px
- font-family: monospace, font-size: 14px

水平線:
- height: 1px, background: --color-border, margin: 24px 0

テーブル:
- border: 1px solid --color-border
- ヘッダー行: background --color-surface, font-weight: 600
- セル padding: 8px 12px
- 偶数行に薄い背景色

画像:
- max-width: 100%, border-radius: 8px
- margin: 16px 0
- クリックで拡大表示

【サンプルコンテンツ】
エディタ内に以下のサンプルコンテンツをデフォルト表示してください:

# 今日の振り返り
## 午前中の出来事
今日は**とても良い天気**だったので、朝から*散歩*に出かけました。

### やったこと
- コードレビューを完了
- ドキュメントの更新
- [ ] 夕食の買い物
- [x] メールの返信

> 「継続は力なり」— この言葉を忘れずに。

`console.log("hello")` のようなコードも書けます。
```

---

## フェーズ 3: モーダルとポップオーバー

### プロンプト 3-1: リンク挿入ダイアログ

```
リンク挿入用のポップオーバーを作成してください。

【表示条件】
- ツールバーのリンクボタンをクリック、またはテキスト選択中に Ctrl+K

【構成】
- ポップオーバー（幅 320px、shadow-lg、角丸 8px）
- URL 入力フィールド（プレースホルダー「URLを入力」）
- テキスト入力フィールド（プレースホルダー「表示テキスト」、選択テキストがあれば自動入力）
- 「挿入」ボタン（accent カラー）と「キャンセル」ボタン
- ポップオーバーの外をクリックで閉じる
```

### プロンプト 3-2: 画像挿入ダイアログ

```
画像挿入用のモーダルダイアログを作成してください。

【構成】
- モーダル（幅 480px、中央表示、背景オーバーレイ付き）
- タブ切り替え:「URL」「アップロード」
- URL タブ: URL 入力フィールド + プレビュー表示エリア
- アップロードタブ: ドラッグ&ドロップエリア（破線ボーダー、中央にアイコンとテキスト「画像をドラッグ&ドロップ、またはクリックして選択」）
- alt テキスト入力フィールド
- 「挿入」と「キャンセル」ボタン
```

### プロンプト 3-3: スラッシュコマンドメニュー

```
エディタ内でスラッシュ（/）を入力すると表示されるコマンドメニューを作成してください。

【表示条件】
- 行頭で「/」を入力したとき、カーソル位置の直下にフローティングメニュー表示

【メニュー項目】（アイコン + ラベル + 説明の3カラム構成）
- 見出し1 | 大きな見出し
- 見出し2 | 中サイズの見出し
- 見出し3 | 小さな見出し
- 箇条書きリスト | 箇条書きを作成
- 番号付きリスト | 番号付きリストを作成
- チェックリスト | タスクリストを作成
- 引用 | 引用ブロックを挿入
- コードブロック | コードを記述
- テーブル | テーブルを挿入
- 画像 | 画像を挿入
- 水平線 | 区切り線を挿入

【動作】
- キーボードの上下矢印で選択を移動（ハイライト表示）
- Enter で選択を確定
- 「/」の後にテキストを入力するとフィルタリング（例: 「/見」で見出し系のみ表示）
- Escape でメニューを閉じる
- メニュー幅: 280px、max-height: 320px、スクロール可能
- shadow-lg、角丸 8px、背景 --color-bg-secondary
```

---

## フェーズ 4: フローティングツールバー（バブルメニュー）

### プロンプト 4-1: テキスト選択時のフローティングメニュー

```
テキストを選択したときに表示されるフローティングツールバー（バブルメニュー）を作成してください。

【表示条件】
- テキストをドラッグ選択したとき、選択範囲の上部中央に表示

【構成】
- 横一列のコンパクトなツールバー（高さ 36px）
- 背景: ダークグレー (#1F2937)、角丸 8px、shadow-lg
- アイコンカラー: 白
- ボタン: 太字 | 斜体 | 取り消し線 | コード | リンク
- 各ボタン間にセパレーターなし（連続配置）
- hover で背景が少し明るく
- アクティブ状態のボタンはアクセントカラー背景

【アニメーション】
- fade-in（150ms ease-out）で表示
- 選択解除で fade-out
```

---

## フェーズ 5: サイドバーとドキュメント管理

### プロンプト 5-1: サイドバー

```
左サイドバーのドキュメント管理パネルを作成してください。

【レイアウト】
- 幅: 260px（開いた状態）、0px（閉じた状態）
- 開閉トグルボタン（ハンバーガーメニュー）はヘッダー左端に配置

【サイドバー構成】
上部:
- 「新規作成」ボタン（+ アイコン、幅 100%、accent カラー背景、白テキスト）
- 検索フィールド（虫眼鏡アイコン、プレースホルダー「ドキュメントを検索」）

ドキュメントリスト:
- 各アイテム: ドキュメントアイコン + タイトル + 最終更新日時
- hover で背景色変化
- 現在開いているドキュメントはアクセントカラーの左ボーダー
- 右クリックまたは「...」ボタンでコンテキストメニュー（名前変更、複製、削除）
- 日付でグルーピング（「今日」「昨日」「今週」「それ以前」）

下部:
- ユーザー情報エリア（アバター + メールアドレス）
- 設定ボタン（歯車アイコン）
- ダークモード切り替えトグル
```

---

## フェーズ 6: レスポンシブ対応

### プロンプト 6-1: モバイル対応

```
全画面をモバイルレスポンシブに対応させてください。

【ブレークポイント】
- デスクトップ: 1024px 以上（サイドバー常時表示可能）
- タブレット: 768px〜1023px（サイドバーはオーバーレイ）
- モバイル: 767px 以下

【モバイル時の変更点】
- サイドバー: 画面幅 100% のオーバーレイとしてスライドイン（左から）
- エディタツールバー: 横スクロール可能、またはグループごとに折りたたみ
- エディタ本体: 左右パディングを 16px に縮小
- フローティングツールバー: 画面下部に固定表示に切り替え
- ドキュメントタイトル: ヘッダー中央に truncate 表示
- タッチ操作に対応したボタンサイズ（最小 44x44px タッチターゲット）
```

---

## フェーズ 7: Supabase バックエンド接続

### プロンプト 7-1: 認証とデータ保存

```
Supabase バックエンドを接続してください。

【認証】
- メールアドレス + パスワードでのサインアップ/ログイン
- ログイン画面: シンプルなカード形式（中央配置）
  - 「pickles」ロゴ
  - メールアドレス入力
  - パスワード入力
  - 「ログイン」ボタン（primary）
  - 「アカウント作成」リンク
- ログイン状態はセッションで管理

【データベーステーブル: documents】
- id: uuid (primary key)
- user_id: uuid (references auth.users)
- title: text
- content: text (マークダウン文字列を保存)
- created_at: timestamptz
- updated_at: timestamptz
- is_deleted: boolean (ソフトデリート)

【自動保存】
- エディタの内容変更から 2 秒後に自動保存（デバウンス）
- 保存状態をヘッダーに表示（「保存済み ✓」「保存中...」「オフライン」）

【RLS ポリシー】
- ユーザーは自分の documents のみ CRUD 可能
```

---

## 補足: Figma Make 使用時の注意事項

### 入力順序
1. まず `guidelines/Guidelines.md` を設定
2. フェーズ 1 → 7 の順にプロンプトを入力
3. 各フェーズ完了後、プレビューで確認してから次へ進む
4. 問題があれば「Point and Edit」モードで微調整

### npm パッケージの追加
Figma Make のパッケージ管理画面から以下を追加:
- `@tiptap/react`
- `@tiptap/starter-kit`
- `@tiptap/extension-link`
- `@tiptap/extension-image`
- `@tiptap/extension-table`（および関連パッケージ）
- `@tiptap/extension-task-list`
- `@tiptap/extension-task-item`
- `@tiptap/extension-placeholder`
- `@tiptap/extension-code-block-lowlight`
- `tiptap-markdown`
- `lowlight`
- `@supabase/supabase-js`

### ファイルが重くなった場合
Figma Make は約 900 プロンプトを超えると性能が劣化します。その場合:
- 新しい Figma Make ファイルを作成
- 既存のコードをコピー
- Guidelines.md を再設定して続行

### コードのエクスポート
完成後、Figma Make から `.zip` でエクスポートし、pickles プロジェクトの `frontend/` ディレクトリに配置してください。

# WYSIWYG マークダウンエディタ設計書

## 1. 概要

本ドキュメントは、pickles プロジェクトの新規フロントエンドにおける WYSIWYG マークダウンエディタの技術設計と、Figma Make への UI 生成指示をまとめたものです。

## 2. 技術選定

### 2.1 推奨構成

| レイヤー | 技術 | 選定理由 |
|---|---|---|
| フレームワーク | React (Figma Make の出力形式) | Figma Make が React コードを生成するため |
| エディタ | **Tiptap** | 最大のエコシステム（35K stars）、ヘッドレスで UI 自由度が高い、ProseMirror ベースで安定 |
| マークダウンパース | **tiptap-markdown** 拡張 + **remark/unified** | Tiptap との統合が容易。remark でカスタム構文にも対応可能 |
| バックエンド | Supabase（既存） | pickles プロジェクトで既に使用中 |
| スタイリング | CSS Modules or Tailwind CSS | Figma Make が CSS を生成するため |

### 2.2 代替候補

マークダウンをより忠実に保持したい場合は **Milkdown**（remark/mdast ネイティブ）も有力な選択肢です。Notion 風のブロックエディタを最速で実現したい場合は **BlockNote** が適しています。

### 2.3 アーキテクチャ

```
[ユーザー入力 (WYSIWYG)]
        |
        v
[Tiptap Editor (ProseMirror Document Model)]
        |
        v  tiptap-markdown 拡張
[Markdown 文字列]
        |
        v  Supabase API
[Supabase PostgreSQL に保存]
        |
        v  remark-parse → mdast → remark-rehype → rehype-stringify
[HTML ビュー（閲覧時のレンダリング）]
```

**ポイント:**
- 保存形式はマークダウン文字列（ポータブルで軽量）
- 編集時は Tiptap の WYSIWYG で操作
- 閲覧時は remark/rehype パイプラインで HTML に変換してレンダリング
- 双方向変換: マークダウン ↔ ProseMirror ドキュメントモデル

## 3. 対応するマークダウン要素

| 要素 | マークダウン記法 | WYSIWYG 表示 |
|---|---|---|
| 見出し | `# H1` `## H2` `### H3` | フォントサイズ・太さで区別 |
| 太字 | `**bold**` | **太字表示** |
| 斜体 | `*italic*` | *斜体表示* |
| 取り消し線 | `~~strike~~` | ~~取り消し線~~ |
| リンク | `[text](url)` | クリック可能なリンク |
| 箇条書き | `- item` | ・ インデント付きリスト |
| 番号付きリスト | `1. item` | 番号付きリスト |
| チェックリスト | `- [ ] todo` | チェックボックス付きリスト |
| 引用 | `> quote` | 左ボーダー付き引用ブロック |
| コードブロック | `` ```code``` `` | シンタックスハイライト付きブロック |
| インラインコード | `` `code` `` | 背景色付きインラインコード |
| 水平線 | `---` | 区切り線 |
| 画像 | `![alt](url)` | 画像プレビュー |
| テーブル | GFM テーブル記法 | 構造化テーブル |

## 4. 必要な npm パッケージ

```json
{
  "dependencies": {
    "@tiptap/react": "^2.x",
    "@tiptap/starter-kit": "^2.x",
    "@tiptap/extension-link": "^2.x",
    "@tiptap/extension-image": "^2.x",
    "@tiptap/extension-table": "^2.x",
    "@tiptap/extension-table-row": "^2.x",
    "@tiptap/extension-table-cell": "^2.x",
    "@tiptap/extension-table-header": "^2.x",
    "@tiptap/extension-task-list": "^2.x",
    "@tiptap/extension-task-item": "^2.x",
    "@tiptap/extension-placeholder": "^2.x",
    "@tiptap/extension-code-block-lowlight": "^2.x",
    "tiptap-markdown": "^0.8.x",
    "lowlight": "^3.x",
    "remark-parse": "^11.x",
    "remark-rehype": "^11.x",
    "rehype-stringify": "^10.x",
    "unified": "^11.x",
    "remark-gfm": "^4.x",
    "@supabase/supabase-js": "^2.x"
  }
}
```

# WYSIWYG マークダウンエディタ — 技術設計書

## 1. 概要

pickles フロントエンドにおける WYSIWYG エディタの技術構成とデータ保存設計。
ユーザーがリッチテキスト形式でジャーナルを入力し、構造化された JSON として保存する。

---

## 2. 技術スタック

### 2.1 確定構成

| レイヤー | 技術 | 選定理由 |
|---|---|---|
| フレームワーク | **React + TypeScript** | Figma Make の出力形式。型安全性の確保 |
| エディタ | **Tiptap v2** (ProseMirror) | 最大エコシステム（35K stars）、ヘッドレスで UI 自由度が高い |
| Markdown 入出力 | **tiptap-markdown** 拡張 | Markdown ↔ Tiptap JSON の双方向変換 |
| Markdown 閲覧レンダリング | **remark / rehype** (unified) | AST ベースで GFM 拡張対応。閲覧専用ビューの HTML 生成に使用 |
| バックエンド | **Supabase**（既存） | 既に pickles で使用中。auth / DB / Storage 統合済み |
| スタイリング | **Tailwind CSS** or CSS Modules | Figma Make 出力と親和性が高い |

### 2.2 主要 npm パッケージ

```
# エディタ本体
@tiptap/react
@tiptap/starter-kit
@tiptap/extension-link
@tiptap/extension-image
@tiptap/extension-table (+table-row, table-cell, table-header)
@tiptap/extension-task-list
@tiptap/extension-task-item
@tiptap/extension-placeholder
@tiptap/extension-code-block-lowlight
tiptap-markdown
lowlight

# 閲覧レンダリング（エディタ外でのMarkdown→HTML変換）
unified
remark-parse
remark-gfm
remark-rehype
rehype-stringify

# バックエンド
@supabase/supabase-js

# ユーティリティ
uuid                    # ブロックID生成用
```

---

## 3. データフロー

### 3.1 全体像

```
┌─────────────────────────────────────────────────┐
│  編集時                                          │
│                                                  │
│  ユーザー入力 (WYSIWYG)                           │
│       │                                          │
│       v                                          │
│  Tiptap Editor                                   │
│  (ProseMirror Document Model)                    │
│       │                                          │
│       ├──→ editor.getJSON()     → content_json   │  ← 正データ（JSONB）
│       ├──→ editor.getText()     → content_search │  ← 検索用プレーンテキスト
│       └──→ storage.markdown     → (必要時のみ)    │  ← エクスポート用
│               .getMarkdown()                     │
│                                                  │
│       │           2秒 debounce                   │
│       v                                          │
│  Supabase API (upsert)                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  閲覧時                                          │
│                                                  │
│  content_json (JSONB)                            │
│       │                                          │
│       ├──→ Tiptap: editor.commands.setContent()  │  ← 再編集
│       │    (JSON をそのまま渡す)                    │
│       │                                          │
│       └──→ tiptap-markdown で Markdown 文字列化    │  ← 閲覧ビュー
│               │                                  │
│               v                                  │
│            remark-parse → rehype → HTML           │
└─────────────────────────────────────────────────┘
```

### 3.2 なぜ JSONB が正データか

| 観点 | Markdown 文字列保存 | JSONB 保存（採用） |
|---|---|---|
| データ忠実性 | JSON→MD 変換で情報欠落（カスタム属性、ブロックID） | Tiptap 内部表現そのものなので完全保持 |
| 再編集 | MD→JSON のパース（拡張必須、不可逆リスク） | `setContent(json)` で無変換ロード |
| ブロック操作 | 構造情報なし | ノード単位の参照・並替・AI 分析が可能 |
| 検索 | 全文検索しやすい | 直接は非効率 → `content_search` で解決 |
| エクスポート | そのまま | `tiptap-markdown` で随時変換可能 |

**結論**: JSONB を Single Source of Truth とし、検索用にプレーンテキストを別途保持する。

---

## 4. データベース設計

### 4.1 新規テーブル: `journal_entries`

既存テーブル（`users`, `analysis_runs`, `deliveries`）はバッチ分析パイプライン用。
`journal_entries` はフロントエンドからの直接入力を扱う新テーブル。

```sql
CREATE TABLE public.journal_entries (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- コンテンツ
    title          TEXT,
    content_json   JSONB NOT NULL,             -- Tiptap JSON (正データ)
    content_search TEXT,                        -- 検索用プレーンテキスト (トリガーで自動生成)

    -- メタデータ
    mood           TEXT,                        -- 気分タグ (将来のAI分析用)
    tags           TEXT[],                      -- ユーザー定義タグ

    -- バージョニング
    schema_version INTEGER NOT NULL DEFAULT 1,  -- JSONB スキーマ変更時のマイグレーション用

    -- タイムスタンプ
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ソフトデリート
    is_deleted     BOOLEAN NOT NULL DEFAULT FALSE
);
```

### 4.2 各カラムの役割

| カラム | 型 | 役割 | 更新タイミング |
|---|---|---|---|
| `content_json` | JSONB | エディタの正データ。Tiptap の `editor.getJSON()` 出力をそのまま保存 | 自動保存（2秒 debounce） |
| `content_search` | TEXT | 全文検索用プレーンテキスト。`content_json` から抽出 | DB トリガーで自動生成 |
| `title` | TEXT | ドキュメントタイトル。null 可（無題ドキュメント） | ユーザー編集時 |
| `mood` | TEXT | 気分・感情タグ。将来のAI分析・統計用 | ユーザー入力 or AI 推定 |
| `tags` | TEXT[] | 自由入力タグ。フィルタリング・分類用 | ユーザー入力 |
| `schema_version` | INTEGER | `content_json` のスキーマバージョン。破壊的変更時にマイグレーション判定に使用 | スキーマ更新時 |
| `is_deleted` | BOOLEAN | ソフトデリート。完全削除せず復元可能に | ユーザー削除操作時 |

### 4.3 `content_json` の構造（Tiptap JSON フォーマット）

```json
{
  "type": "doc",
  "content": [
    {
      "type": "heading",
      "attrs": { "level": 1, "blockId": "a1b2c3d4" },
      "content": [
        { "type": "text", "text": "今日の振り返り" }
      ]
    },
    {
      "type": "paragraph",
      "attrs": { "blockId": "e5f6g7h8" },
      "content": [
        { "type": "text", "text": "今日は" },
        {
          "type": "text",
          "marks": [{ "type": "bold" }],
          "text": "とても良い天気"
        },
        { "type": "text", "text": "だった。" }
      ]
    },
    {
      "type": "taskList",
      "content": [
        {
          "type": "taskItem",
          "attrs": { "checked": true },
          "content": [
            { "type": "paragraph", "content": [
              { "type": "text", "text": "メールの返信" }
            ]}
          ]
        }
      ]
    }
  ]
}
```

### 4.4 インデックス

```sql
-- 全文検索 ('simple' 辞書: 日本語対応。形態素解析なし、トークン単純分割)
-- 注意: 'english' では日本語が検索不可
CREATE INDEX idx_journal_entries_search
    ON public.journal_entries
    USING GIN (to_tsvector('simple', content_search));

-- ユーザー別 + 日時順（一覧取得の主クエリ）
CREATE INDEX idx_journal_entries_user_date
    ON public.journal_entries (user_id, created_at DESC)
    WHERE is_deleted = FALSE;

-- タグ検索
CREATE INDEX idx_journal_entries_tags
    ON public.journal_entries USING GIN (tags);
```

### 4.5 `content_search` 自動更新トリガー

クライアント側（`editor.getText()`）だけでなく、サーバー側でも `content_json` から自動生成する。
API 経由の更新（AI による書き換え等）でもテキスト抽出が漏れない。

```sql
-- JSONB から全テキストノードを再帰的に抽出する関数
CREATE OR REPLACE FUNCTION extract_text_from_tiptap_json(content JSONB)
RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$
    WITH RECURSIVE nodes AS (
        -- ルート要素
        SELECT content AS node
        UNION ALL
        -- content 配列内の子要素を再帰展開
        SELECT elem
        FROM nodes, jsonb_array_elements(node -> 'content') AS elem
        WHERE node ? 'content' AND jsonb_typeof(node -> 'content') = 'array'
    )
    SELECT COALESCE(string_agg(node ->> 'text', ' '), '')
    FROM nodes
    WHERE node ? 'text';
$$;

-- INSERT / UPDATE 時に content_search を自動更新するトリガー
CREATE OR REPLACE FUNCTION update_journal_content_search()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    NEW.content_search := extract_text_from_tiptap_json(NEW.content_json);
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_journal_content_search
    BEFORE INSERT OR UPDATE OF content_json
    ON public.journal_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_journal_content_search();
```

### 4.6 RLS ポリシー

```sql
ALTER TABLE public.journal_entries ENABLE ROW LEVEL SECURITY;

-- ユーザーは自分のエントリのみ操作可能
CREATE POLICY "Users can CRUD own entries"
    ON public.journal_entries
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);
```

### 4.7 既存テーブルとの関係

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────┐
│ auth.users   │     │ public.users       │     │ analysis_runs│
│ (Supabase    │     │ (Google Sheets同期) │────→│ (バッチ分析)  │
│  Auth)       │     │                    │     │              │
│              │     └────────────────────┘     └──────────────┘
│              │                                       │
│              │                                       v
│              │                                ┌──────────────┐
│              │                                │ deliveries   │
│              │                                │ (配信履歴)    │
│              │                                └──────────────┘
│              │
│              │     ┌────────────────────┐
│              │────→│ journal_entries     │  ← 新規テーブル
│              │     │ (フロントエンド入力) │
└──────────────┘     └────────────────────┘
```

**ポイント**:
- `journal_entries.user_id` は `auth.users(id)` を参照（Supabase Auth）
- 既存の `public.users` はバッチパイプライン用（Google Sheets 同期）
- 将来的に `journal_entries` を発酵システム（`fermentation_nodes`）の原料として使用可能

---

## 5. ブロック ID の実装

各ブロックに一意 ID を付与し、AI 分析時のブロック参照や並べ替えに使う。

**注意**: `@tiptap-pro/extension-unique-id` は有料（Tiptap Pro）。以下のカスタム拡張で代替する。

```typescript
import { Extension } from '@tiptap/core';
import { Plugin } from '@tiptap/pm/state';
import { v4 as uuidv4 } from 'uuid';

const BlockId = Extension.create({
  name: 'blockId',

  addGlobalAttributes() {
    return [{
      types: ['heading', 'paragraph', 'codeBlock', 'blockquote',
              'bulletList', 'orderedList', 'taskList', 'table'],
      attributes: {
        blockId: {
          default: null,
          rendered: false,
          parseHTML: (el) => el.getAttribute('data-block-id'),
          renderHTML: (attrs) =>
            attrs.blockId ? { 'data-block-id': attrs.blockId } : {},
        },
      },
    }];
  },

  addProseMirrorPlugins() {
    return [new Plugin({
      appendTransaction: (_, __, newState) => {
        const tr = newState.tr;
        let modified = false;
        newState.doc.descendants((node, pos) => {
          if (node.isBlock && !node.attrs.blockId
              && node.type.spec.attrs?.blockId) {
            tr.setNodeMarkup(pos, undefined, {
              ...node.attrs,
              blockId: uuidv4(),
            });
            modified = true;
          }
        });
        return modified ? tr : null;
      },
    })];
  },
});

export default BlockId;
```

---

## 6. エディタ初期化コード

```typescript
import { useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from 'tiptap-markdown';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import Table from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import Placeholder from '@tiptap/extension-placeholder';
import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight';
import { common, createLowlight } from 'lowlight';
import BlockId from './extensions/block-id';

const lowlight = createLowlight(common);

function useJournalEditor(initialContent?: object) {
  return useEditor({
    extensions: [
      StarterKit.configure({
        codeBlock: false,  // CodeBlockLowlight で上書き
      }),
      Markdown,            // tiptap-markdown: MD 入出力を可能にする
      BlockId,             // カスタム拡張: 各ブロックに UUID 付与
      Link.configure({ openOnClick: false }),
      Image,
      TaskList,
      TaskItem.configure({ nested: true }),
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
      CodeBlockLowlight.configure({ lowlight }),
      Placeholder.configure({
        placeholder: 'ここに書き始めましょう...',
      }),
    ],

    content: initialContent ?? '',

    onUpdate: ({ editor }) => {
      // 自動保存に渡すデータ
      const json = editor.getJSON();          // → content_json (JSONB)
      const text = editor.getText();          // → content_search (TEXT) ※クライアント側フォールバック
      debouncedSave(json, text);
    },
  });
}
```

---

## 7. 自動保存の実装方針

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// 2秒 debounce で自動保存
const debouncedSave = debounce(
  async (json: object, text: string, entryId: string) => {
    const { error } = await supabase
      .from('journal_entries')
      .update({
        content_json: json,
        // content_search は DB トリガーで自動生成されるが、
        // フォールバックとしてクライアント側からも送る
        content_search: text,
      })
      .eq('id', entryId);

    if (error) console.error('Save failed:', error);
  },
  2000
);
```

---

## 8. 将来の検索拡張

### 8.1 現時点: `tsvector` + `'simple'` 辞書

日本語に特化した形態素解析は行わないが、基本的な全文検索は可能。

```sql
-- 検索クエリ例
SELECT id, title, content_search
FROM journal_entries
WHERE user_id = $1
  AND is_deleted = FALSE
  AND to_tsvector('simple', content_search) @@ plainto_tsquery('simple', $2)
ORDER BY created_at DESC;
```

### 8.2 将来候補

| 手段 | 特徴 | 用途 |
|---|---|---|
| `pg_bigm` (2-gram) | 日本語部分一致に強い。Supabase での利用可否要確認 | 日本語全文検索の精度向上 |
| `pgvector` + Embedding | ベクトル類似検索。Supabase で利用可能 | 意味的に近いエントリの発見。発酵システムとの統合 |
| 外部検索エンジン (Meilisearch 等) | 日本語トークナイザ内蔵 | 大規模データでの高速検索 |

`pgvector` は発酵システム（`FERMENTATION_DESIGN.md` の `embedding vector(1536)` ）と自然に統合できるため、最有力候補。

---

## 9. 対応するマークダウン要素

| 要素 | マークダウン記法 | Tiptap ノードタイプ |
|---|---|---|
| 見出し | `# H1` `## H2` `### H3` | `heading` (attrs.level) |
| 太字 | `**bold**` | mark: `bold` |
| 斜体 | `*italic*` | mark: `italic` |
| 取り消し線 | `~~strike~~` | mark: `strike` |
| リンク | `[text](url)` | mark: `link` |
| 箇条書き | `- item` | `bulletList` > `listItem` |
| 番号付き | `1. item` | `orderedList` > `listItem` |
| チェックリスト | `- [ ] todo` | `taskList` > `taskItem` |
| 引用 | `> quote` | `blockquote` |
| コードブロック | `` ```lang `` | `codeBlock` (attrs.language) |
| インラインコード | `` `code` `` | mark: `code` |
| 水平線 | `---` | `horizontalRule` |
| 画像 | `![alt](url)` | `image` (attrs.src, alt) |
| テーブル | GFM テーブル | `table` > `tableRow` > `tableCell` |

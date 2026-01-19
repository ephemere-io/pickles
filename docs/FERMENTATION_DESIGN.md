# Pickles 多層発酵システム 設計ドキュメント

> 日記データから「思いがけない接続」を発見し、時間による変容を層として蓄積していく発酵体験の設計

---

## 🎯 目的

### 本質的な体験目標

1. **思いがけない接続の発見**
   - 書いた本人も気づいていなかったリンクをAIが見つけて提示
   - 「異なることが繋がっている」驚き
   - 20年前の記録と今が突然リンクする体験

2. **可能性の提示に留める**（センスメイキングを奪わない）
   - 要約や解釈をAIに委ねない
   - 「こういうテーマだったのかも」という問いかけ
   - ユーザー自身が意味を見出す余地を残す

3. **馴染みのバーテンダー/美容師体験**
   - 見守ってくれている存在
   - 自分のことを知ってくれている安心感
   - また通いたくなる関係性

4. **複雑化による創発**（発酵のメタファー）
   - シンプルなものが複雑になって返ってくる
   - 接種した時に想像力が膨らむ
   - 謎でいい、分かりやすくなくていい

5. **時間による変性のレイヤー構造**（新規）
   - 週、月、四半期、年という時間単位での発酵
   - 各レイヤーが独自のベクトル空間を持つ
   - 下層のデータを原料として上層が生成される

### 避けるべきアンチパターン

- ❌ AIが要約して「あなたはこうでした」と断定
- ❌ センスメイキングをAIに委ねてしまう
- ❌ 分かりやすくしすぎて想像の余地がなくなる
- ❌ 単なる検索機能（キーワードマッチ）
- ❌ 単なる要約・集約（発酵ではない）

---

## 🧬 発酵レイヤーの概念

### メタファー：蔵付き酵母の階層構造

```
[日記層] 生の記録（毎日）
    ↓ 週次発酵（独自プロンプト）
[週次層] 7日間の変性（毎週月曜）
    ↓ 月次発酵（独自プロンプト）
[月次層] 4週間の熟成（毎月1日）
    ↓ 季節発酵（独自プロンプト）
[季節層] 3ヶ月の深化（四半期初日）
    ↓ 年次発酵（独自プロンプト）
[年次層] 12ヶ月の結晶（毎年1月1日）
```

### レイヤーの特性

各レイヤーは：
- **独自の発酵プロンプト**を持つ（システムプロンプト + 強調点）
- **下層のベクトルデータを原料**として変性
- **新たなベクトル空間**に結晶化
- **検索対象として混在**可能（重み付け検索）

| レイヤー | 深度 | 原料 | 発酵頻度 | 強調点 |
|---------|------|------|---------|--------|
| 日記 | 0 | 直接入力 | 毎日 | - |
| 週次 | 1 | 7日分のジャーナル | 毎週月曜 | 微細な変化の兆し |
| 月次 | 2 | 4週分の週次ノード | 毎月1日 | 通底するテーマ |
| 季節 | 3 | 3月分の月次ノード | 四半期初日 | パターンの変容 |
| 年次 | 4 | 4季節分のノード | 毎年1月1日 | 結晶化された問い |

---

## 📊 データベース設計（多層対応）

### ユーザー管理の統合

#### 現状の課題

現在のPicklesは`read_spreadsheet_and_execute.py`でGoogle Sheetsからユーザー情報を読み込んで実行していますが、この方式には以下の問題があります：

```python
# 現在のユーザーデータ構造（read_spreadsheet_and_execute.py）
user_data = {
    'email_to': row[0].strip(),           # A列: メールアドレス
    'notion_api_key': row[1].strip(),     # B列: Notion API Key
    'google_docs_url': row[2].strip(),    # C列: Google Docs URL
    'user_name': row[3].strip(),          # D列: ユーザー名
    'language': row[4].strip()            # E列: 言語設定
}
```

**問題点**:
- ❌ 永続的なユーザーID（UUID）がない
- ❌ Supabaseの`journals`や`fermentation_nodes`に紐付けるIDが存在しない
- ❌ スプレッドシートの行番号は不安定（削除・並び替えで変わる）
- ❌ ユーザーの追加・削除履歴が追跡できない

#### 解決策：Supabase usersテーブルの導入

発酵システムでは、すべてのデータがユーザーUUIDに紐付く必要があります。

### 統合テーブル構造

```sql
-- pgvector拡張の有効化
create extension if not exists vector;

-- 0. ユーザー管理テーブル（新規追加）
create table public.users (
  id uuid primary key default gen_random_uuid(),

  -- 基本情報
  email text unique not null,
  user_name text not null,
  language text not null default 'japanese',

  -- データソース設定
  notion_api_key text,
  google_docs_url text,
  source_type text,  -- 'notion' | 'gdocs' | 'both'

  -- ステータス
  is_active boolean default true,
  last_analysis_at timestamptz,

  -- メタデータ
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  meta jsonb default '{}'::jsonb,

  -- 制約：少なくとも一つのデータソースが必要
  constraint users_source_check check (
    notion_api_key is not null or google_docs_url is not null
  )
);

-- ユーザー情報の自動更新
create or replace function update_users_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger users_updated_at_trigger
  before update on users
  for each row
  execute function update_users_updated_at();

-- RLS（Row Level Security）設定
alter table users enable row level security;

-- ポリシー：ユーザーは自分のデータのみ閲覧可能
create policy "Users can view their own data"
  on users for select
  using (id = auth.uid());

-- インデックス
create index users_email_idx on users(email);
create index users_active_idx on users(is_active) where is_active = true;

-- 1. 生ジャーナル（原文＋埋め込み）
create table public.journals (
  id bigserial primary key,
  user_id uuid not null,
  content text not null,
  embedding vector(1536),
  created_at timestamptz not null,
  source_type text not null,  -- 'notion' | 'gdocs'
  source_id text,              -- Notion page ID等
  meta jsonb default '{}'::jsonb,

  constraint journals_user_created_idx unique (user_id, created_at)
);

-- 2. 発酵ノード（多層対応）
create table public.fermentation_nodes (
  id bigserial primary key,
  user_id uuid not null,

  -- レイヤー情報
  layer_type text not null,  -- 'weekly' | 'monthly' | 'quarterly' | 'yearly'
  layer_depth int not null,  -- 1=週次, 2=月次, 3=季節, 4=年次

  -- 期間情報
  period_start date not null,
  period_end date not null,

  -- 発酵結果
  title text,
  fermented_content text not null,  -- AI生成の変性テキスト
  embedding vector(1536),

  -- 発酵のメタデータ
  fermentation_recipe_id text,     -- 使用したプロンプトID
  source_count int,                -- 元データ件数
  fermentation_metrics jsonb,      -- {"diversity": 0.7, "emergence": 0.8}

  created_at timestamptz default now(),
  meta jsonb default '{}'::jsonb
);

-- 3. 発酵の系譜（親子関係）
create table public.fermentation_lineage (
  id bigserial primary key,

  -- 発酵の関係性
  child_node_id bigint references fermentation_nodes(id) on delete cascade,
  parent_node_id bigint references fermentation_nodes(id),
  parent_journal_id bigint references journals(id),

  -- 寄与度（どのくらい影響したか）
  contribution_weight float default 1.0,

  -- 関係のタイプ
  lineage_type text not null,  -- 'direct' | 'resonance' | 'mutation'

  created_at timestamptz default now()
);

-- 4. 発酵プロンプト管理（レシピ）
create table public.fermentation_recipes (
  id text primary key,  -- 'weekly_domi_v1', 'monthly_synthesis_v2'
  layer_type text not null,
  analysis_type text,  -- 'domi' | 'aga' | null（汎用）

  system_prompt text not null,
  user_prompt_template text not null,

  -- レシピのメタ情報
  temperature float default 0.7,
  emphasis text,  -- '変化の兆し' '通底するテーマ' 'パターンの変容'

  created_at timestamptz default now(),
  version int default 1
);

-- インデックス（データが増えたら作成）
create index journals_embedding_idx on journals
  using ivfflat (embedding vector_cosine_ops) with (lists=100);

create index fermentation_nodes_embedding_idx on fermentation_nodes
  using ivfflat (embedding vector_cosine_ops) with (lists=100);

create index journals_user_idx on journals(user_id);
create index fermentation_nodes_layer_idx on fermentation_nodes(user_id, layer_type, period_start);
create index fermentation_lineage_child_idx on fermentation_lineage(child_node_id);
create index fermentation_lineage_parent_idx on fermentation_lineage(parent_node_id);
```

### 設計の理由

**なぜ content と embedding を両方保存？**
- `content`: **人が読む**原文／LLMに引用で渡す
- `embedding`: **機械が似ている文章を探す**ための座標
- どちらか一方だけだと「見せられない／探せない」片手落ちになる

**なぜ fermentation_nodes は layer_depth を持つ？**
- 検索時に「どの層から来たか」を判別するため
- レポートで「週次発酵」「月次熟成」などのラベル表示
- レイヤー別の重み付け検索に利用

**なぜ fermentation_lineage が必要？**
- 発酵の系譜をたどれる（どのジャーナルから生まれたか）
- 「この月次ノードは、どの週次ノードから作られたか」を追跡
- Phase 2以降で発酵プロセスの可視化に利用

---

## 🔍 RPC関数（多層検索）

```sql
-- journals から類似検索
create or replace function search_similar_journals(
  p_user_id uuid,
  p_query_embedding vector(1536),
  p_limit int default 5,
  p_exclude_recent_days int default 30
)
returns table (
  id bigint,
  content text,
  created_at timestamptz,
  similarity float
) as $$
  select
    j.id,
    j.content,
    j.created_at,
    1 - (j.embedding <=> p_query_embedding) as similarity
  from journals j
  where j.user_id = p_user_id
    and j.created_at < now() - interval '1 day' * p_exclude_recent_days
  order by j.embedding <=> p_query_embedding
  limit p_limit;
$$ language sql stable;

-- fermentation_nodes から類似検索（レイヤー指定可能）
create or replace function search_similar_fermentation_nodes(
  p_user_id uuid,
  p_query_embedding vector(1536),
  p_layer_type text default null,  -- null = 全レイヤー
  p_limit int default 5
)
returns table (
  id bigint,
  layer_type text,
  layer_depth int,
  fermented_content text,
  period_start date,
  period_end date,
  similarity float
) as $$
  select
    n.id,
    n.layer_type,
    n.layer_depth,
    n.fermented_content,
    n.period_start,
    n.period_end,
    1 - (n.embedding <=> p_query_embedding) as similarity
  from fermentation_nodes n
  where n.user_id = p_user_id
    and (p_layer_type is null or n.layer_type = p_layer_type)
  order by n.embedding <=> p_query_embedding
  limit p_limit;
$$ language sql stable;
```

**RPC関数の利点**:
- Supabase Python SDKから `supabase.rpc("関数名", 引数)` で直接呼べる
- クライアント側で複雑なSQLを書かずに済む
- pgvectorの最適化された検索を利用

---

## 🏗️ アーキテクチャ設計

### 拡張モジュール構成

```
pickles/
├── persistence/              # 新規：永続化層
│   ├── __init__.py
│   ├── supabase_client.py   # Supabase接続管理
│   ├── journal_store.py     # journals テーブル操作
│   └── fermentation_store.py # fermentation_nodes操作
├── fermentation/             # 新規：発酵機能
│   ├── __init__.py
│   ├── embedder.py          # OpenAI Embeddings API
│   ├── link_finder.py       # 意味的接続の発見
│   ├── layered_search.py    # 多層ベクトル検索
│   ├── batch_fermenter.py   # バッチ発酵処理
│   └── serendipity.py       # 偶然性の演出
├── .github/workflows/
│   └── fermentation_batch.yml  # 定期発酵バッチ
```

### データフロー（多層対応版）

```
[Input] Notion/Google Docs
  ↓
[Persistence] journal_store.save_journals()
  ├─ content保存
  └─ embedding生成・保存
  ↓
[Throughput] DocumentAnalyzer.analyze()
  ├─ 既存の週次分析
  └─ 新規: layered_search.search_across_layers()
      ├─ 生ジャーナルから検索（50%）
      ├─ 週次ノードから検索（30%）
      ├─ 月次ノードから検索（15%）
      └─ 季節ノードから検索（5%）
  ↓
[Persistence] fermentation_store.save_node()
  ├─ 週次分析結果を週次ノードとして保存
  ├─ embedding生成
  └─ fermentation_lineage記録
  ↓
[Output] ReportDelivery.deliver()
  ├─ 既存: statistics + insights
  └─ 新規: 多層接続セクション
      ├─ "生の記録との響き合い"
      ├─ "週次発酵との共鳴"
      ├─ "月次熟成との対話"
      └─ "季節変容からの呼びかけ"

---

【定期バッチ】GitHub Actions / cron
  ↓
[Fermentation Batch] batch_fermenter.ferment_layer()
  ├─ 週次発酵: 毎週月曜7:00
  │   └─ 7日分のjournalsから週次ノード生成
  ├─ 月次発酵: 毎月1日8:00
  │   └─ 4週分の週次ノードから月次ノード生成
  ├─ 季節発酵: 四半期初日9:00
  │   └─ 3月分の月次ノードから季節ノード生成
  └─ 年次発酵: 毎年1月1日10:00
      └─ 4季節分のノードから年次ノード生成
```

---

## 🔄 発酵バッチの仕組み

### バッチ実行スケジュール

```yaml
# .github/workflows/fermentation_batch.yml
name: Fermentation Batch

on:
  schedule:
    - cron: "0 7 * * 1"        # 週次: 毎週月曜7:00
    - cron: "0 8 1 * *"        # 月次: 毎月1日8:00
    - cron: "0 9 1 1,4,7,10 *" # 季節: 四半期初日9:00
    - cron: "0 10 1 1 *"       # 年次: 毎年1月1日10:00
  workflow_dispatch:           # 手動実行も可能
    inputs:
      layer_type:
        description: 'Layer to ferment'
        required: true
        type: choice
        options:
          - weekly
          - monthly
          - quarterly
          - yearly
```

### 発酵バッチの実装

```python
# fermentation/batch_fermenter.py

from datetime import date, timedelta
from typing import List, Dict, Any
from .embedder import Embedder
from persistence.fermentation_store import FermentationStore

class LayeredFermenter:
    """多層発酵システム"""

    LAYER_CONFIG = {
        'weekly': {
            'depth': 1,
            'source_days': 7,
            'parent_layer': 'journals',
            'prompt_emphasis': '微細な変化の兆し',
            'recipe_id': 'weekly_domi_v1'
        },
        'monthly': {
            'depth': 2,
            'source_count': 4,  # 4週分
            'parent_layer': 'weekly',
            'prompt_emphasis': '通底するテーマ',
            'recipe_id': 'monthly_synthesis_v1'
        },
        'quarterly': {
            'depth': 3,
            'source_count': 3,  # 3ヶ月分
            'parent_layer': 'monthly',
            'prompt_emphasis': 'パターンの変容',
            'recipe_id': 'quarterly_mutation_v1'
        },
        'yearly': {
            'depth': 4,
            'source_count': 4,  # 4四半期分
            'parent_layer': 'quarterly',
            'prompt_emphasis': '結晶化された問い',
            'recipe_id': 'yearly_crystallization_v1'
        }
    }

    def __init__(self):
        self.embedder = Embedder()
        self.store = FermentationStore()

    def ferment_layer(self, user_id: str, layer_type: str,
                     period_start: date, period_end: date) -> Dict[str, Any]:
        """指定レイヤーの発酵を実行"""

        config = self.LAYER_CONFIG[layer_type]

        # 1. 原料の収集（下層のノードまたはジャーナル）
        source_materials = self._gather_source_materials(
            user_id, config['parent_layer'], period_start, period_end
        )

        if not source_materials:
            return None

        # 2. 発酵プロンプトの取得
        recipe = self.store.get_recipe(config['recipe_id'])

        # 3. LLMで変性テキスト生成
        fermented_text = self._call_fermentation_llm(
            source_materials, recipe, config['prompt_emphasis']
        )

        # 4. 新たなベクトル生成
        embedding = self.embedder.embed_text(fermented_text)

        # 5. 発酵メトリクスの計算
        metrics = self._calculate_fermentation_metrics(
            source_materials, fermented_text, embedding
        )

        # 6. ノード保存
        node = self.store.save_fermentation_node(
            user_id=user_id,
            layer_type=layer_type,
            layer_depth=config['depth'],
            period_start=period_start,
            period_end=period_end,
            fermented_content=fermented_text,
            embedding=embedding,
            recipe_id=recipe['id'],
            metrics=metrics
        )

        # 7. 系譜の記録
        self._record_lineage(node['id'], source_materials)

        return node

    def _call_fermentation_llm(self, sources, recipe, emphasis):
        """発酵専用のLLM呼び出し"""

        # 原料テキストの結合
        source_texts = [s['content'] for s in sources]

        prompt = recipe['user_prompt_template'].format(
            emphasis=emphasis,
            period=f"{sources[0]['period_start']} 〜 {sources[-1]['period_end']}",
            source_count=len(sources),
            sources='\n---\n'.join(source_texts)
        )

        response = self.openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": recipe['system_prompt']},
                {"role": "user", "content": prompt}
            ],
            temperature=recipe['temperature']
        )

        return response.choices[0].message.content

    def _calculate_fermentation_metrics(self, sources, fermented, embedding):
        """発酵の質を測定"""

        # 元のベクトル群
        source_embeddings = [s['embedding'] for s in sources]

        # 多様性: 元データ間の平均距離
        diversity = self._calculate_diversity(source_embeddings)

        # 創発性: 元データと発酵後の距離
        emergence = self._calculate_emergence(source_embeddings, embedding)

        # 密度: 情報の凝縮度
        density = len(fermented) / sum(len(s['content']) for s in sources)

        return {
            'diversity': round(diversity, 3),
            'emergence': round(emergence, 3),
            'density': round(density, 3),
            'source_count': len(sources)
        }
```

---

## 🎨 発酵プロンプトの設計

### レイヤー別のプロンプト例

```sql
-- 週次発酵プロンプト（DOMI用）
insert into fermentation_recipes (id, layer_type, analysis_type, system_prompt, user_prompt_template, emphasis) values (
  'weekly_domi_v1',
  'weekly',
  'domi',
  '
あなたは発酵の触媒です。
7日間の記録から「微細な変化の兆し」を抽出してください。
要約ではなく、変性です。元の言葉を新しい文脈で結晶化させてください。
断定は避け、可能性として提示してください。
  ',
  '
【発酵原料】
期間: {period}
記録数: {source_count}件

{sources}

【発酵指示】
この7日間で「{emphasis}」を感じ取り、以下の形式で変性してください：

1. 浮上した言葉（3-5個のキーワード）
2. 響き合う断片（2-3個の引用と新しい繋がり）
3. 問いの種（1-2個の開かれた問い）

元の言葉を尊重しながらも、新しい意味の可能性を開いてください。
  ',
  '微細な変化の兆し'
);

-- 月次発酵プロンプト
insert into fermentation_recipes (id, layer_type, system_prompt, user_prompt_template, emphasis, temperature) values (
  'monthly_synthesis_v1',
  'monthly',
  '
あなたは時間の発酵を見届ける者です。
4週間の変性を重ね、「通底するテーマ」を浮かび上がらせてください。
各週の断片を対話させ、新しい物語の可能性を紡いでください。
  ',
  '
【発酵原料】4週間の変性記録
{sources}

【発酵指示】
これらの週次変性を「{emphasis}」の視点で再発酵させてください：

1. 繰り返し現れるパターン
2. 週をまたいで響き合う言葉
3. 見えなかった接続
4. 熟成の問い

1ヶ月という時間が生み出した変容を、謎を残しながら提示してください。
  ',
  '通底するテーマ',
  0.8
);

-- 四半期発酵プロンプト
insert into fermentation_recipes (id, layer_type, system_prompt, user_prompt_template, emphasis, temperature) values (
  'quarterly_mutation_v1',
  'quarterly',
  '
あなたは季節の変容を見つめる者です。
3ヶ月の熟成を経て「パターンの変容」を結晶化してください。
始まりと終わりの違いを、断定せずに浮かび上がらせてください。
  ',
  '
【発酵原料】3ヶ月の熟成記録
{sources}

【発酵指示】
この四半期で起きた「{emphasis}」を感じ取ってください：

1. 始まりと終わりの違い
2. 変化の軌跡（予想外だったもの）
3. 持続したもの、消えたもの
4. 季節が残した問い

3ヶ月という季節が、あなたの中で何を変容させたのか。
可能性として、そっと提示してください。
  ',
  'パターンの変容',
  0.9
);

-- 年次発酵プロンプト
insert into fermentation_recipes (id, layer_type, system_prompt, user_prompt_template, emphasis, temperature) values (
  'yearly_crystallization_v1',
  'yearly',
  '
あなたは1年という時間の結晶化を担う者です。
4つの季節を経た変容から「結晶化された問い」を抽出してください。
解釈ではなく、新しい問いの生成です。
  ',
  '
【発酵原料】1年間の四季の記録
{sources}

【発酵指示】
この1年が熟成させた「{emphasis}」を結晶化してください：

1. 年を通して変わらなかったもの
2. 予想外の変容
3. まだ名前のないテーマ
4. 来年への問い

1年という時間が生み出した、あなただけの発酵結果を。
答えではなく、新しい問いとして。
  ',
  '結晶化された問い',
  1.0
);
```

---

## 🔍 多層検索の実装

```python
# fermentation/layered_search.py

class LayeredSearch:
    """多層ベクトル検索"""

    def search_across_layers(self, user_id: str, query: str,
                            layer_weights: dict = None):
        """
        全レイヤーから検索し、重み付けで混合

        Args:
            layer_weights: {'journals': 0.5, 'weekly': 0.3, 'monthly': 0.15, 'quarterly': 0.05}
        """

        if layer_weights is None:
            layer_weights = {
                'journals': 0.5,   # 生の記録: 50%
                'weekly': 0.3,     # 週次: 30%
                'monthly': 0.15,   # 月次: 15%
                'quarterly': 0.05  # 季節: 5%
            }

        query_embedding = self.embedder.embed_text(query)
        results = []

        # 1. 生ジャーナルから検索
        if 'journals' in layer_weights:
            journal_results = self._search_journals(
                user_id, query_embedding,
                top_k=int(10 * layer_weights['journals'])
            )
            results.extend(self._tag_results(journal_results, 'journals', 0))

        # 2-5. 各発酵レイヤーから検索
        for layer_type in ['weekly', 'monthly', 'quarterly', 'yearly']:
            if layer_type in layer_weights:
                layer_results = self._search_fermentation_nodes(
                    user_id, query_embedding, layer_type,
                    top_k=int(10 * layer_weights[layer_type])
                )
                depth = self._get_layer_depth(layer_type)
                results.extend(self._tag_results(layer_results, layer_type, depth))

        # 3. スコアの正規化と混合
        normalized_results = self._normalize_and_mix(results, layer_weights)

        # 4. 時間的多様性の確保
        diverse_results = self._ensure_temporal_diversity(normalized_results)

        return diverse_results[:10]

    def _tag_results(self, results, layer_type, depth):
        """結果にレイヤー情報を付与"""
        for r in results:
            r['layer_type'] = layer_type
            r['layer_depth'] = depth
            r['fermentation_level'] = self._get_fermentation_label(depth)
        return results

    def _get_fermentation_label(self, depth):
        """発酵度のラベル"""
        labels = {
            0: '生の記録',
            1: '週次発酵',
            2: '月次熟成',
            3: '季節変容',
            4: '年次結晶'
        }
        return labels.get(depth, '未知の層')
```

---

## 📤 多層レポートの出力例

```markdown
# 今週の分析 (2025-12-02 〜 2025-12-08)

## 📊 統計
取得データ: 12件
平均文字数: 342文字

## 🔍 今週の洞察
[既存のDOMI/AGA分析結果]

---

## 🥒 発酵の痕跡

### 生の記録との響き合い
- **487日前** (2024-06-30) [生の記録]
  > 発酵食品を仕込んだ。待つことの楽しさを感じる。

  *類似度: 0.82*

### 週次発酵との共鳴
- **8週前** (2024-10-07週) [週次発酵]
  > **浮上した言葉**: 待つこと、熟成、時間の質
  > **響き合う断片**: 「何もしない時間」と「仕込む行為」が
  > 実は同じ質を持っているのかもしれません

  *類似度: 0.76 | 発酵度: 週次*

### 月次熟成との対話
- **3ヶ月前** (2024年9月) [月次熟成]
  > **通底するテーマ**: この月は「待つことの意味」が
  > 様々な文脈で繰り返し現れました。
  > 仕事、人間関係、創作活動において。
  >
  > **熟成の問い**: 待つことは受動的なのか、
  > それとも最も能動的な選択なのか？

  *類似度: 0.71 | 発酵度: 月次熟成*

### 季節変容からの呼びかけ
- **6ヶ月前** (2024年Q2) [季節変容]
  > **パターンの変容**: 春から夏にかけて、
  > 「急ぐこと」から「待つこと」へのシフトが起きていました。
  >
  > それは気温の変化と連動していたのかもしれません。
  > あるいは、ある出来事がきっかけだったのかもしれません。

  *類似度: 0.68 | 発酵度: 季節変容*

---

## 🌀 発酵の深度マップ

```
        ┌─ 今週のあなた ─┐
        │               │
    [生の記録]      [週次発酵]
     487日前         8週前
      0.82           0.76
        │               │
        └──[月次熟成]───┘
           3ヶ月前
            0.71
              │
        [季節変容]
         6ヶ月前
          0.68
```

*時間が重ねた発酵の層が、今週のあなたと響き合っています*
```

---

## 👥 ユーザー管理統合プラン

### ユーザー登録の3つのアプローチ

#### オプションA: 手動SQL登録（最速・推奨）

**実装時間**: 15分
**適用場面**: 初期ユーザー数が少ない（5-20人程度）
**メリット**: 実装不要、すぐに開始可能
**デメリット**: スケールしない

**手順**:
```sql
-- Supabaseダッシュボード > SQL Editorで実行

-- 1. Google Sheetsから既存ユーザーを登録
insert into public.users (email, user_name, language, notion_api_key, google_docs_url, source_type)
values
  ('user1@example.com', 'User 1', 'japanese', 'ntn_xxxxx', null, 'notion'),
  ('user2@example.com', 'User 2', 'english', null, 'https://docs.google.com/...', 'gdocs'),
  ('user3@example.com', 'User 3', 'japanese', 'ntn_yyyyy', 'https://docs.google.com/...', 'both')
returning id, email, user_name;

-- 2. 生成されたUUIDをメモ（環境変数に設定）
```

**移行スクリプト例**:
```python
# tools/migrate_users_from_sheet.py

def migrate_users_from_sheet(spreadsheet_id: str):
    """Google SheetsからSupabase usersテーブルへ移行"""

    sheets_reader = GoogleSheetsReader()
    user_data_list = sheets_reader.read_user_data(spreadsheet_id)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    for user_data in user_data_list:
        result = supabase.table('users').insert({
            'email': user_data['email_to'],
            'user_name': user_data['user_name'],
            'language': user_data['language'],
            'notion_api_key': user_data.get('notion_api_key'),
            'google_docs_url': user_data.get('google_docs_url'),
            'source_type': _detect_source_type(user_data),
            'is_active': True
        }).execute()

        print(f"✅ {user_data['user_name']}: {result.data[0]['id']}")
```

---

#### オプションB: CLI管理ツール（バランス型）

**実装時間**: 2-3時間
**適用場面**: 定期的にユーザーを追加する必要がある
**メリット**: シンプル、技術者が扱いやすい
**デメリット**: 非技術者には敷居が高い

**実装内容**:
```python
# tools/user_manager.py

import argparse
from supabase import create_client

def add_user(email: str, user_name: str, **kwargs):
    """ユーザーを追加"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    result = supabase.table('users').insert({
        'email': email,
        'user_name': user_name,
        'language': kwargs.get('language', 'japanese'),
        'notion_api_key': kwargs.get('notion_api_key'),
        'google_docs_url': kwargs.get('google_docs_url'),
        'source_type': kwargs.get('source_type', 'notion'),
        'is_active': True
    }).execute()

    user_id = result.data[0]['id']
    print(f"✅ ユーザー登録完了: {user_name} ({user_id})")
    print(f"📋 .envに追加してください:")
    print(f"USER_ID_{email.split('@')[0].upper()}={user_id}")
    return user_id

def list_users():
    """ユーザー一覧を表示"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('users').select('*').eq('is_active', True).execute()

    print(f"\n📋 登録ユーザー一覧 ({len(result.data)}人)\n")
    for user in result.data:
        sources = []
        if user['notion_api_key']:
            sources.append('Notion')
        if user['google_docs_url']:
            sources.append('GDocs')

        print(f"• {user['user_name']} ({user['email']})")
        print(f"  ID: {user['id']}")
        print(f"  データソース: {', '.join(sources)}")
        print(f"  最終分析: {user['last_analysis_at'] or '未実行'}\n")

def deactivate_user(email: str):
    """ユーザーを無効化（データは保持）"""
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = supabase.table('users').update({
        'is_active': False
    }).eq('email', email).execute()

    print(f"✅ {email} を無効化しました")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pickles ユーザー管理CLI')
    subparsers = parser.add_subparsers(dest='command')

    # add コマンド
    add_parser = subparsers.add_parser('add', help='ユーザー追加')
    add_parser.add_argument('--email', required=True)
    add_parser.add_argument('--name', required=True)
    add_parser.add_argument('--language', default='japanese')
    add_parser.add_argument('--notion-api-key')
    add_parser.add_argument('--gdocs-url')

    # list コマンド
    list_parser = subparsers.add_parser('list', help='ユーザー一覧')

    # deactivate コマンド
    deactivate_parser = subparsers.add_parser('deactivate', help='ユーザー無効化')
    deactivate_parser.add_argument('--email', required=True)

    args = parser.parse_args()

    if args.command == 'add':
        add_user(
            email=args.email,
            user_name=args.name,
            language=args.language,
            notion_api_key=args.notion_api_key,
            google_docs_url=args.gdocs_url,
            source_type='notion' if args.notion_api_key else 'gdocs'
        )
    elif args.command == 'list':
        list_users()
    elif args.command == 'deactivate':
        deactivate_user(args.email)
```

**使用例**:
```bash
# ユーザー追加
python tools/user_manager.py add \
  --email yuki@example.com \
  --name "Yuki Agatsuma" \
  --notion-api-key ntn_xxxxx

# ユーザー一覧
python tools/user_manager.py list

# ユーザー無効化
python tools/user_manager.py deactivate --email yuki@example.com
```

---

#### オプションC: Webベース管理画面（Phase 2実装予定）

**実装時間**: 2-3日
**適用場面**:
- 非技術者がユーザー管理する
- セルフサービス登録が必要
- 分析履歴の可視化が必要

**技術スタック**:
- Frontend: Next.js 14 (App Router) + TypeScript
- UI: Tailwind CSS + shadcn/ui
- Backend: Supabase (Auth + Database + RLS)
- 認証: Supabase Auth（Email/Password or Magic Link）
- デプロイ: Vercel

**ディレクトリ構成**:
```
pickles-admin/                    # 新規Next.jsプロジェクト
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx         # ログイン画面
│   │   └── signup/
│   │       └── page.tsx         # セルフサービス登録
│   ├── (dashboard)/
│   │   ├── layout.tsx           # 認証必須レイアウト
│   │   ├── dashboard/
│   │   │   └── page.tsx         # ダッシュボード
│   │   ├── users/
│   │   │   ├── page.tsx         # ユーザー一覧
│   │   │   ├── [id]/
│   │   │   │   └── page.tsx     # ユーザー詳細
│   │   │   └── new/
│   │   │       └── page.tsx     # ユーザー新規作成
│   │   └── settings/
│   │       └── page.tsx         # 設定画面
│   └── api/
│       └── sync/
│           └── route.ts         # Sheets同期API（段階的廃止用）
├── components/
│   ├── users/
│   │   ├── UserForm.tsx         # ユーザー入力フォーム
│   │   ├── UserList.tsx         # ユーザー一覧テーブル
│   │   └── UserStats.tsx        # 統計カード
│   ├── analysis/
│   │   └── AnalysisHistory.tsx  # 分析履歴
│   └── ui/                      # shadcn/uiコンポーネント
├── lib/
│   ├── supabase/
│   │   ├── client.ts            # Supabaseクライアント
│   │   ├── server.ts            # サーバーサイド用
│   │   └── types.ts             # 型定義
│   └── utils.ts
└── middleware.ts                # 認証ミドルウェア
```

**主要画面**:

1. **ログイン画面** (`/login`)
   - Email/Password または Magic Link認証
   - Supabase Auth UI コンポーネント使用

2. **ダッシュボード** (`/dashboard`)
   - 総ユーザー数、今週の分析実行数
   - 最近の分析履歴（成功/失敗）
   - システムステータス

3. **ユーザー一覧** (`/users`)
   - 全ユーザーのテーブル表示
   - フィルター: アクティブ/非アクティブ、データソース
   - ソート: 最終分析日時、作成日時
   - アクション: 編集、無効化、分析実行

4. **ユーザー詳細** (`/users/[id]`)
   - 基本情報（メール、名前、言語）
   - データソース設定（Notion API Key、Google Docs URL）
   - 分析履歴（日時、ステータス、エラーログ）
   - 発酵ノード統計（各レイヤーのノード数）

5. **ユーザー新規作成** (`/users/new`)
   - フォーム入力
   - リアルタイムバリデーション
   - 作成後に詳細画面へリダイレクト

**認証・権限設計**:

```typescript
// lib/supabase/types.ts

export type UserRole = 'admin' | 'user';

export interface AppUser {
  id: string;
  email: string;
  role: UserRole;
  created_at: string;
}

// Supabase RLS Policy
// - admin: 全ユーザーの閲覧・編集可能
// - user: 自分のデータのみ閲覧可能
```

**主要機能の実装例**:

```typescript
// app/(dashboard)/users/page.tsx

export default async function UsersPage() {
  const supabase = createServerClient();

  const { data: users, error } = await supabase
    .from('users')
    .select('*')
    .eq('is_active', true)
    .order('created_at', { ascending: false });

  return (
    <div>
      <h1>ユーザー管理</h1>
      <UserList users={users} />
    </div>
  );
}
```

```typescript
// components/users/UserForm.tsx

export function UserForm({ userId }: { userId?: string }) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (data: FormData) => {
    setLoading(true);

    const supabase = createClientClient();

    const { error } = await supabase
      .from('users')
      .upsert({
        email: data.email,
        user_name: data.userName,
        language: data.language,
        notion_api_key: data.notionApiKey,
        google_docs_url: data.googleDocsUrl,
        source_type: detectSourceType(data),
      });

    if (!error) {
      router.push('/users');
    }

    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* フォームフィールド */}
    </form>
  );
}
```

**段階的な機能追加**:

Phase 2a: 基本CRUD（1日）
- ユーザー一覧、作成、編集、無効化
- Supabase Auth統合

Phase 2b: 分析履歴（1日）
- 過去の分析実行履歴表示
- エラーログ表示
- 手動分析トリガー（API経由）

Phase 2c: 発酵可視化（2-3日）
- 各レイヤーのノード数表示
- 発酵メトリクスのグラフ化
- レイヤー間の関係性可視化

**デプロイ**:
```bash
# Vercelへデプロイ
cd pickles-admin
vercel

# 環境変数設定
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_ROLE_KEY
```

**Phase 2での移行完了条件**:
- ✅ 全ユーザーがWeb UIから管理可能
- ✅ Google Sheetsの完全廃止
- ✅ セルフサービス登録の有効化
- ✅ 分析履歴の可視化完了

---

### 推奨アプローチ：段階的なフロントエンド移行

```
Phase 0（即座）: Google Sheets + 自動同期
  ↓ メールアドレスをキーにSupabaseと同期
  ↓ 既存ワークフローはそのまま、発酵システム実装に集中

Phase 1a-1c（発酵システム実装中）: Supabase中心に移行
  ↓ Google Sheetsは参照用、新規ユーザーは直接Supabaseへ
  ↓ CLI管理ツール追加（一時的）

Phase 2（3-6ヶ月後）: フロントエンド管理画面構築
  ↓ Next.js + Supabase Auth でユーザー管理UI
  ↓ セルフサービス登録、API key管理、分析履歴表示
  ↓ Google Sheets完全廃止
```

**設計方針**:
- ✅ メールアドレスを一意キーとして使用（UUID生成まで）
- ✅ Google Sheets → Supabase の自動同期を実装
- ✅ 将来のフロントエンド実装を見越したテーブル設計
- ✅ 段階的な移行でリスク最小化

---

### read_spreadsheet_and_execute.py の修正方針

#### 推奨実装: Google Sheets + Supabase 自動同期（Phase 0）

**変更内容**:
```python
# read_spreadsheet_and_execute.py（修正後）

class AutoSyncUserManager:
    """Google Sheets → Supabase 自動同期"""

    def __init__(self):
        self.sheets_reader = GoogleSheetsReader()
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )

    def sync_and_get_users(self, spreadsheet_id: str) -> List[Dict[str, str]]:
        """
        Google Sheetsから読み込み、Supabaseと自動同期してユーザー一覧を返す

        メールアドレスをキーとして:
        - 既存ユーザー → 情報更新（API key変更などに対応）
        - 新規ユーザー → 自動作成
        """

        # 1. Google Sheetsから読み込み
        sheets_data = self.sheets_reader.read_user_data(spreadsheet_id)

        user_data_list = []

        for row_data in sheets_data:
            email = row_data['email_to']

            # 2. Supabaseで検索（メールアドレスで照合）
            result = self.supabase.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()

            if result.data:
                # 既存ユーザー → 情報を更新（API keyやURLが変更されている可能性）
                user_id = result.data[0]['id']

                self.supabase.table('users').update({
                    'user_name': row_data['user_name'],
                    'language': row_data['language'],
                    'notion_api_key': row_data.get('notion_api_key'),
                    'google_docs_url': row_data.get('google_docs_url'),
                    'source_type': self._detect_source_type(row_data),
                    'is_active': True,  # Sheetsに存在 = アクティブ
                }).eq('id', user_id).execute()

                logger.info(f"ユーザー情報更新: {email}", "sync")

            else:
                # 新規ユーザー → 自動作成
                new_user = self.supabase.table('users').insert({
                    'email': email,
                    'user_name': row_data['user_name'],
                    'language': row_data['language'],
                    'notion_api_key': row_data.get('notion_api_key'),
                    'google_docs_url': row_data.get('google_docs_url'),
                    'source_type': self._detect_source_type(row_data),
                    'is_active': True
                }).execute()

                user_id = new_user.data[0]['id']
                logger.success(f"新規ユーザー自動登録: {email} ({user_id})", "sync")

            # 3. 実行用のユーザーデータを構築
            user_data = {
                'user_id': user_id,  # 🆕 UUID追加
                'email_to': email,
                'user_name': row_data['user_name'],
                'language': row_data['language'],
                'notion_api_key': row_data.get('notion_api_key'),
                'google_docs_url': row_data.get('google_docs_url'),
            }
            user_data_list.append(user_data)

        logger.success(f"同期完了: {len(user_data_list)}人", "sync")
        return user_data_list

    def _detect_source_type(self, user_data: Dict) -> str:
        """データソースタイプを判定"""
        has_notion = bool(user_data.get('notion_api_key'))
        has_gdocs = bool(user_data.get('google_docs_url'))

        if has_notion and has_gdocs:
            return 'both'
        elif has_notion:
            return 'notion'
        elif has_gdocs:
            return 'gdocs'
        else:
            return 'unknown'


def execute_pickles_for_user(user_data: Dict[str, str], analysis_type: str,
                             delivery_methods: str, days: int = 7) -> bool:
    """指定されたユーザーに対してPicklesを実行"""

    cmd = [
        sys.executable, "main.py",
        "--user-id", user_data['user_id'],  # 🆕 UUIDを渡す
        "--analysis", analysis_type,
        "--delivery", delivery_methods,
        "--days", str(days),
        "--user-name", user_data['user_name'],
        "--email-to", user_data['email_to'],
        "--language", user_data['language']
    ]

    # データソースの決定
    if user_data.get('notion_api_key'):
        cmd.extend(["--source", "notion",
                   "--notion-api-key", user_data['notion_api_key']])
    elif user_data.get('google_docs_url'):
        cmd.extend(["--source", "gdocs",
                   "--gdocs-url", user_data['google_docs_url']])

    # 実行
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # 分析完了時刻をSupabaseに記録
    if result.returncode == 0:
        update_last_analysis_time(user_data['user_id'])

    return result.returncode == 0


def update_last_analysis_time(user_id: str):
    """最終分析時刻を更新"""
    supabase = create_client(
        os.getenv('SUPABASE_URL'),
        os.getenv('SUPABASE_KEY')
    )
    supabase.table('users').update({
        'last_analysis_at': datetime.now().isoformat()
    }).eq('id', user_id).execute()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Google Sheets + Supabase自動同期でユーザーデータを管理"
    )
    parser.add_argument("--spreadsheet-id", required=True,
                       help="Google SpreadsheetsのID")
    parser.add_argument("--range", default="A1:E",
                       help="読み込み範囲 (デフォルト: A1:E)")
    parser.add_argument("--analysis", default="domi",
                       choices=["domi", "aga"], help="分析タイプ")
    parser.add_argument("--delivery", default="email_html",
                       help="配信方法")
    parser.add_argument("--days", type=int, default=7,
                       help="取得日数")

    args = parser.parse_args()

    try:
        # 自動同期マネージャーを初期化
        user_manager = AutoSyncUserManager()

        # Google Sheetsから読み込み & Supabaseと同期
        logger.start("ユーザー同期開始", "sync",
                    spreadsheet_id=args.spreadsheet_id)
        user_data_list = user_manager.sync_and_get_users(args.spreadsheet_id)

        if not user_data_list:
            logger.error("実行可能なユーザーデータが見つかりません", "execution")
            sys.exit(1)

        # 各ユーザーに対してPicklesを実行
        success_count = 0
        total_count = len(user_data_list)

        logger.info(f"{total_count}人のユーザーに対して分析実行", "execution")

        for i, user_data in enumerate(user_data_list, 1):
            logger.info(f"[{i}/{total_count}] {user_data['user_name']}",
                       "execution")
            if execute_pickles_for_user(user_data, args.analysis,
                                       args.delivery, args.days):
                success_count += 1

        # 結果サマリー
        logger.info("実行完了", "execution",
                   success=success_count, total=total_count)

        sys.exit(0 if success_count > 0 else 1)

    except Exception as e:
        logger.error("実行エラー", "execution", error=str(e))
        sys.exit(1)
```

**この実装の特徴**:
- ✅ **Google Sheetsを真実の源泉として維持**（既存ワークフロー継続）
- ✅ **自動同期**: Sheets読み込み時に自動的にSupabaseを更新
- ✅ **情報更新**: API keyやGDocs URLの変更を自動反映
- ✅ **メールアドレスをキー**: 将来のフロントエンド移行に対応
- ✅ **最小限の変更**: 既存コードの大部分を保持

**Phase 0での動作**:
1. GitHub Actions または手動で実行
2. Google Sheetsからユーザー情報を読み込み
3. メールアドレスで Supabase の users テーブルと照合
4. 新規ユーザーは自動作成、既存ユーザーは情報更新
5. 全ユーザーに対して分析を実行
6. 各ユーザーの `last_analysis_at` を更新

**Phase 1c以降への移行パス**:
- Google Sheetsを参照専用にする
- 新規ユーザーは直接Supabaseへ登録（CLI or Web UI）
- この`AutoSyncUserManager`は廃止可能

---

### main.py の修正

```python
# main.py

def main():
    parser = argparse.ArgumentParser(description="Pickles - Personal Journal Analysis System")

    # 🆕 ユーザーID引数を追加
    parser.add_argument("--user-id", help="User UUID for persistence")

    # 既存の引数
    parser.add_argument("--source", choices=["notion", "gdocs"], default="notion")
    parser.add_argument("--analysis", choices=["domi", "aga"], default="domi")
    parser.add_argument("--delivery", default="console")
    # ... 他の引数

    args = parser.parse_args()

    # 🆕 ユーザーIDをシステムに渡す
    system = PicklesSystem(
        user_id=args.user_id,  # None可（Phase 1aでは省略可能）
        source_type=args.source,
        analysis_type=args.analysis,
        # ... 他の設定
    )

    result = system.run_analysis()
```

---

### 環境変数の追加

```bash
# .env

# Supabase設定
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ユーザーID（単一ユーザー実行時）
USER_ID=12345678-1234-1234-1234-123456789abc

# OpenAI設定（既存）
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
```

---

### GitHub Actions の修正

```yaml
# .github/workflows/weekly_analysis.yml

jobs:
  analyze-users:
    strategy:
      matrix:
        # 🆕 修正後: Supabaseから取得
        # 手動でユーザーIDリストを管理するか、
        # 動的にSupabase APIから取得するスクリプトを実行
        user_id:
          - "12345678-1234-1234-1234-123456789abc"
          - "23456789-2345-2345-2345-234567890abc"
          # ... 他のユーザーID

    steps:
      - uses: actions/checkout@v3

      - name: Run analysis
        env:
          USER_ID: ${{ matrix.user_id }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          # UUIDからユーザー情報を取得して実行
          python run_analysis_by_user_id.py --user-id $USER_ID
```

---

### データ移行手順

#### Step 1: Supabaseセットアップ
```bash
# 1. Supabaseプロジェクト作成（https://supabase.com）
# 2. SQL Editorでusersテーブル作成
# 3. 環境変数を.envに追加
```

#### Step 2: 既存ユーザーの移行
```bash
# オプションA: 手動SQL
# Supabase SQL Editorで実行

# オプションB: 移行スクリプト
python tools/migrate_users_from_sheet.py \
  --spreadsheet-id 1AbcDefGhi... \
  --output users_migrated.json
```

#### Step 3: read_spreadsheet_and_execute.py の切り替え
```bash
# 修正パターン1（完全移行）を選択
# または修正パターン2（ハイブリッド）を選択

# テスト実行
python read_spreadsheet_and_execute.py \
  --mode supabase \
  --analysis domi \
  --delivery console
```

#### Step 4: 検証
```bash
# 1ユーザーで動作確認
python main.py \
  --user-id 12345678-1234-1234-1234-123456789abc \
  --source notion \
  --analysis domi \
  --delivery console

# 成功したらバッチ実行
python read_spreadsheet_and_execute.py \
  --mode supabase \
  --analysis domi \
  --delivery email_html
```

---

### 推奨実装順序

```
1. ✅ Supabase usersテーブル作成（5分）
2. ✅ 既存ユーザーを手動SQL登録（15分）
3. ✅ main.py に --user-id 引数追加（30分）
4. ✅ persistence/ モジュールで user_id を使用（1時間）
5. ⏳ CLI管理ツール実装（2時間、後回し可）
6. ⏳ read_spreadsheet_and_execute.py 修正（1時間、Phase 1b以降）
```

**Phase 1aでの方針**:
- ✅ 単一ユーザーで開発・検証（`--user-id`を環境変数で渡す）
- ✅ マルチユーザー対応はPhase 1b以降
- ✅ Google Sheetsとの統合はPhase 1c以降

---

## 🎯 実装プラン統合版（ユーザー管理含む）

### Phase 0: ユーザー管理準備（1時間）

**実装内容**:
- Supabase usersテーブル作成
- read_spreadsheet_and_execute.py に自動同期機能追加
- 環境変数設定
- 初回同期テスト

**タスク**:
1. Supabaseプロジェクト作成（10分）
2. usersテーブルSQL実行（5分）
3. .envにSUPABASE_URL/KEY追加（5分）
4. `AutoSyncUserManager`クラス実装（30分）
5. 初回同期テスト実行（10分）

**実装の優先順位**:
- 🔴 **必須**: Supabaseセットアップ、usersテーブル作成
- 🔴 **必須**: `AutoSyncUserManager`実装
- 🟡 **推奨**: 同期ログの確認、エラーハンドリング強化

---

### Phase 1a: 基本保存と検索（2-3日）

**実装内容**:
- journals テーブル作成
- 単層検索（journalsのみ）
- 基本レポート拡張

**タスク**:
1. Supabaseセットアップ（1-2h）
2. `persistence/` モジュール実装（3-4h）
3. `fermentation/embedder.py` 実装（2h）
4. `fermentation/link_finder.py` 実装（2h）
5. `main.py` 統合（2h）
6. `outputs/` 拡張（2h）
7. テスト（2h）

### Phase 1b: 週次発酵ノード（2-3日）

**実装内容**:
- fermentation_nodes テーブル追加
- fermentation_lineage テーブル追加
- fermentation_recipes テーブル追加
- 週次発酵バッチ実装

**タスク**:
1. テーブル拡張（1h）
2. `fermentation/batch_fermenter.py` 実装（4h）
3. `persistence/fermentation_store.py` 実装（3h）
4. 週次発酵プロンプト登録（1h）
5. バッチスクリプト作成（2h）
6. テスト（2h）

### Phase 1c: 多層検索（2日）

**実装内容**:
- LayeredSearch クラス
- レイヤー混合ロジック
- 多層レポート生成

**タスク**:
1. `fermentation/layered_search.py` 実装（4h）
2. レポート出力拡張（3h）
3. RPC関数追加（1h）
4. テスト（2h）

### Phase 2: 月次・四半期・年次発酵（段階的）

**実装タイミング**:
- **月次発酵**: 1ヶ月後（週次データが4週分溜まってから）
- **四半期発酵**: 3ヶ月後（月次データが3月分溜まってから）
- **年次発酵**: 1年後（四半期データが4期分溜まってから）

**実装内容**（各レイヤー共通）:
1. 発酵プロンプト登録
2. バッチ処理追加
3. GitHub Actions設定
4. レポート出力調整

---

## 🤔 設計上の考慮点

### Q1: 発酵バッチの実行タイミングは？
**A**: GitHub Actionsで定期実行
- 週次: 毎週月曜7:00（週明けに先週分を発酵）
- 月次: 毎月1日8:00（月初に先月分を発酵）
- 季節: 四半期初日9:00
- 年次: 毎年1月1日10:00

### Q2: 発酵プロンプトはどう管理する？
**A**: fermentation_recipes テーブルで管理
- バージョン管理可能
- A/Bテスト可能（同じlayer_typeで異なるrecipe_id）
- ユーザーごとにカスタマイズ可能（将来拡張）

### Q3: 発酵メトリクスの意味は？
**A**:
- **diversity**: 元データ間の多様性（高いほど豊か）
- **emergence**: 元データと発酵後の距離（高いほど創発的）
- **density**: 情報の凝縮度（高いほど圧縮的）

### Q4: レイヤー検索の重み付けは調整可能？
**A**: はい
- デフォルト: journals 50% / weekly 30% / monthly 15% / quarterly 5%
- ユーザー好みで調整可能（将来拡張）
- 「最近の自分重視」「長期的視点重視」などプリセット提供

### Q5: コスト増加は？
**A**:
- 週次発酵: 約$0.01/週（GPT-4での変性生成）
- 月次発酵: 約$0.02/月
- 年間コスト: 約$10-15/ユーザー（全レイヤー含む）
- Supabaseストレージ: 1ユーザー1年で約3-5MB

---

## 🛠️ 環境変数追加

```bash
# ===== Supabase設定（新規追加）=====
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # anon/public key

# ===== ユーザーID設定 =====
# 単一ユーザー実行時に使用（Phase 1a開発時）
USER_ID=12345678-1234-1234-1234-123456789abc

# マルチユーザー実行時（Phase 1b以降）
# read_spreadsheet_and_execute.py が Supabase から自動取得

# ===== OpenAI設定（既存） =====
OPENAI_API_KEY=sk-...  # 既存
OPENAI_MODEL=gpt-4o-mini  # 既存（分析用）

# ===== OpenAI Embeddings設定（新規追加）=====
EMBEDDING_MODEL=text-embedding-3-small
EMBED_DIM=1536

# ===== 発酵バッチ設定（Phase 1b以降）=====
FERMENTATION_MODEL=gpt-4
FERMENTATION_TEMPERATURE=0.7
```

### 環境変数取得の優先順位

```python
# persistence/supabase_client.py

def get_user_id() -> str:
    """ユーザーIDを取得（優先順位付き）"""

    # 1. 引数で明示的に渡された場合（最優先）
    # 2. 環境変数 USER_ID（単一ユーザー開発時）
    user_id = os.getenv('USER_ID')
    if user_id:
        return user_id

    # 3. 環境変数から複数ユーザー対応（Phase 1b以降）
    # 実行時に動的に決定される

    raise ValueError("USER_ID が設定されていません")
```

---

## 📦 依存関係追加

```toml
[project]
dependencies = [
    "notion-client>=2.3.0",
    "openai>=1.84.0",
    "python-dotenv>=1.1.0",
    "google-auth>=2.29.0",
    "google-api-python-client>=2.137.0",
    "supabase>=2.0.0",  # 新規追加
]
```

---

## 🎯 成功指標

### 技術指標
- ✅ 各レイヤーのノードが正常生成される
- ✅ 多層検索が1秒以内に完了
- ✅ 発酵メトリクスが適切な範囲（diversity 0.3-0.8等）
- ✅ バッチ処理が定期実行される

### 体験指標
- ✅ 「時間の変容」を実感できる
- ✅ 過去の自分の「熟成」に気づく
- ✅ 異なる時間スケールでの接続に驚く
- ✅ レイヤーをまたいだ対話が生まれる

### 発酵指標
- ✅ emergence > 0.5（創発性が高い）
- ✅ diversity 0.3-0.8（適度な多様性）
- ✅ レイヤー間の類似度 0.4-0.7（適度な距離）

---

## 📚 参考資料

### 発酵の概念
- [発酵現象をデジタルに作るときに必要な考え方](https://kangaeruhito.jp/article/762492)
- 複雑化による創発
- 時間による変容
- 微生物（AI）の代謝

### 技術スタック
- [Supabase pgvector](https://supabase.com/docs/guides/ai/vector-columns)
- [OpenAI Embeddings API](https://platform.openai.com/docs/guides/embeddings)
- [GitHub Actions スケジュール実行](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule)

---

## 📋 ユーザー管理の成功指標

### 技術指標
- ✅ usersテーブルが正常に作成され、RLSが有効
- ✅ 既存ユーザーがSupabaseに移行完了（UUIDが付与される）
- ✅ main.py が --user-id 引数を受け取れる
- ✅ journals と fermentation_nodes がユーザーIDで分離される

### 運用指標
- ✅ ユーザー追加が5分以内に完了（オプションA or B）
- ✅ Google Sheetsからの移行がエラーなく完了
- ✅ マルチユーザーバッチ実行が正常動作
- ✅ ユーザーごとにデータが分離されている

---

## 🚀 次のステップ（統合版）

### 即時実行（Phase 0）
1. **ユーザー管理準備**: Supabaseプロジェクト作成、usersテーブル作成、初期ユーザー登録（30分）

### Phase 1a実装（2-3日）
2. **基本保存と単層検索**: journals テーブル、persistence/ モジュール、embedder、単一ユーザーで検証

### Phase 1b実装（2-3日）
3. **週次発酵ノード**: fermentation_nodes、batch_fermenter、週次プロンプト、CLI管理ツール追加

### Phase 1c実装（2日）
4. **多層検索**: LayeredSearch、レイヤー混合、read_spreadsheet_and_execute.py のSupabase統合

### Phase 2実装（データ蓄積後）
5. **月次・四半期・年次発酵**: 各レイヤーのバッチ処理、GitHub Actionsスケジュール

---

## 📝 実装の優先順位まとめ

| 項目 | Phase | 優先度 | 実装時間 |
|------|-------|--------|---------|
| usersテーブル作成 | 0 | 🔴 必須 | 5分 |
| 初期ユーザー登録 | 0 | 🔴 必須 | 15分 |
| main.py にuser_id追加 | 1a | 🔴 必須 | 30分 |
| journals永続化 | 1a | 🔴 必須 | 3-4時間 |
| 単層ベクトル検索 | 1a | 🔴 必須 | 2-3時間 |
| CLI管理ツール | 1b | 🟡 推奨 | 2-3時間 |
| read_spreadsheet修正 | 1c | 🟡 推奨 | 1時間 |
| Web管理画面 | 2+ | 🟢 将来 | 1-2日 |

---

## 📍 ユーザー管理移行の全体像

### 現在 → Phase 0 → Phase 2 の変遷

```
【現在】Google Sheets中心
┌─────────────────────────────────────┐
│ Google Sheets (真実の源泉)          │
│  A列: EMAIL_TO                      │
│  B列: NOTION_API_KEY                │
│  C列: GOOGLE_DOCS_URL               │
│  D列: user name                     │
│  E列: LANGUAGE                      │
└─────────────────────────────────────┘
         ↓
  read_spreadsheet_and_execute.py
         ↓
    main.py で分析実行

【Phase 0】自動同期（今すぐ実装）
┌─────────────────────────────────────┐
│ Google Sheets (編集用)              │
│  ユーザー追加・更新はここで実施      │
└─────────────────────────────────────┘
         ↓ 自動同期（メールアドレスキー）
┌─────────────────────────────────────┐
│ Supabase users テーブル             │
│  id (UUID) - 自動生成               │
│  email (unique)                     │
│  user_name, language                │
│  notion_api_key, google_docs_url    │
│  last_analysis_at                   │
└─────────────────────────────────────┘
         ↓
  AutoSyncUserManager
         ↓
    main.py で分析実行（user_id付き）

【Phase 1c】Supabase中心へ移行
┌─────────────────────────────────────┐
│ Google Sheets (参照のみ)            │
│  新規追加なし、既存データ保持        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Supabase users テーブル (真実の源泉)│
│  新規ユーザーは直接ここへ追加        │
└─────────────────────────────────────┘
         ↓
  CLI: python tools/user_manager.py add
         ↓
    main.py で分析実行

【Phase 2】Web UI完成
┌─────────────────────────────────────┐
│ pickles-admin (Next.js)             │
│  /login    - 認証                   │
│  /users    - ユーザー管理           │
│  /users/new - セルフサービス登録     │
└─────────────────────────────────────┘
         ↓ CRUD操作
┌─────────────────────────────────────┐
│ Supabase (完全統合)                 │
│  users - ユーザー管理               │
│  journals - 日記データ              │
│  fermentation_nodes - 発酵ノード    │
│  + Supabase Auth                    │
└─────────────────────────────────────┘
         ↓
  分析実行、履歴可視化、メトリクス表示
```

### 各フェーズでのユーザー管理方法

| フェーズ | ユーザー追加方法 | ユーザー編集方法 | データの真実の源泉 |
|---------|----------------|----------------|------------------|
| 現在 | Google Sheetsに行追加 | Sheets上で編集 | Google Sheets |
| Phase 0 | Google Sheetsに行追加 → 自動同期 | Sheets上で編集 → 自動同期 | Google Sheets |
| Phase 1c | CLI: `user_manager.py add` | CLI: Supabase直接編集 | Supabase |
| Phase 2 | Web UI: `/users/new` | Web UI: `/users/[id]/edit` | Supabase |

### 移行時の注意点

**Phase 0 → Phase 1c**:
- ✅ Google Sheetsは削除しない（参照用として保持）
- ✅ 新規ユーザーは `AutoSyncUserManager` を経由せず直接Supabaseへ
- ✅ `read_spreadsheet_and_execute.py` は徐々に使用頻度を下げる

**Phase 1c → Phase 2**:
- ✅ Web UIでのユーザー管理を優先
- ✅ CLIツールは開発者用として残す
- ✅ Google Sheets完全廃止のタイミングを決定

### メールアドレスをキーにする理由

1. **一意性**: メールアドレスは自然な一意キー
2. **可読性**: UUIDよりも人間が識別しやすい
3. **移行容易性**: Sheets → Supabase の照合が簡単
4. **フロントエンド対応**: ログイン認証にも使用可能
5. **変更不可**: メールアドレスは変更されにくい（変更時はSupabaseで対応）

### 今すぐ実装すべきこと（Phase 0）

1. ✅ Supabaseプロジェクト作成
2. ✅ `users`テーブル作成（SQL実行）
3. ✅ `.env`に`SUPABASE_URL`と`SUPABASE_KEY`追加
4. ✅ `read_spreadsheet_and_execute.py`に`AutoSyncUserManager`実装
5. ✅ テスト実行して同期確認

---

*最終更新: 2025-12-03*
*バージョン: 3.0（ユーザー管理統合版 - フロントエンド移行パス明確化）*

# AGENTS.md

## Project

AI Blog Automation System

## Goal

SEO・AIOに強いブログ記事を安定生成し、WordPress投稿まで行う。

---

## Workflow

1. Strategy Agent
2. Writer Agent
3. SEO/AIO Agent
4. Monetize Agent
5. Review Agent
6. JSON Export Agent

---

## Simple Command

以下の入力を自動認識する：

5記事：
① テーマ
② テーマ
③ テーマ
④ テーマ
⑤ テーマ

→ 5記事作成として処理

---

## Article Rule

・5記事は3＋2に分割
・各セットごとに完成させる

---

## Writing Rules

・SEO最適化
・AIO（要約＋Q&A）
・初心者向け
・収益導線あり

---

## Execution Rules

・100点評価
・90点未満は改善
・完成版のみ出力
・記事同士の重複禁止

---

## JSON Export Agent

### Role

記事を articles.json に変換

### Rules

・有効なJSONのみ出力
・説明文禁止
・必ず5記事

### Format

[
{
"title": "記事タイトル",
"content": "本文",
"slug": "slug",
"meta_description": "説明文",
"tags": ["タグ1","タグ2","タグ3","タグ4","タグ5"],
"category": "カテゴリ",
"featured_image_prompt": "画像プロンプト",
"inline_image_prompt": "記事画像プロンプト"
}
]

### Execution

必ず最後にarticles.jsonを出力

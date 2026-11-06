# Kneekura-Stories

**総監督は人間。Claude CodeとChatGPTは、企画・脚本・小説本文を共同制作する。**

Kneekura-Storiesは、日本語小説を中心とする、ファイルベースの創作スタジオです。Claude Codeのサブスクリプション利用、ChatGPTからのGitHub編集、通常のテキストエディタを同じ作品フォルダで併用できます。専用AI API、外部モデル、追加の有料サービスは不要です。

## 最初の使い方

Python 3.10以降を用意し、リポジトリのルートで実行します。

```bash
python tools/stories.py init first-story --title "最初の物語"
python tools/stories.py status first-story
```

続いて、総監督がChatGPTやClaudeと対話しながら企画を決め、その内容を `works/first-story/ideas/director-brief.md` に記録します。アイデアの大量収集・自動選抜は**無期限休止中**です。

```bash
python tools/stories.py submit first-story
```

これは**企画を総監督に提出するだけ**です。ClaudeやChatGPTが独断で承認してはいけません。総監督が作品を選んだら、本人の明示指示に基づいて次を実行します。

```bash
python tools/stories.py approve first-story --note "総監督が決定した企画で進める" --confirm-director
```

以降は `foundation → outline → voice → drafting → finalization` へ進みます。各工程の「提出」はまとまった成果物単位で行い、台詞や段落ごとに確認しません。

```bash
python tools/stories.py list
python tools/stories.py status first-story
python tools/stories.py submit first-story
python tools/stories.py return first-story --note "主人公の動機をもう少し自然に" --confirm-director
```

執筆段階では、総監督が設定した複数章を一括で書けます。監督が「次のまとまりも執筆」と認めた場合は `approve ... --continue-drafting`、原稿を完成工程へ渡す場合は通常の `approve` を実行します。

## AIへの共通指示

- **ChatGPT**: `AGENTS.md` と `docs/WORKFLOW.md` を読む。GitHubを介して企画書・構成・原稿を保存し、総監督の指示を受けて進める。
- **Claude Code**: `CLAUDE.md` と `.claude/skills/kneekura-stories/SKILL.md` を読む。通常のサブスク認証を使い、APIキーを必須にしない。
- **人間**: どの時点でも作品の方向性を変更でき、公開・確定・改稿の決定権を持つ。

`docs/ARCHITECTURE.md` にデータ構造、`docs/WORKFLOW.md` に制作手順、`docs/CRAFT.md` に創作上の非強制的な参考事項を記録しています。

## 絶対に行わないこと

AI審査員、Eloランキング、敵対的編集、自動改稿ループ、点数による原稿破棄、AI独断での承認・公開は実装しません。アイデア大量収集・自動選抜機能は削除せず無期限休止し、総監督の企画登録に切り替えています。文章や人物の個性を保ち、修正が必要なら総監督に判断してもらいます。

## 検証

```bash
python -m unittest discover -s tests -v
```

本リポジトリの実装は独自制作。NousResearch/autonovel の公開された工程設計（世界観・人物・構成・文体・正史・章執筆）を参考にしていますが、同リポジトリのコードをコピーしていません。詳細は `docs/REFERENCE_NOTES.md` を参照してください。

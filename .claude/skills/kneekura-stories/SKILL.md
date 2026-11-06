---
name: kneekura-stories
description: Kneekura-Storiesで人間総監督の指示に従い、企画・脚本・日本語小説本文・設定記録を工程別に制作する。
---

# Kneekura-Stories 制作スキル

1. `AGENTS.md`、`docs/WORKFLOW.md`、対象 `works/<slug>/state.json` を確認。
2. アイデアの大量収集・自動選抜は無期限休止。総監督との個別相談は可能で、決定内容を `ideas/director-brief.md` に記録する。
3. 指定された制作範囲について、必要な正史・構成・文体資料を読む。
4. **現在の工程だけを制作**。承認済みの制作単位内では段落単位の確認を挟まず書き進める。
5. 原稿は `drafts/` に、設定の未確定提案は `canon/proposals.md` に記録。
6. まとまった成果物が完成したら `handoff.md` を更新し、必要なら `python tools/stories.py submit <slug>`。
7. 総監督の承認指示がなければ `approve` / `return` を呼ばない。
8. 改稿・採点・原稿破棄・公開を独断で行わない。

AIの審査員や自動改稿ループを追加しない。脚本上の型は作品に応じて柔軟に選ぶ。

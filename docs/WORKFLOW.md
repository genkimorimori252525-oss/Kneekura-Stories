# 制作工程 — 総監督主導

## 原則
総監督は人間。ClaudeとChatGPTは同じ資料を参照する制作者。工程ごとの手続きをそろえることと、表現を型に押し込むことは違う。**提出点は文章ごとではなく作品上の節目**とする。

## 6工程

| 段階 | AIが作るもの | 総監督の役割 | 必須ファイル |
|---|---|---|---|
| 1. ideation（監督の企画登録） | AIは個別相談の相手・記録係。自動収集は無期限休止 | 企画を相談で決めて登録する | `ideas/director-brief.md` |
| 2. foundation（基礎） | 企画・世界観・人物の動機や関係 | 作品の方向性を確定する | `planning/premise.md`, `canon/world.md`, `canon/characters.md` |
| 3. outline（脚本） | シノプシス、章構成、場面設計、伏線 | 大筋と結末を判断する | `planning/synopsis.md`, `planning/outline.md`, `planning/scenes.md`, `canon/foreshadowing.md` |
| 4. voice（文体） | 複数の試作文章、作品固有の文体資料 | 文体の方向を選ぶ | `drafts/voice-tests.md`, `style/voice.md` |
| 5. drafting（執筆） | まとまった章・シーンの本文 | 指定の章群を読んで進行判断 | `drafts/chapters/*.md` |
| 6. finalization（確定） | 指示済み修正反映、完成原稿 | 完成と公開可否を決める | `manuscript/*.md` |

### 通常の流れ
- `init` で作品を作る。最初は総監督がAIとの個別相談で決めた企画を `ideas/director-brief.md` に記録する。旧アイデア収集機能はコードを削除せず無期限休止。
- `submit` は提出物の存在とハッシュを記録し、監督の判断待ちにする（**品質評価はしない**）。
- 総監督が確認後、`approve` または `return` を指示する。
- `approve` は次工程へ進む。執筆工程だけ `--continue-drafting` で次の執筆まとまりへ進める。
- `return` は修正依頼のみを記録。原稿は消さない。AIは監督の指示箇所を必要な範囲だけ修正する。
- 提出後に原稿が変更されたら承認は拒否するが、差戻しは可能。再提出で修正後の内容を確認し、操作不能にならないようにする。
- 完成工程では、執筆した章のファイル名と完成原稿の章を照合し、欠落があれば提出を拒否する。
- 完了時も、自動投稿・公開・AIによる合否判定はしない。

### 監督承認の例

```bash
python tools/stories.py submit first-story
python tools/stories.py approve first-story --note "監督が決めた企画を採用" --confirm-director
python tools/stories.py submit first-story
python tools/stories.py return first-story --note "主人公の動機だけ見直して" --confirm-director
```

監督の判断は作品の `decisions.jsonl` に記録。CLIは認証システムではないため、`--confirm-director` をAIが勝手に指定してよいわけではない。

### 役割と作業範囲
- AIの大量アイデア収集と自動選抜は起動しない。総監督からの個別相談の依頼にのみ応じ、決定は総監督が行う。
- 脚本担当は物語の因果関係と構成を考える。三幕構成などを強制しない。
- 小説担当は台詞、地の文、沈黙や人物の反応に創作裁量を持つ。
- 正史候補は `canon/proposals.md` に置き、総監督の指示により確定資料へ反映する。
- Claude / ChatGPT間の引継ぎは `handoff.md` に、担当の章と未解決点を記す。
- 監督が承認した後の作業範囲内では、段落単位の確認を挟まずまとまって執筆する。

### 回帰・復元
- Gitの履歴で前の稿を保持する。原稿変更時は差分を残す。
- ハッシュによる提出固定は改稿指示によって解除される。自動破棄・強制リセットはしない。
- 品質や個性の判断を、数値評価、AI審査員、Elo、自動改稿ループに委ねない。

# 制作工程 — 総監督主導

## 原則
総監督は人間。ClaudeとChatGPTは同じ資料を参照する制作者。工程ごとの手続きをそろえることと、表現を型に押し込むことは違う。**提出点は文章ごとではなく作品上の節目**とする。

## 6工程

| 段階 | AIが作るもの | 総監督の役割 | 必須ファイル |
|---|---|---|---|
| 1. ideation（企画） | 多様なアイデア候補（目安10〜20） | 好きな企画を選ぶ | `ideas/candidates.md` |
| 2. foundation（基礎） | 企画・世界観・人物の動機や関係 | 作品の方向性を確定する | `planning/premise.md`, `canon/world.md`, `canon/characters.md` |
| 3. outline（脚本） | シノプシス、章構成、場面設計、伏線 | 大筋と結末を判断する | `planning/synopsis.md`, `planning/outline.md`, `planning/scenes.md`, `canon/foreshadowing.md` |
| 4. voice（文体） | 複数の試作文章、作品固有の文体資料 | 文体の方向を選ぶ | `drafts/voice-tests.md`, `style/voice.md` |
| 5. drafting（執筆） | まとまった章・シーンの本文 | 指定の章群を読んで進行判断 | `drafts/chapters/*.md` |
| 6. finalization（確定） | 指示済み修正反映、完成原稿 | 完成と公開可否を決める | `manuscript/*.md` |

### 通常の流れ
- `init` で作品を作り、AIが指定工程のファイルを作成する。
- `submit` は提出物の存在とハッシュを記録し、監督の判断待ちにする（**品質評価はしない**）。
- 総監督が確認後、`approve` または `return` を指示する。
- `approve` は次工程へ進む。執筆工程だけ `--continue-drafting` で次の執筆まとまりへ進める。
- `return` は修正依頼のみを記録。原稿は消さない。AIは監督の指示箇所を必要な範囲だけ修正する。
- 原稿が提出後に変更されていたら、承認前に再提出が必要。意図しないすり替えを防ぐため。
- 完了時も、自動投稿・公開・AIによる合否判定はしない。

### 監督承認の例

```bash
python tools/stories.py submit first-story
python tools/stories.py approve first-story --pick "案05" --note "この企画を採用" --confirm-director
python tools/stories.py submit first-story
python tools/stories.py return first-story --note "主人公の動機だけ見直して" --confirm-director
```

監督の判断は作品の `decisions.jsonl` に記録。CLIは認証システムではないため、`--confirm-director` をAIが勝手に指定してよいわけではない。

### 役割と作業範囲
- 企画AIは自由に発想できるが、候補を自分で採用しない。
- 脚本担当は物語の因果関係と構成を考える。三幕構成などを強制しない。
- 小説担当は台詞、地の文、沈黙や人物の反応に創作裁量を持つ。
- 正史候補は `canon/proposals.md` に置き、総監督の指示により確定資料へ反映する。
- Claude / ChatGPT間の引継ぎは `handoff.md` に、担当の章と未解決点を記す。
- 監督が承認した後の作業範囲内では、段落単位の確認を挟まずまとまって執筆する。

### 回帰・復元
- Gitの履歴で前の稿を保持する。原稿変更時は差分を残す。
- ハッシュによる提出固定は改稿指示によって解除される。自動破棄・強制リセットはしない。
- 品質や個性の判断を、数値評価、AI審査員、Elo、自動改稿ループに委ねない。

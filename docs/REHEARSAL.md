# 実証手順: Kneekura-Stories v0.2 機能試験

この文書は、**ソフトウェアの進行と人間主導の創作を分けて実証する**ための手順です。最初から長編を書く必要はありません。

## ステップ1 — 自動のオフライン通し試験（AI使用量ゼロ）

Python 3.10+ でリポジトリのルートから実行します。

```bash
python -m unittest discover -s tests -v
python tools/rehearse.py
```

`rehearse.py` は、テスト用に「総監督が決めた架空企画」「脚本」「二章の仮文」「Claude→ChatGPTの引継ぎ」を生成し、次を確認します。

1. AIのアイデア候補ファイルだけでは企画を提出できない。
2. 監督企画の記録、提出、模擬的な承認によって工程が進む。
3. **監督確認フラグを欠く承認は拒否される**（実際の本人認証ではない）。
4. ClaudeからChatGPTへ引継ぎ履歴を渡しても、提出状態が壊れない。
5. 提出後に資料を変更すると `doctor` が不一致を検出し、差戻し・再提出で復帰できる。
6. 執筆が一章で中断されても、次の執筆バッチへ進める。
7. 完成原稿に章が欠けた場合は提出を拒否する。
8. 二章が揃うと、最後まで状態遷移できる。

成功時はJSONで `"result": "PASS"` を出力します。**この試験では実際のClaudeもChatGPTも呼び出しません。監督の承認もテストデータの模擬操作です。**

生成されたテスト原稿や引継ぎ履歴を調べたい場合は、未作成の保存先を指定できます。

```bash
python tools/rehearse.py --output ./rehearsal-output
```

※ `rehearsal-output/` はGitから除外します。既存の保存先を上書きすることはありません。

## ステップ2 — 一作品を使った手動の実地試験（総監督の判断が必要）

### 作品の登録

```bash
python tools/stories.py init test-story --title "実地試験"
```

鴨川がClaudeまたはジョリーと**個別に相談して決めた企画だけ**を `works/test-story/ideas/director-brief.md` に記録する。AIは候補を自動で集めません。

```bash
python tools/stories.py doctor test-story
python tools/stories.py submit test-story
```

総監督自身の確認が済んだ場合にだけ、明示した承認の範囲で実行します。

```bash
python tools/stories.py approve test-story --note "監督が決めた企画を採用" --confirm-director
```

### ClaudeとChatGPTで担当を交代

Claude Codeに基礎設定を作ってもらい、`docs/WORKFLOW.md` に従って提出と監督承認を済ませた後、次のように引き継ぎます。

```bash
python tools/stories.py handoff test-story --from claude --to chatgpt --scope planning/scenes.md --summary "確定設定を確認した上でシーン案を作る。新設定は未確定提案として分ける"
```

引継ぎ内容は `handoff.md` と `handoffs.jsonl` に保存されます。ChatGPTには `AGENTS.md`、`state.json`、`handoff.md`、関連する設定資料を読ませます。必要なシーンを編集したら、GitHubのコミットや差分で確認します。

**同じ章を二つのAIに同時編集させない**こと。引継ぎは記録機能であって、技術的なファイルロックではありません。

### 動作を判定するポイント

- ClaudeとChatGPTが**同じ世界観・人物の正本**を参照できるか
- 先行担当の変更を、後任担当が意図せず消していないか
- 長い文章の途中で監督への確認を繰り返さず、合意したまとまりを執筆できるか
- 総監督の指示がない限り、確定原稿を変更したり新たな設定を正史化したりしないか
- `doctor` が正常・異常を区別できるか
- 作業後も別セッションで続きから再開できるか

### 重要な限界

- `--confirm-director` は本人認証ではありません。AIへの禁止指示と監督の実際の意思確認が必要です。
- ChatGPTからGitHubを編集できても、ChatGPTのセッションで必ずCLIが実行できるわけではありません。実行できない場合はファイル編集までを担当し、状態遷移はClaude Codeまたは人間が実行します。
- オフラインの成功は、AIの日本語小説の品質・Claude/ChatGPTの実際の連携・長編の安定性を証明しません。それらはステップ2で実証します。
- 未完成の原稿を自動採点・自動改稿・自動公開する機能はありません。

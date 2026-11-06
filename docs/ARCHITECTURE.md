# 設計とデータ所有権

## 一作品のフォルダ構造

```text
works/<slug>/
  project.json              # タイトル・作成日時
  state.json                # 現在工程・提出・進捗
  decisions.jsonl           # 総監督の判断履歴
  handoff.md                # Claude / ChatGPT間の引継ぎ
  ideas/director-brief.md   # 総監督が決めた企画（現行）
  ideas/candidates.md       # 旧・収集機能（無期限休止）
  ideas/selected.md         # 旧・選抜記録（無期限休止）
  planning/premise.md       # 企画の芯・テーマ
  planning/synopsis.md      # 結末までのあらすじ
  planning/outline.md       # 章別構成
  planning/scenes.md        # シーンカード
  planning/proposals.md     # 大きな変更の提案
  canon/world.md            # 確定した世界観
  canon/characters.md       # 確定人物・呼称・知識状態
  canon/foreshadowing.md    # 伏線と回収計画
  canon/proposals.md        # 新設定の提案（未確定）
  style/voice.md            # 作品固有の文体
  drafts/voice-tests.md     # 試作文章
  drafts/chapters/*.md      # 執筆中の各章
  manuscript/*.md           # 総監督確認済みの完成原稿
```

空の作品では、主要ファイルを自動作成しません。AIが工程ごとに作成した時点で提出条件を満たします。空のテンプレートが誤って採用されるのを防ぐためです。

## 真実の置き場
- 監督の決定: `decisions.jsonl` （追記専用）。企画内容の正本は `ideas/director-brief.md`。
- 自動アイデア収集・選抜は無期限休止。`IDEA_COLLECTION_ENABLED = False` は総監督の明示指示なしに変更しない。
- 作業進捗: `state.json` （`tools/stories.py` のみ更新）
- 世界観・人物・伏線の確定内容: `canon/` の正本（`proposals.md` は除外）
- 構成: `planning/`。原稿に合わせて無断で書き換えない。
- 作業原稿: `drafts/`。自動的に `manuscript/` へ昇格しない。

## 共有リポジトリでの競合防止
1. 同じ作品の同じ章を同時に複数AIへ割り振らない。
2. 担当分担を `handoff.md` に明記する。直近変更を先に確認する。
3. 大きな改稿では作業ブランチを分け、差分を総監督に示す。
4. 意図しない上書きが起きたら復旧方法を案内する。勝手な `git reset --hard` は禁止。

## チャットモデルとの接続方法
Claude Codeはローカルリポジトリでファイルを編集可能。ChatGPTはGitHub接続を使い、同じリポジトリのMarkdownファイルを読み書きできる。CLIを実行できないChatGPTセッションでは、CLIに依存する状態遷移を「実行済み」と偽らない。総監督の判断は明示指示に従って記録する。

## 実装方針
- AI推論の呼び出しはCLIに含めない。ChatGPT／Claude自身が制作を行う。
- Python標準ライブラリのみで進捗管理。外部APIキー、データベース、常駐サーバー不要。
- スクリプトはファイルの存在・整合性だけを検査し、文学的評価をしない。
- 総監督の承認を形式的に代替しない。`--confirm-director` は自動承認防止の操作確認であり、本人認証ではない。

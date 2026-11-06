#!/usr/bin/env python3
"""End-to-end offline rehearsal of the author-directed story workflow.

No model calls, no API keys, no actual director approval, no story publishing.
This uses simulated human approvals to exercise the software state machine.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import stories


def write(work: Path, path: str, content: str) -> None:
    dest = work / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")


def expect_rejected(action, message: str) -> None:
    try:
        action()
    except stories.StoryError:
        return
    raise AssertionError(message)


def rehearse(root: Path) -> dict:
    stages = []
    slug = "rehearsal"
    work = root / slug
    stories.init_project(slug, "制作システムの模擬作品", root)
    assert not stories.IDEA_COLLECTION_ENABLED, "AIによるアイデア収集を起動してはいけません"
    expect_rejected(lambda: stories.submit_project(slug, root), "監督の企画がないのに提出できた")
    write(work, "ideas/candidates.md", "旧機能の候補資料は、今は制作工程で利用できません。")
    expect_rejected(lambda: stories.submit_project(slug, root), "休止中の自動候補で提出できた")

    write(work, "ideas/director-brief.md",
          "# 監督の企画\n\n夜の図書室で、互いの名前を忘れた二人が古い地図を見つける。これは機能試験用の架空企画。")
    stories.submit_project(slug, root)
    expect_rejected(
        lambda: stories.approve_project(slug, "模擬承認", False, works_dir=root),
        "監督確認フラグなしで承認できた",
    )
    stories.approve_project(slug, "監督の模擬承認（テストデータ）", True, works_dir=root)
    stages.append("director brief → foundation")

    for file, body in (
        ("planning/premise.md", "# 概念\n\n夜の図書室を中心とした、名前と記憶をめぐる架空の小さな物語。"),
        ("canon/world.md", "# 世界観\n\n図書室には古い地図が保管されている。重要な追加設定は監督の承認が必要。"),
        ("canon/characters.md", "# 登場人物\n\n語り手と来訪者。両者の知識と呼称を独立して管理する。"),
    ):
        write(work, file, body)
    stories.submit_project(slug, root)
    stories.approve_project(slug, "基礎設計の模擬承認", True, works_dir=root)
    stages.append("foundation → outline")

    stories.handoff_project(
        slug, "claude", "chatgpt", "planning/scenes.md",
        "基礎設定と人物の知識状態を確認して場面の流れを設計する。", root
    )
    for file, body in (
        ("planning/synopsis.md", "# シノプシス\n\n二人は地図を探し、互いの記憶に異なる事実があると気づく。結末は地図を閉じて別れる。"),
        ("planning/outline.md", "# 構成\n\n第1章: 図書室。第2章: 地図の発見と別れ。今回の試験では二章とする。"),
        ("planning/scenes.md", "# 場面設計\n\n第一場面: 扉を開ける。第二場面: 地図を見つける。第三場面: 二人は別れる。"),
        ("canon/foreshadowing.md", "# 伏線\n\n第一章の地図の余白は第二章で意味が明らかになる。"),
    ):
        write(work, file, body)
    stories.submit_project(slug, root)
    write(work, "planning/scenes.md", "# 修正済み場面設計\n\n提出後の変更を意図的に再現する。差戻しから再提出できることを検査。")
    assert not stories.diagnose_project(slug, root)["ok"], "提出後の改変を見逃した"
    stories.return_project(slug, "模擬差戻し（状態回復の検証）", True, root)
    stories.submit_project(slug, root)
    stories.approve_project(slug, "脚本構成の模擬承認", True, works_dir=root)
    stages.append("outline → voice; stale submission recovered")

    for file, body in (
        ("drafts/voice-tests.md", "# 試作\n\n室内の静けさを直接語る版と、会話の間で感じさせる版を比べる。"),
        ("style/voice.md", "# 文体\n\n一人称。落ち着いた文体。短い台詞を自然に配置する。"),
    ):
        write(work, file, body)
    stories.submit_project(slug, root)
    stories.approve_project(slug, "文体の模擬承認", True, works_dir=root)
    stages.append("voice → drafting")

    write(work, "drafts/chapters/ch_01.md",
          "# 第一章\n\n扉を開けると、図書室には一人の少年がいた。彼は名前を言わず、窓に目を向けた。")
    stories.submit_project(slug, root)
    stories.approve_project(
        slug, "第一章の模擬承認・次の章へ", True, continue_drafting=True, works_dir=root
    )
    assert stories.show_state(slug, root)["stage"] == "drafting"
    expect_rejected(lambda: stories.submit_project(slug, root), "更新のない本文が再提出できた")
    stages.append("draft batch 1 → next batch")

    stories.handoff_project(
        slug, "claude", "chatgpt", "drafts/chapters/ch_02.md",
        "第二章を担当。第一章の人物の知識を確認し、総監督の承認なく結末を変更しない。", root
    )
    write(work, "drafts/chapters/ch_02.md",
          "# 第二章\n\n地図の端に二つの名前があった。少年はそれを指さし、何も言わずに図書室を出た。")
    stories.submit_project(slug, root)
    stories.approve_project(slug, "全章執筆の模擬承認", True, works_dir=root)
    stages.append("draft batch 2 → finalization")

    shutil.copy2(work / "drafts/chapters/ch_01.md", work / "manuscript/ch_01.md")
    expect_rejected(lambda: stories.submit_project(slug, root), "第二章が欠けた完成原稿を提出できた")
    shutil.copy2(work / "drafts/chapters/ch_02.md", work / "manuscript/ch_02.md")
    stories.submit_project(slug, root)
    stories.approve_project(slug, "完成稿の模擬承認（監督本人による判断ではない）", True, works_dir=root)
    assert stories.show_state(slug, root)["stage"] == "complete"
    assert stories.diagnose_project(slug, root)["ok"]
    stages.append("finalization → complete")

    handoffs = (work / "handoffs.jsonl").read_text(encoding="utf-8").splitlines()
    decisions = (work / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(handoffs) == 2 and len(decisions) == 8
    return {
        "result": "PASS",
        "scope": "offline workflow simulation only; Claude/ChatGPT API use and human approval not tested",
        "stage": "complete",
        "transitions": stages,
        "decision_records": len(decisions),
        "handoff_records": len(handoffs),
        "chapter_files": 2,
        "automatic_idea_collection": "indefinitely disabled",
        "path": str(work),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Kneekura-Stories全工程のオフライン模擬試験")
    p.add_argument("--output", type=Path, help="結果を保存する未作成のディレクトリ（省略時は一時領域）")
    args = p.parse_args()
    if args.output is not None:
        output = args.output.resolve()
        if output.exists():
            p.error("--output の保存先は新しいディレクトリにしてください（既存作品の保護）")
        output.mkdir(parents=True)
        print(json.dumps(rehearse(output), ensure_ascii=False, indent=2))
    else:
        with tempfile.TemporaryDirectory(prefix="kneekura-rehearsal-") as temporary:
            report = rehearse(Path(temporary))
            report["path"] = "(temporary directory deleted)"
            print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

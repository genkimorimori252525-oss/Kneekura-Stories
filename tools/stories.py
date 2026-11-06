#!/usr/bin/env python3
"""Kneekura-Stories: human-directed story workflow (stdlib only).

This program does not call AI models, grade prose, or revise manuscripts.
Submitting a stage freezes a content snapshot. Only an explicit director
decision can advance a stage. The --confirm-director flag is an operational
acknowledgement, NOT authentication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import PurePosixPath
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKS_DIR = REPO_ROOT / "works"
STAGES = ("ideation", "foundation", "outline", "voice", "drafting", "finalization")
# Indefinitely suspended: only a new explicit director decision can reactivate this.
IDEA_COLLECTION_ENABLED = False
REQUIRED = {
    "ideation": ("ideas/candidates.md",) if IDEA_COLLECTION_ENABLED else ("ideas/director-brief.md",),
    "foundation": ("planning/premise.md", "canon/world.md", "canon/characters.md"),
    "outline": (
        "planning/synopsis.md",
        "planning/outline.md",
        "planning/scenes.md",
        "canon/foreshadowing.md",
    ),
    "voice": ("drafts/voice-tests.md", "style/voice.md"),
    "drafting": ("drafts/chapters/*.md",),
    "finalization": ("manuscript/*.md",),
}
DIRECTORIES = (
    "ideas", "planning", "canon", "style", "drafts/chapters", "manuscript",
)


class StoryError(Exception):
    """Expected user-facing workflow error."""


def timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def story_dir(slug: str, works_dir: Path = WORKS_DIR) -> Path:
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,48}", slug):
        raise StoryError("作品IDは英小文字で始まる2〜49文字の英小文字・数字・ハイフンにしてください。")
    return works_dir / slug


def write_json(path: Path, value: dict) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def append_decision(work: Path, entry: dict) -> None:
    with (work / "decisions.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_state(work: Path) -> dict:
    path = work / "state.json"
    if not path.is_file():
        raise StoryError("作品がありません。先に init を実行してください。")
    return json.loads(path.read_text(encoding="utf-8"))


def init_project(slug: str, title: str, works_dir: Path = WORKS_DIR) -> dict:
    work = story_dir(slug, works_dir)
    if not title.strip():
        raise StoryError("作品タイトルは空にできません。")
    if work.exists():
        raise StoryError("同じ作品IDが既に存在します。既存作品は上書きしません。")
    work.mkdir(parents=True)
    for folder in DIRECTORIES:
        (work / folder).mkdir(parents=True, exist_ok=True)
    metadata = {"slug": slug, "title": title.strip(), "created_at": timestamp()}
    state = {
        "schema_version": 1,
        "stage": "ideation",
        "status": "working",
        "pending": None,
        "approved_stages": [],
        "drafting_batches_approved": 0,
        "last_draft_hash": None,
    }
    write_json(work / "project.json", metadata)
    write_json(work / "state.json", state)
    (work / "decisions.jsonl").write_text("", encoding="utf-8")
    (work / "handoff.md").write_text(
        "# 引継ぎ\n\n現在の担当: 未設定\n\n次の制作範囲: 総監督が決定した企画の記録（自動収集は無期限休止）\n\n未解決点: なし\n",
        encoding="utf-8",
    )
    return state


def _require_meaningful(path: Path) -> bool:
    return path.is_file() and len(path.read_text(encoding="utf-8").strip()) >= 16


def required_artifacts(work: Path, stage: str) -> tuple[list[Path], list[str]]:
    found: list[Path] = []
    missing: list[str] = []
    for pattern in REQUIRED[stage]:
        paths = sorted(p for p in work.glob(pattern) if _require_meaningful(p))
        if not paths:
            missing.append(pattern)
        else:
            found.extend(paths)
    return found, missing


def snapshot_hash(work: Path) -> str:
    """Hash story prose and planning files, not mutable state or handoff."""
    checksum = hashlib.sha256()
    for path in sorted(work.rglob("*.md")):
        if path.name == "handoff.md" or not path.is_file():
            continue
        relative = path.relative_to(work).as_posix()
        checksum.update(relative.encode("utf-8"))
        checksum.update(b"\0")
        checksum.update(path.read_bytes())
        checksum.update(b"\0")
    return checksum.hexdigest()


def draft_hash(work: Path) -> str:
    checksum = hashlib.sha256()
    for path in sorted((work / "drafts" / "chapters").glob("*.md")):
        checksum.update(path.name.encode("utf-8"))
        checksum.update(b"\0")
        checksum.update(path.read_bytes())
    return checksum.hexdigest()


def submit_project(slug: str, works_dir: Path = WORKS_DIR) -> dict:
    work = story_dir(slug, works_dir)
    state = load_state(work)
    if state["stage"] == "complete":
        raise StoryError("この作品は確定済みです。新しい指示で別途作業してください。")
    if state["status"] == "awaiting_director":
        raise StoryError("総監督の判断待ちです。資料を修正した場合は差戻しまたは新たな指示が必要です。")
    found, missing = required_artifacts(work, state["stage"])
    if missing:
        raise StoryError("提出に必要なファイルが不足しています: " + ", ".join(missing))
    if state["stage"] == "drafting" and draft_hash(work) == state.get("last_draft_hash"):
        raise StoryError("前回承認以降、章の本文が変わっていません。新しい執筆分を用意してください。")
    if state["stage"] == "finalization":
        draft_names = {p.name for p in (work / "drafts" / "chapters").glob("*.md") if _require_meaningful(p)}
        final_names = {p.name for p in (work / "manuscript").glob("*.md") if _require_meaningful(p)}
        missing_chapters = sorted(draft_names - final_names)
        if missing_chapters:
            raise StoryError("完成原稿に未収録の章があります: " + ", ".join(missing_chapters))
    state["pending"] = {
        "stage": state["stage"],
        "snapshot": snapshot_hash(work),
        "submitted_at": timestamp(),
        "artifacts": [p.relative_to(work).as_posix() for p in found],
    }
    state["status"] = "awaiting_director"
    write_json(work / "state.json", state)
    return state


def _pending_is_current(work: Path, state: dict, check_snapshot: bool = True) -> None:
    if state["status"] != "awaiting_director" or not state.get("pending"):
        raise StoryError("承認または差戻しできる提出物がありません。")
    if check_snapshot and state["pending"]["snapshot"] != snapshot_hash(work):
        raise StoryError("提出後に内容が変更されています。提出物を固定し直してから判断してください。")


def approve_project(
    slug: str,
    note: str,
    confirm_director: bool,
    pick: str | None = None,
    continue_drafting: bool = False,
    works_dir: Path = WORKS_DIR,
) -> dict:
    if not confirm_director:
        raise StoryError("総監督の明示指示が必要です（--confirm-director）。")
    if not note.strip():
        raise StoryError("承認理由または監督指示を --note で残してください。")
    work = story_dir(slug, works_dir)
    state = load_state(work)
    _pending_is_current(work, state)
    stage = state["stage"]
    if stage == "ideation" and IDEA_COLLECTION_ENABLED and not (pick and pick.strip()):
        raise StoryError("企画の採用IDを --pick で指定してください。")
    if pick and (stage != "ideation" or not IDEA_COLLECTION_ENABLED):
        raise StoryError("アイデア収集・自動選抜は無期限休止中です。--pickは使用できません。")
    if stage != "drafting" and continue_drafting:
        raise StoryError("--continue-drafting は本文執筆工程でのみ使えます。")

    append_decision(work, {
        "at": timestamp(),
        "type": "approved",
        "actor": "human_director",
        "stage": stage,
        "note": note.strip(),
        "selected_idea": pick.strip() if pick else None,
        "continue_drafting": continue_drafting,
        "submission_snapshot": state["pending"]["snapshot"],
    })
    if stage == "ideation" and IDEA_COLLECTION_ENABLED:
        (work / "ideas" / "selected.md").write_text(
            "# 総監督が採用した企画\n\nID: " + pick.strip() +
            "\n\n監督指示: " + note.strip() + "\n", encoding="utf-8"
        )
    if stage == "drafting":
        state["drafting_batches_approved"] += 1
        state["last_draft_hash"] = draft_hash(work)
    if stage != "drafting" or not continue_drafting:
        state["approved_stages"].append(stage)
        index = STAGES.index(stage)
        state["stage"] = STAGES[index + 1] if index + 1 < len(STAGES) else "complete"
    state["pending"] = None
    state["status"] = "complete" if state["stage"] == "complete" else "working"
    write_json(work / "state.json", state)
    return state


def return_project(
    slug: str, note: str, confirm_director: bool, works_dir: Path = WORKS_DIR
) -> dict:
    if not confirm_director:
        raise StoryError("総監督の明示指示が必要です（--confirm-director）。")
    if not note.strip():
        raise StoryError("差戻しの理由を --note で残してください。")
    work = story_dir(slug, works_dir)
    state = load_state(work)
    # Stale submissions can be returned, otherwise the project gets stuck.
    _pending_is_current(work, state, check_snapshot=False)
    append_decision(work, {
        "at": timestamp(),
        "type": "returned",
        "actor": "human_director",
        "stage": state["stage"],
        "note": note.strip(),
        "submission_snapshot": state["pending"]["snapshot"],
        "changed_since_submission": state["pending"]["snapshot"] != snapshot_hash(work),
    })
    state["pending"] = None
    state["status"] = "working"
    write_json(work / "state.json", state)
    return state


def handoff_project(
    slug: str, source: str, target: str, scope: str, summary: str,
    works_dir: Path = WORKS_DIR,
) -> dict:
    """Record a human-readable transfer without advancing the workflow.

    Advisory only: Git/GitHub branch discipline is still required to avoid
    simultaneous edits to the same prose file.
    """
    participants = {"claude", "chatgpt", "director"}
    if source not in participants or target not in participants or source == target:
        raise StoryError("引継ぎ元・先は claude/chatgpt/director の異なる担当を指定してください。")
    if not summary.strip():
        raise StoryError("引継ぎの要点を --summary で指定してください。")
    if len(summary) > 5000:
        raise StoryError("引継ぎ内容が長すぎます。5000文字以内にしてください。")
    normalized = scope.replace("\\", "/").strip("/")
    path = PurePosixPath(normalized)
    if (
        not normalized or path.is_absolute()
        or ".." in path.parts or "." in path.parts
        or not normalized.startswith(("ideas/", "planning/", "canon/", "style/", "drafts/", "manuscript/"))
    ):
        raise StoryError("対象範囲は作品内の相対パスで指定してください。")
    work = story_dir(slug, works_dir)
    state = load_state(work)
    entry = {
        "at": timestamp(),
        "from": source,
        "to": target,
        "scope": normalized,
        "summary": summary.strip(),
        "stage": state["stage"],
        "status": state["status"],
    }
    with (work / "handoffs.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps(entry, ensure_ascii=False) + "\n")
    (work / "handoff.md").write_text(
        "# 最新の引継ぎ\n\n"
        f"- 担当: {source} → {target}\n"
        f"- 工程: {state['stage']}\n"
        f"- 対象: `{normalized}`\n"
        f"- 引継ぎ内容: {summary.strip()}\n\n"
        "確定資料と原稿は勝手に上書きせず、対象ファイルの最新差分を確認すること。\n",
        encoding="utf-8",
    )
    return entry


def diagnose_project(slug: str, works_dir: Path = WORKS_DIR) -> dict:
    """Software integrity checks only. Never a judge of literary quality."""
    work = story_dir(slug, works_dir)
    state = load_state(work)
    errors = []
    warnings = []
    stage = state.get("stage")
    status = state.get("status")
    if stage not in STAGES + ("complete",):
        errors.append("不明な工程です。")
    if status not in ("working", "awaiting_director", "complete"):
        errors.append("不明な状態です。")
    if (stage == "complete") != (status == "complete"):
        errors.append("完了工程と状態が一致しません。")
    pending = state.get("pending")
    if status == "awaiting_director":
        if not isinstance(pending, dict) or pending.get("stage") != stage:
            errors.append("提出状態が不整合です。")
        elif pending.get("snapshot") != snapshot_hash(work):
            errors.append("提出後に資料が変更されています。差戻しと再提出が必要です。")
    elif pending is not None:
        errors.append("提出待ちでない状態に提出物が残っています。")
    if stage == "ideation" and not IDEA_COLLECTION_ENABLED:
        if not _require_meaningful(work / "ideas" / "director-brief.md"):
            warnings.append("総監督の企画ブリーフはまだ登録されていません。")
    if stage in ("finalization", "complete"):
        draft_files = {p.name for p in (work / "drafts" / "chapters").glob("*.md") if _require_meaningful(p)}
        final_files = {p.name for p in (work / "manuscript").glob("*.md") if _require_meaningful(p)}
        if not draft_files.issubset(final_files):
            errors.append("完成原稿に未収録の章があります: " + ", ".join(sorted(draft_files - final_files)))
    if not (work / "decisions.jsonl").is_file():
        errors.append("監督決定の記録ファイルがありません。")
    if not (work / "handoff.md").is_file():
        warnings.append("引継ぎ資料がありません。")
    return {"slug": slug, "ok": not errors, "errors": errors, "warnings": warnings,
            "stage": stage, "status": status}


def show_state(slug: str, works_dir: Path = WORKS_DIR) -> dict:
    work = story_dir(slug, works_dir)
    state = load_state(work)
    title = json.loads((work / "project.json").read_text(encoding="utf-8"))["title"]
    found, missing = ([], []) if state["stage"] == "complete" else required_artifacts(work, state["stage"])
    return {
        "slug": slug,
        "title": title,
        **state,
        "artifacts_present": [p.relative_to(work).as_posix() for p in found],
        "artifacts_missing": missing,
    }


def list_projects(works_dir: Path = WORKS_DIR) -> list[dict]:
    if not works_dir.exists():
        return []
    result = []
    for child in sorted(works_dir.iterdir()):
        if child.is_dir() and (child / "state.json").is_file():
            result.append(show_state(child.name, works_dir))
    return result


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kneekura-Stories 監督主導の制作管理")
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init", help="新規作品")
    init.add_argument("slug")
    init.add_argument("--title", required=True)
    sub.add_parser("list", help="作品一覧")
    handoff = sub.add_parser("handoff", help="Claude/ChatGPT間の担当引継ぎを記録")
    handoff.add_argument("slug")
    handoff.add_argument("--from", dest="source", required=True, choices=("claude", "chatgpt", "director"))
    handoff.add_argument("--to", dest="target", required=True, choices=("claude", "chatgpt", "director"))
    handoff.add_argument("--scope", required=True)
    handoff.add_argument("--summary", required=True)
    doctor = sub.add_parser("doctor", help="制作状態の整合性を確認（文学的評価なし）")
    doctor.add_argument("slug")
    for name in ("status", "submit", "approve", "return"):
        command = sub.add_parser(name)
        command.add_argument("slug")
        if name in ("approve", "return"):
            command.add_argument("--note", required=True)
            command.add_argument("--confirm-director", action="store_true")
        if name == "approve":
            command.add_argument("--pick")
            command.add_argument("--continue-drafting", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.action == "init":
            output = init_project(args.slug, args.title)
        elif args.action == "list":
            output = list_projects()
        elif args.action == "status":
            output = show_state(args.slug)
        elif args.action == "handoff":
            output = handoff_project(args.slug, args.source, args.target, args.scope, args.summary)
        elif args.action == "doctor":
            output = diagnose_project(args.slug)
        elif args.action == "submit":
            output = submit_project(args.slug)
        elif args.action == "approve":
            output = approve_project(
                args.slug, args.note, args.confirm_director, args.pick, args.continue_drafting
            )
        else:
            output = return_project(args.slug, args.note, args.confirm_director)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if args.action == "doctor" and not output["ok"] else 0
    except (StoryError, OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())

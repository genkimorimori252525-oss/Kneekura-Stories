"""Offline regression tests for human-directed story workflow."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "stories.py"
SPEC = importlib.util.spec_from_file_location("kneekura_stories", SOURCE)
stories = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stories)


class StoriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        stories.init_project("my-story", "試験用小説", self.root)
        self.work = self.root / "my-story"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, text="長めの原稿です。これは提出のための十分な文章です。"):
        path = self.work / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_init_and_status(self):
        info = stories.show_state("my-story", self.root)
        self.assertEqual(info["stage"], "ideation")
        self.assertEqual(info["status"], "working")
        self.assertEqual(info["artifacts_missing"], ["ideas/candidates.md"])

    def test_reject_existing_and_path_traversal(self):
        with self.assertRaises(stories.StoryError):
            stories.init_project("my-story", "上書き", self.root)
        with self.assertRaises(stories.StoryError):
            stories.init_project("../private", "不正", self.root)

    def test_cannot_submit_without_artifact(self):
        with self.assertRaises(stories.StoryError):
            stories.submit_project("my-story", self.root)

    def test_director_only_approval(self):
        self.write("ideas/candidates.md")
        stories.submit_project("my-story", self.root)
        with self.assertRaises(stories.StoryError):
            stories.approve_project("my-story", "採用", False, "案01", works_dir=self.root)
        with self.assertRaises(stories.StoryError):
            stories.approve_project("my-story", "採用", True, works_dir=self.root)
        state = stories.approve_project("my-story", "採用", True, "案01", works_dir=self.root)
        self.assertEqual(state["stage"], "foundation")
        self.assertIn("案01", (self.work / "ideas/selected.md").read_text(encoding="utf-8"))
        self.assertEqual(
            json.loads((self.work / "decisions.jsonl").read_text(encoding="utf-8").splitlines()[0])["actor"],
            "human_director",
        )

    def test_snapshot_changes_block_approval(self):
        self.write("ideas/candidates.md")
        stories.submit_project("my-story", self.root)
        self.write("ideas/candidates.md", "提出後に内容を更新しました。変更された企画候補です。")
        with self.assertRaises(stories.StoryError):
            stories.approve_project("my-story", "採用", True, "案01", works_dir=self.root)

    def test_return_preserves_draft(self):
        self.write("ideas/candidates.md")
        stories.submit_project("my-story", self.root)
        state = stories.return_project("my-story", "次を調整", True, self.root)
        self.assertEqual(state["stage"], "ideation")
        self.assertEqual(state["status"], "working")
        self.assertTrue((self.work / "ideas/candidates.md").exists())

    def reach_drafting(self):
        self.write("ideas/candidates.md")
        stories.submit_project("my-story", self.root)
        stories.approve_project("my-story", "この企画", True, "案01", works_dir=self.root)
        for stage in ("foundation", "outline", "voice"):
            for pattern in stories.REQUIRED[stage]:
                self.write(pattern)
            stories.submit_project("my-story", self.root)
            stories.approve_project("my-story", stage + " 承認", True, works_dir=self.root)

    def test_drafting_batch_continue_and_finish(self):
        self.reach_drafting()
        self.assertEqual(stories.show_state("my-story", self.root)["stage"], "drafting")
        self.write("drafts/chapters/ch_01.md")
        stories.submit_project("my-story", self.root)
        state = stories.approve_project(
            "my-story", "次の章へ", True, continue_drafting=True, works_dir=self.root
        )
        self.assertEqual(state["stage"], "drafting")
        self.assertEqual(state["drafting_batches_approved"], 1)
        with self.assertRaises(stories.StoryError):
            stories.submit_project("my-story", self.root)
        self.write("drafts/chapters/ch_02.md")
        stories.submit_project("my-story", self.root)
        state = stories.approve_project("my-story", "完成工程へ", True, works_dir=self.root)
        self.assertEqual(state["stage"], "finalization")
        self.write("manuscript/ch_01.md")
        self.write("manuscript/ch_02.md")
        stories.submit_project("my-story", self.root)
        state = stories.approve_project("my-story", "完成を承認", True, works_dir=self.root)
        self.assertEqual(state["status"], "complete")
        self.assertEqual(state["stage"], "complete")

    def test_wrong_stage_flags_are_rejected(self):
        self.write("ideas/candidates.md")
        stories.submit_project("my-story", self.root)
        with self.assertRaises(stories.StoryError):
            stories.approve_project(
                "my-story", "採用", True, "案01", continue_drafting=True, works_dir=self.root
            )

    def test_project_list(self):
        entries = stories.list_projects(self.root)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["slug"], "my-story")


if __name__ == "__main__":
    unittest.main()

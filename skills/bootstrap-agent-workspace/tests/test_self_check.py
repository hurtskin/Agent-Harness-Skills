from __future__ import annotations

import importlib.util
import io
import shutil
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "self_check.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_self_check", MODULE_PATH)
assert SPEC and SPEC.loader
self_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(self_check)


class SelfCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = Path(__file__).resolve().parents[1]

    def copy_skill(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name) / "bootstrap-agent-workspace"
        shutil.copytree(self.source_root, root)
        return temporary, root

    def test_repository_contract_is_valid(self) -> None:
        self.assertEqual([], self_check.validate(self.source_root))

    def test_missing_indexed_file_is_reported(self) -> None:
        temporary, root = self.copy_skill()
        self.addCleanup(temporary.cleanup)
        (root / "modules" / "kanban.md").unlink()

        errors = self_check.check_required_files(root)

        self.assertTrue(any("modules/kanban.md" in error for error in errors))

    def test_broken_relative_markdown_link_is_reported(self) -> None:
        temporary, root = self.copy_skill()
        self.addCleanup(temporary.cleanup)
        (root / "README.md").write_text("[missing](./no-such-file.md)\n", encoding="utf-8")

        errors = self_check.check_markdown_links(root)

        self.assertEqual(["无效 Markdown 相对链接: README.md -> ./no-such-file.md"], errors)

    def test_fact_source_drift_is_reported(self) -> None:
        temporary, root = self.copy_skill()
        self.addCleanup(temporary.cleanup)
        skill = root / "SKILL.md"
        skill.write_text(
            skill.read_text(encoding="utf-8").replace("、`BACKLOG.md`", ""),
            encoding="utf-8",
        )

        errors = self_check.check_fact_sources(root)

        self.assertTrue(any("SKILL.md" in error for error in errors))

    def test_configure_output_encoding_uses_utf8(self) -> None:
        class ConfigurableStream(io.StringIO):
            configured: tuple[str, str] | None = None

            def reconfigure(self, *, encoding: str, errors: str) -> None:
                self.configured = (encoding, errors)

        stdout = ConfigurableStream()
        stderr = ConfigurableStream()
        original_stdout, original_stderr = self_check.sys.stdout, self_check.sys.stderr
        self.addCleanup(setattr, self_check.sys, "stdout", original_stdout)
        self.addCleanup(setattr, self_check.sys, "stderr", original_stderr)
        self_check.sys.stdout = stdout
        self_check.sys.stderr = stderr

        self_check.configure_output_encoding()

        self.assertEqual(("utf-8", "backslashreplace"), stdout.configured)
        self.assertEqual(("utf-8", "backslashreplace"), stderr.configured)


if __name__ == "__main__":
    unittest.main()

import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from kentaro.api.demo import read_packaged_demo
from kentaro.cli import main
from kentaro.workspace import (
    _managed_instruction_block,
    _managed_instruction_digest,
    _content_digest,
    maysano_config_path,
    maysano_environment_path,
    timestamped_output,
    workspace_path,
)


class FixedDateTime:
    @classmethod
    def now(cls, _timezone):
        return datetime(2026, 10, 17, 12, 0, 0, tzinfo=timezone.utc)


class DefaultCliTests(unittest.TestCase):
    def test_packaged_demo_resource_is_available_without_repository_examples(self):
        resource = files("kentaro.resources").joinpath("demo-portfolio.json")
        self.assertTrue(resource.is_file())
        context = read_packaged_demo()
        self.assertEqual(context["scope"], "portfolio-demo")
        self.assertTrue(all(record["source_ref"].startswith("demo:") for record in context["records"]))

    def test_demo_runs_without_config_or_http_and_writes_timestamped_dashboard(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr), patch("kentaro.api.live.urlopen") as urlopen:
                    code = main(["demo"])
                self.assertEqual(code, 0)
                self.assertEqual(stderr.getvalue(), "")
                self.assertIn("Kentaro synthetic demo", stdout.getvalue())
                self.assertIn("# Portfolio brief", stdout.getvalue())
                dashboard = Path(next(line.removeprefix("Dashboard: ") for line in stdout.getvalue().splitlines() if line.startswith("Dashboard: ")))
                self.assertTrue(dashboard.is_file())
                self.assertTrue(dashboard.is_relative_to((Path(directory) / ".kentaro" / "workspace").resolve()))
                self.assertIn("demo:obj-1", dashboard.read_text(encoding="utf-8"))
                urlopen.assert_not_called()
            finally:
                os.chdir(previous)

    def test_portfolio_brief_defaults_to_packaged_demo_without_http(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr), patch("kentaro.api.live.urlopen") as urlopen:
                    code = main(["portfolio", "brief"])
                self.assertEqual(code, 0)
                self.assertEqual(stderr.getvalue(), "")
                self.assertIn("synthetic demo fixture", stdout.getvalue())
                self.assertIn("demo:obj-1", stdout.getvalue())
                self.assertTrue((Path(directory) / ".kentaro" / "workspace").is_dir())
                urlopen.assert_not_called()
            finally:
                os.chdir(previous)

    def test_dashboard_defaults_to_unique_timestamped_local_outputs_without_http(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                outputs = []
                with patch("kentaro.api.live.urlopen") as urlopen:
                    for _ in range(2):
                        stdout = io.StringIO()
                        with redirect_stdout(stdout):
                            self.assertEqual(main(["dashboard"]), 0)
                        outputs.append(Path(stdout.getvalue().strip()))
                self.assertNotEqual(outputs[0], outputs[1])
                self.assertTrue(all(output.is_file() for output in outputs))
                self.assertTrue(all(output.is_relative_to((Path(directory) / ".kentaro" / "workspace").resolve()) for output in outputs))
                urlopen.assert_not_called()
            finally:
                os.chdir(previous)

    def test_timestamped_output_never_selects_an_existing_file(self):
        with TemporaryDirectory() as directory, patch("kentaro.workspace.datetime", FixedDateTime):
            workspace = Path(directory)
            first = timestamped_output(workspace, "portfolio-dashboard", ".html")
            first.write_text("existing", encoding="utf-8")
            second = timestamped_output(workspace, "portfolio-dashboard", ".html")
        self.assertNotEqual(first, second)
        self.assertTrue(second.name.endswith("-1.html"))

    def test_guided_maysano_setup_keeps_key_local_and_validates_before_writing(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                stdout = io.StringIO()
                with redirect_stdout(stdout), patch("kentaro.cli.getpass.getpass", return_value="test-key"):
                    self.assertEqual(main(["configure", "maysano", "--api-base-url", "https://example.test/api", "--scope", "pilot-scope"]), 0)
                workspace = workspace_path()
                self.assertTrue(maysano_config_path(workspace).is_file())
                self.assertTrue(maysano_environment_path(workspace).is_file())
                self.assertNotIn("test-key", stdout.getvalue())
                self.assertIn("API_KEY=test-key", maysano_environment_path(workspace).read_text(encoding="utf-8"))

                with redirect_stderr(io.StringIO()), patch("kentaro.cli.getpass.getpass", return_value="replacement-key"):
                    self.assertEqual(main(["configure", "maysano", "--api-base-url", "http://not-https", "--scope", "pilot-scope", "--replace"]), 2)
                self.assertIn("API_KEY=test-key", maysano_environment_path(workspace).read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)

    def test_setup_codex_installs_all_skills_and_is_idempotent(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(["setup", "codex"]), 0)
                instructions = Path(directory) / "AGENTS.md"
                self.assertTrue(instructions.is_file())
                installed_instructions = instructions.read_text(encoding="utf-8")
                self.assertIn("Kentaro local business-design workspace", installed_instructions)
                self.assertIn("First business prompt", installed_instructions)
                self.assertIn("kentaro design\npropose", installed_instructions)
                self.assertIn("Open the visual canvas in Codex beside the conversation", installed_instructions)
                self.assertIn("refresh or reopen that same canvas in Codex", installed_instructions)
                self.assertIn('"replaced": false', stdout.getvalue())
                self.assertIn('"fresh_codex_conversation_required": true', stdout.getvalue())
                self.assertIn("start a new Codex conversation", stdout.getvalue())
                skills = Path(directory) / ".agents" / "skills"
                self.assertEqual(len(list(skills.glob("*/SKILL.md"))), 13)
                repeated = io.StringIO()
                with redirect_stdout(repeated):
                    self.assertEqual(main(["setup", "codex"]), 0)
                self.assertIn('"instruction_status": "reused"', repeated.getvalue())
                self.assertIn('"reused": 1', repeated.getvalue())
            finally:
                os.chdir(previous)

    def test_setup_codex_upgrades_an_unmodified_legacy_managed_instruction_block(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                instructions = Path(directory) / "AGENTS.md"
                legacy = _managed_instruction_block().replace(
                    "Open the visual canvas in Codex beside the conversation as the default companion to the\nfirst proposal; do not merely provide a file link and leave the learner to open it. ",
                    "",
                )
                with patch("kentaro.workspace.LEGACY_UNMODIFIED_MANAGED_INSTRUCTION_HASHES", {_managed_instruction_digest(legacy.rstrip("\n"))}):
                    instructions.write_text(legacy, encoding="utf-8")
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(main(["setup", "codex"]), 0)
                self.assertIn("Open the visual canvas in Codex beside the conversation", instructions.read_text(encoding="utf-8"))
                self.assertIn('"instruction_status": "upgraded_managed"', stdout.getvalue())
            finally:
                os.chdir(previous)

    def test_setup_codex_upgrades_only_an_unmodified_legacy_skill(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                self.assertEqual(main(["setup", "codex"]), 0)
                skill = Path(directory) / ".agents" / "skills" / "kentaro-objective-design" / "SKILL.md"
                legacy = b"# exact legacy skill\n"
                skill.write_bytes(legacy)
                with patch(
                    "kentaro.workspace.LEGACY_UNMODIFIED_SKILL_FILE_HASHES",
                    {"kentaro-objective-design/SKILL.md": frozenset({_content_digest(legacy)})},
                ):
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        self.assertEqual(main(["setup", "codex"]), 0)
                self.assertIn("The learner should see the updated business target", skill.read_text(encoding="utf-8"))
                self.assertIn('"upgraded_unmodified": 1', stdout.getvalue())
            finally:
                os.chdir(previous)

    def test_setup_codex_preserves_existing_instructions_and_changed_skill_without_replace(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                instructions = Path(directory) / "AGENTS.md"
                instructions.write_text("# My team instructions\nKeep our review rule.\n", encoding="utf-8")
                self.assertEqual(main(["setup", "codex"]), 0)
                self.assertIn("Keep our review rule.", instructions.read_text(encoding="utf-8"))
                skill = Path(directory) / ".agents" / "skills" / "kentaro-objective-design" / "SKILL.md"
                skill.write_text("# Learner change\n", encoding="utf-8")
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(main(["setup", "codex"]), 0)
                self.assertEqual(skill.read_text(encoding="utf-8"), "# Learner change\n")
                self.assertIn('"preserved_modified": 1', stdout.getvalue())
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["setup", "codex", "--replace"]), 0)
                self.assertIn("# Kentaro Business Objective Design", skill.read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)

    def test_doctor_reports_actionable_setup_and_odps_results(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                missing = io.StringIO()
                with redirect_stdout(missing), redirect_stderr(io.StringIO()):
                    self.assertEqual(main(["doctor"]), 2)
                missing_result = json.loads(missing.getvalue())
                self.assertFalse(missing_result["valid"])
                self.assertTrue(missing_result["fixes"])
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(main(["setup", "codex"]), 0)
                healthy = io.StringIO()
                with redirect_stdout(healthy):
                    self.assertEqual(main(["doctor"]), 0)
                result = json.loads(healthy.getvalue())
                self.assertTrue(result["valid"])
                skills = next(check for check in result["checks"] if check["name"] == "kentaro_skills")
                self.assertEqual(skills["detail"], "13/13 installed")
                self.assertEqual(next(check for check in result["checks"] if check["name"] == "design_portfolio")["status"], "not_started")
                self.assertEqual(next(check for check in result["checks"] if check["name"] == "codex_conversation_reload")["status"], "action_required")
                self.assertEqual(next(check for check in result["checks"] if check["name"] == "visual_canvas")["status"], "ok")
            finally:
                os.chdir(previous)

    def test_setup_codex_never_replaces_a_symbolic_link(self):
        with TemporaryDirectory() as directory:
            previous = Path.cwd()
            os.chdir(directory)
            try:
                linked_file = Path(directory) / "existing-instructions.md"
                linked_file.write_text("keep this file", encoding="utf-8")
                (Path(directory) / "AGENTS.md").symlink_to(linked_file)
                with redirect_stderr(io.StringIO()):
                    self.assertEqual(main(["setup", "codex", "--replace"]), 2)
                self.assertEqual(linked_file.read_text(encoding="utf-8"), "keep this file")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()

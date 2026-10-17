import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from kentaro.cli import main


class DataProductCliTests(unittest.TestCase):
    def test_local_draft_uses_safe_workspace_output_and_records_provenance(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "warehouse-notes.md"
            source.write_text("# Warehouse capacity\n\nDocumented source facts.", encoding="utf-8")
            previous = Path.cwd()
            os.chdir(root)
            calls = []

            def sdk_run(command, *, environment):
                calls.append((command, environment))
                if "generate" in command:
                    output = Path(command[command.index("--output") + 1])
                    output.mkdir(parents=True, exist_ok=True)
                    (output / "warehouse-capacity.yaml").write_text("apiVersion: v1\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

            try:
                stdout = io.StringIO()
                with redirect_stdout(stdout), patch("kentaro.data_products._require_sdk"), patch("kentaro.data_products._run", side_effect=sdk_run):
                    self.assertEqual(main(["data-product", "draft", str(source)]), 0)
            finally:
                os.chdir(previous)

            result = json.loads(stdout.getvalue())
            output = Path(result["output"]["directory"])
            self.assertTrue(output.is_relative_to((root / ".kentaro" / "workspace" / "products").resolve()))
            self.assertTrue((output / "warehouse-capacity.yaml").is_file())
            self.assertEqual(result["provider"], "ollama")
            self.assertFalse(result["content_egress"])
            self.assertIn("--provider", calls[0][0])
            self.assertEqual(calls[0][0][calls[0][0].index("--provider") + 1], "ollama")
            self.assertEqual(calls[0][0][calls[0][0].index("--ollama-url") + 1], "http://127.0.0.1:11434")
            self.assertEqual(calls[0][1]["OPEN_DATA_PRODUCTS_ACTIVITY_LOG_PATH"], str((root / ".kentaro" / "workspace" / "sdk" / "activity.log").resolve()))
            evidence = root / ".kentaro" / "workspace" / "evidence" / "data-product-drafts.jsonl"
            record = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual(record["source"]["path"], str(source.resolve()))
            self.assertEqual(len(record["source"]["sha256"]), 64)

    def test_hosted_generation_requires_explicit_content_egress_acknowledgement(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "brief.txt"
            source.write_text("Sensitive business context", encoding="utf-8")
            previous = Path.cwd()
            os.chdir(root)
            try:
                with redirect_stderr(io.StringIO()), patch("kentaro.data_products._require_sdk"), patch("kentaro.data_products._run") as run:
                    self.assertEqual(main(["data-product", "draft", str(source), "--provider", "openai", "--config", "provider.yaml"]), 2)
                run.assert_not_called()
                self.assertFalse((root / ".kentaro" / "workspace" / "products").exists())
            finally:
                os.chdir(previous)

    def test_local_provider_rejects_a_non_loopback_ollama_url(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "brief.txt"
            source.write_text("Business context", encoding="utf-8")
            with redirect_stderr(io.StringIO()), patch("kentaro.data_products._require_sdk"), patch("kentaro.data_products._run") as run:
                self.assertEqual(main(["data-product", "draft", str(source), "--ollama-url", "https://remote.example"]), 2)
            run.assert_not_called()

    def test_use_case_and_objective_drafts_use_their_odps_kinds_and_workspace_paths(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "brief.md"
            source.write_text("Business context", encoding="utf-8")
            previous = Path.cwd()
            os.chdir(root)
            calls = []

            def sdk_run(command, *, environment):
                calls.append(command)
                if "generate" in command:
                    output = Path(command[command.index("--output") + 1])
                    (output / "draft.yaml").write_text("apiVersion: v1\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

            try:
                with patch("kentaro.data_products._require_sdk"), patch("kentaro.data_products._run", side_effect=sdk_run):
                    for command, expected_kind, expected_directory in (
                        ("use-case", "use-case", "use-cases"),
                        ("objective", "objective", "objectives"),
                    ):
                        stdout = io.StringIO()
                        with redirect_stdout(stdout):
                            self.assertEqual(main([command, "draft", str(source)]), 0)
                        result = json.loads(stdout.getvalue())
                        self.assertEqual(result["artifact_type"], command)
                        self.assertIn(f"/.kentaro/workspace/{expected_directory}/", result["output"]["directory"])
                        generate = next(call for call in calls if "generate" in call and call[call.index("--kind") + 1] == expected_kind)
                        self.assertEqual(generate[generate.index("--kind") + 1], expected_kind)
            finally:
                os.chdir(previous)

    def test_use_case_and_objective_validation_are_local_only(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "draft.yaml"
            artifact.write_text("apiVersion: v1\n", encoding="utf-8")
            calls = []

            def sdk_run(command, *, environment):
                calls.append(command)
                return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

            for command_name in ("use-case", "objective"):
                stdout = io.StringIO()
                with redirect_stdout(stdout), patch("kentaro.data_products._require_sdk"), patch("kentaro.data_products._run", side_effect=sdk_run):
                    self.assertEqual(main([command_name, "validate", str(artifact)]), 0)
                result = json.loads(stdout.getvalue())
                self.assertEqual(result["artifact_type"], command_name)
                self.assertTrue(result["artifact"]["valid"])
            self.assertTrue(all("validate" in command for command in calls))


if __name__ == "__main__":
    unittest.main()

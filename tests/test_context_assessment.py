import io
import json
import os
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from kentaro.cli import main
from kentaro.context import assess_context, render_context_report, write_context_assessment


COMPLETE_SOURCE = """# Service-assistant policy

## Definitions
An eligible request means a request with a case identifier.

## Principle
In practice, staff use the case identifier to locate the request.

The assistant must request a case identifier unless an approved exception applies.
The AI assistant prepares a draft and a human approves every customer response.

Owner: Service Operations
Version: 1.2
Next review: 2027-01-01

## Test cases
Expected behaviour: ask for a missing case identifier.
"""


class ContextAssessmentTests(unittest.TestCase):
    def test_assessment_cites_observed_indicators_and_recommends_level_four_for_agent_use(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "policy.md"
            source.write_text(COMPLETE_SOURCE, encoding="utf-8")
            assessment = assess_context(source, intended_use="Guide an agent workflow")

        self.assertTrue(assessment["local_only"])
        self.assertEqual(assessment["assessment"]["current_level"]["level"], 4)
        self.assertEqual(assessment["assessment"]["recommended_target_level"]["level"], 4)
        self.assertTrue(all(item["status"] == "observed" for item in assessment["assessment"]["findings"]))
        self.assertTrue(all(item["evidence"] for item in assessment["assessment"]["findings"]))
        self.assertIn("line", render_context_report(assessment))

    def test_absent_indicators_remain_source_limited_not_organisational_claims(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "notes.txt"
            source.write_text("Do useful work promptly.\n", encoding="utf-8")
            assessment = assess_context(source, intended_use="Answer questions")

        findings = {item["dimension"]: item for item in assessment["assessment"]["findings"]}
        self.assertEqual(assessment["assessment"]["current_level"]["level"], 1)
        self.assertEqual(assessment["assessment"]["recommended_target_level"]["level"], 2)
        self.assertEqual(findings["terminology"]["status"], "needs_review")
        self.assertEqual(findings["verification"]["status"], "not_evident")
        self.assertIn("may exist elsewhere", " ".join(assessment["limitations"]))

    def test_higher_level_indicators_cannot_skip_missing_lower_level_indicators(self):
        source_text = """# Policy
The AI must prepare a draft unless a human approves an exception.
Owner: Operations
Version: 1
Test case: exception.
"""
        with TemporaryDirectory() as directory:
            source = Path(directory) / "policy.md"
            source.write_text(source_text, encoding="utf-8")
            assessment = assess_context(source, intended_use="Guide an agent")
        self.assertEqual(assessment["assessment"]["current_level"]["level"], 1)

    def test_report_escapes_source_text_with_markdown_table_delimiters(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "policy.md"
            source.write_text("# Policy | v1\nAI must ask a human.\n", encoding="utf-8")
            assessment = assess_context(source, intended_use="Answer questions | route exceptions")
        report = render_context_report(assessment)
        self.assertIn("Policy \\| v1", report)
        self.assertIn("questions \\| route", report)

    def test_assessment_rejects_non_text_inputs(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "policy.pdf"
            source.write_bytes(b"not a real pdf")
            with self.assertRaisesRegex(ValueError, "convert other formats"):
                assess_context(source, intended_use="Answer questions")

    def test_writer_refuses_to_overwrite_existing_assessment(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "policy.md"
            source.write_text(COMPLETE_SOURCE, encoding="utf-8")
            assessment = assess_context(source, intended_use="Answer questions")
            outputs = write_context_assessment(assessment, root / "output")
            self.assertTrue(Path(outputs["json"]).is_file())
            self.assertTrue(Path(outputs["report"]).is_file())
            with self.assertRaisesRegex(ValueError, "already exists"):
                write_context_assessment(assessment, root / "output")

    def test_cli_writes_fresh_local_artifacts_without_network(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "policy.md"
            source.write_text(COMPLETE_SOURCE, encoding="utf-8")
            previous = Path.cwd()
            os.chdir(root)
            try:
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main(["context", "assess", "--input", str(source), "--intended-use", "Answer staff questions"])
                self.assertEqual(code, 0)
                self.assertEqual(stderr.getvalue(), "")
                result = json.loads(stdout.getvalue())
                self.assertTrue(result["local_only"])
                self.assertEqual(result["recommended_target_level"], 2)
                self.assertTrue(Path(result["json"]).is_file())
                self.assertTrue(Path(result["report"]).is_file())
                self.assertTrue(Path(result["output_dir"]).is_relative_to((root / ".kentaro" / "workspace").resolve()))
            finally:
                os.chdir(previous)

    def test_cli_rejects_output_outside_local_workspace(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "policy.md"
            source.write_text(COMPLETE_SOURCE, encoding="utf-8")
            previous = Path.cwd()
            os.chdir(root)
            try:
                with redirect_stderr(io.StringIO()):
                    code = main(["context", "assess", "--input", str(source), "--intended-use", "Answer questions", "--output-dir", str(root / "outside")])
            finally:
                os.chdir(previous)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

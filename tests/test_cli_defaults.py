import io
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
from kentaro.workspace import maysano_config_path, maysano_environment_path, timestamped_output, workspace_path


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


if __name__ == "__main__":
    unittest.main()

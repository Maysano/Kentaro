"""Release smoke test for the package-first local experience."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import tomllib
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_VERSION = tomllib.loads((REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]


class DistributionInstallTests(unittest.TestCase):
    def test_clean_wheel_install_runs_all_default_commands_without_network(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            environment = root / "environment"
            working_directory = root / "working-directory"
            network_guard = root / "network-guard"
            working_directory.mkdir()
            network_guard.mkdir()
            (network_guard / "sitecustomize.py").write_text(
                "import socket\n"
                "def _blocked(*args, **kwargs):\n"
                "    raise AssertionError('default Kentaro commands must not use the network')\n"
                "socket.create_connection = _blocked\n",
                encoding="utf-8",
            )

            supplied_wheel = os.environ.get("KENTARO_DISTRIBUTION_WHEEL")
            wheels = [Path(supplied_wheel)] if supplied_wheel else sorted((REPOSITORY_ROOT / "dist").glob(f"kentaro-{PACKAGE_VERSION}-*.whl"))
            if not wheels or not wheels[-1].is_file():
                self.skipTest("Build the current wheel with `python -m build` before running the distribution-install smoke test")
            self.assertEqual(wheels[-1].name, f"kentaro-{PACKAGE_VERSION}-py3-none-any.whl")
            self._run([sys.executable, "-m", "venv", str(environment)])
            pip = environment / "bin" / "pip"
            kentaro = environment / "bin" / "kentaro"
            self._run([str(pip), "install", "--no-index", str(wheels[-1])])

            guarded_environment = dict(os.environ, PYTHONPATH=str(network_guard))
            demo = self._run([str(kentaro), "demo"], cwd=working_directory, env=guarded_environment)
            brief = self._run([str(kentaro), "portfolio", "brief"], cwd=working_directory, env=guarded_environment)
            dashboard = self._run([str(kentaro), "dashboard"], cwd=working_directory, env=guarded_environment)
            codex_setup = self._run([str(kentaro), "setup", "codex"], cwd=working_directory, env=guarded_environment)
            design = self._run([str(kentaro), "design", "init", "--title", "Clean install design", "--portfolio-id", "clean-install", "--output", ".kentaro/workspace/design/clean.json"], cwd=working_directory, env=guarded_environment)
            masterclass = self._run([str(kentaro), "masterclass", "init", "--output", ".kentaro/workspace/masterclass/clean.json"], cwd=working_directory, env=guarded_environment)

            self.assertIn("Kentaro synthetic demo", demo.stdout)
            self.assertIn("synthetic demo fixture", brief.stdout)
            dashboard_path = Path(dashboard.stdout.strip())
            workspace = working_directory / ".kentaro" / "workspace"
            self.assertTrue(workspace.is_dir())
            self.assertTrue(dashboard_path.is_file())
            self.assertTrue(dashboard_path.is_relative_to(workspace.resolve()))
            self.assertGreaterEqual(len(list(workspace.glob("portfolio-dashboard-*.html"))), 2)
            self.assertIn('"codex_instructions"', codex_setup.stdout)
            self.assertIn("Kentaro local business-design workspace", (working_directory / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn('"model": "DesignPortfolio"', design.stdout)
            self.assertIn('"maysano_connection": false', masterclass.stdout)
            self.assertTrue((workspace / "design/clean.json").is_file())
            self.assertTrue((workspace / "masterclass/clean.json").is_file())
            self.assertTrue((workspace / "masterclass/customer-profile.odps.yaml").is_file())
            self.assertTrue((workspace / "masterclass/customer-profile-repair.odps.yaml").is_file())
            installed_scenario = environment / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages" / "kentaro" / "scenarios" / "udemy_masterclass"
            self.assertTrue((installed_scenario / "customer-risk-intelligence.json").is_file())
            self.assertTrue((installed_scenario / "checkpoints.json").is_file())
            self.assertTrue((installed_scenario / "README.md").is_file())
            self.assertTrue((installed_scenario / "facilitator-answer-key.md").is_file())
            installed_share = environment / "share" / "kentaro"
            self.assertTrue((installed_share / "docs" / "design-portfolio.md").is_file())
            self.assertTrue((installed_share / "docs" / "masterclass-companion.md").is_file())
            for skill in ("kentaro-objective-design", "kentaro-use-case-design", "kentaro-ai-product-design", "kentaro-data-product-design", "kentaro-portfolio-analysis", "kentaro-portfolio-readiness"):
                self.assertTrue((installed_share / "skills" / skill / "SKILL.md").is_file())

    def _run(self, command, *, cwd=None, env=None):
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode:
            self.fail(
                f"Command failed ({result.returncode}): {command!r}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
        return result


if __name__ == "__main__":
    unittest.main()

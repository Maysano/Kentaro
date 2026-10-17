"""Release smoke test for the package-first local experience."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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

            wheels = sorted((REPOSITORY_ROOT / "dist").glob("kentaro-*.whl"))
            if not wheels:
                self.skipTest("Build a wheel with `python -m build` before running the distribution-install smoke test")
            self._run([sys.executable, "-m", "venv", str(environment)])
            pip = environment / "bin" / "pip"
            kentaro = environment / "bin" / "kentaro"
            self._run([str(pip), "install", "--no-index", str(wheels[-1])])

            guarded_environment = dict(os.environ, PYTHONPATH=str(network_guard))
            demo = self._run([str(kentaro), "demo"], cwd=working_directory, env=guarded_environment)
            brief = self._run([str(kentaro), "portfolio", "brief"], cwd=working_directory, env=guarded_environment)
            dashboard = self._run([str(kentaro), "dashboard"], cwd=working_directory, env=guarded_environment)

            self.assertIn("Kentaro synthetic demo", demo.stdout)
            self.assertIn("synthetic demo fixture", brief.stdout)
            dashboard_path = Path(dashboard.stdout.strip())
            workspace = working_directory / ".kentaro" / "workspace"
            self.assertTrue(workspace.is_dir())
            self.assertTrue(dashboard_path.is_file())
            self.assertTrue(dashboard_path.is_relative_to(workspace.resolve()))
            self.assertGreaterEqual(len(list(workspace.glob("portfolio-dashboard-*.html"))), 2)

    def _run(self, command, *, cwd=None, env=None):
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )


if __name__ == "__main__":
    unittest.main()

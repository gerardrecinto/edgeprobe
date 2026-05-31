from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "host-snapshot"


class CliTests(unittest.TestCase):
    def test_terminal_output_matches_demo_shape(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "edgeprobe", "analyze", str(FIXTURE)],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("edgeprobe", result.stdout)
        self.assertIn("ACTION REQUIRED", result.stdout)
        self.assertIn("Kubernetes readiness is blocking delivery", result.stdout)

    def test_json_output_is_machine_readable(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "edgeprobe", "analyze", str(FIXTURE), "--output", "json"],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn('"status": "ACTION REQUIRED"', result.stdout)
        self.assertIn('"container_orchestration"', result.stdout)


if __name__ == "__main__":
    unittest.main()


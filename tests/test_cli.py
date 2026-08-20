from pathlib import Path
import subprocess
import sys
import tempfile
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

    def test_fail_on_info_still_blocks_on_the_fixture(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "edgeprobe", "analyze", str(FIXTURE), "--fail-on", "info"],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)

    def test_fail_on_critical_passes_when_only_info_signals_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            snapshot_dir = Path(tmp) / "gpu-only"
            snapshot_dir.mkdir()
            (snapshot_dir / "lspci.txt").write_text(
                "65:00.0 VGA compatible controller: NVIDIA Corporation GA102GL [RTX A5000]\n"
            )

            default_result = subprocess.run(
                [sys.executable, "-m", "edgeprobe", "analyze", str(snapshot_dir)],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )
            info_result = subprocess.run(
                [sys.executable, "-m", "edgeprobe", "analyze", str(snapshot_dir), "--fail-on", "info"],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(default_result.returncode, 0)
        self.assertEqual(info_result.returncode, 2)


if __name__ == "__main__":
    unittest.main()


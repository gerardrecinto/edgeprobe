from pathlib import Path
import unittest

from edgeprobe.parsers import load_snapshot


FIXTURE = Path(__file__).parent / "fixtures" / "host-snapshot"


class SnapshotParserTests(unittest.TestCase):
    def test_loads_kernel_cpu_gpu_and_wireless_context(self) -> None:
        snapshot = load_snapshot(FIXTURE)

        self.assertEqual(snapshot.kernel_release, "6.6.32-edge-rt")
        self.assertIn("Intel", snapshot.cpu_model or "")
        self.assertEqual(len(snapshot.gpu_devices), 1)
        self.assertTrue(snapshot.wireless_lines)

    def test_missing_snapshot_reports_clear_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_snapshot(FIXTURE / "missing")


if __name__ == "__main__":
    unittest.main()


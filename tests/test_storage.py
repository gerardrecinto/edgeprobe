from pathlib import Path
import unittest

from edgeprobe.classifier import classify
from edgeprobe.models import Category, Severity
from edgeprobe.parsers import load_snapshot

FIXTURES = Path(__file__).parent / "fixtures"


def storage_signals(name: str):
    report = classify(load_snapshot(FIXTURES / name))
    return report, [s for s in report.signals if s.category in (Category.STORAGE, Category.NETWORK_PATH)]


class StorageTests(unittest.TestCase):
    def test_degraded_node_is_action_required(self) -> None:
        report, signals = storage_signals("storage-degraded")
        titles = {s.title: s for s in signals}

        self.assertEqual(report.status, "ACTION REQUIRED")
        self.assertEqual(titles["Software RAID array is degraded"].severity, Severity.CRITICAL)
        self.assertIn("[4/3] [U_UU]", titles["Software RAID array is degraded"].evidence)
        self.assertEqual(titles["ZFS pool is not healthy"].severity, Severity.CRITICAL)
        self.assertEqual(titles["A bond member link is down"].severity, Severity.WARN)
        self.assertIn("ens1f1", titles["A bond member link is down"].evidence)

    def test_bad_nfs_options_are_listed(self) -> None:
        _, signals = storage_signals("storage-degraded")
        nfs = next(s for s in signals if s.title.startswith("NFS mount options"))
        for part in ("soft mount", "version below 4", "UDP", "32768"):
            self.assertIn(part, nfs.evidence)

    def test_healthy_node_has_no_storage_signals(self) -> None:
        report, signals = storage_signals("storage-healthy")

        self.assertEqual(signals, [])
        self.assertEqual(report.status, "READY")
        for check in ("md raid health", "nfs mount options", "bond link state", "zfs pool health"):
            self.assertIn(check, report.passed_checks)

    def test_rebuild_without_degraded_status_is_a_warning(self) -> None:
        from edgeprobe.models import Snapshot

        snap = Snapshot(name="x", kernel_release="k", kernel_cmdline="c", mdstat_lines=(
            "md0 : active raid10 a[0] b[1]",
            "1 blocks [2/2] [UU]",
            "[=>...]  resync = 40.0% (1/2) finish=1min speed=1K/sec",
        ))
        raid = [s for s in classify(snap).signals if s.category == Category.STORAGE]
        self.assertEqual([s.severity for s in raid], [Severity.WARN])

    def test_existing_snapshot_is_unchanged(self) -> None:
        report = classify(load_snapshot(FIXTURES / "host-snapshot"))
        self.assertFalse([s for s in report.signals if s.category == Category.STORAGE])


if __name__ == "__main__":
    unittest.main()

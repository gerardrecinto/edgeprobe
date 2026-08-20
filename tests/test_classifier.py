from pathlib import Path
import unittest

from edgeprobe.classifier import classify
from edgeprobe.models import Category, Severity, Snapshot
from edgeprobe.parsers import load_snapshot


FIXTURE = Path(__file__).parent / "fixtures" / "host-snapshot"


class ClassifierTests(unittest.TestCase):
    def test_fixture_surfaces_role_relevant_signals(self) -> None:
        report = classify(load_snapshot(FIXTURE))

        categories = {signal.category for signal in report.signals}
        self.assertIn(Category.DEVICE_DRIVER, categories)
        self.assertIn(Category.CONTAINER_ORCHESTRATION, categories)
        self.assertIn(Category.NETWORK_PATH, categories)
        self.assertIn(Category.CELLULAR_WIFI, categories)
        self.assertIn(Category.GPU_CPU_HETEROGENEOUS, categories)
        self.assertEqual(report.status, "ACTION REQUIRED")
        self.assertGreaterEqual(report.confidence, 0.85)

    def test_critical_driver_timeout_is_not_smoothed_to_warning(self) -> None:
        report = classify(load_snapshot(FIXTURE))
        driver = next(signal for signal in report.signals if signal.category == Category.DEVICE_DRIVER)

        self.assertEqual(driver.severity, Severity.CRITICAL)
        self.assertIn("timeout", driver.evidence.lower())

    def test_signals_are_sorted_critical_first(self) -> None:
        report = classify(load_snapshot(FIXTURE))

        ranks = {Severity.CRITICAL: 0, Severity.WARN: 1, Severity.INFO: 2}
        severities = [ranks[signal.severity] for signal in report.signals]
        self.assertEqual(severities, sorted(severities))

    def test_strong_cellular_signal_is_not_flagged_weak(self) -> None:
        snapshot = Snapshot(
            name="strong-signal",
            wireless_lines=("wwan0 lte rsrp=-85 rsrq=-9 sinr=15 handover=0",),
        )

        report = classify(snapshot)

        self.assertNotIn(Category.CELLULAR_WIFI, {signal.category for signal in report.signals})

    def test_weak_cellular_signal_is_still_flagged(self) -> None:
        snapshot = Snapshot(
            name="weak-signal",
            wireless_lines=("wwan0 lte rsrp=-118 rsrq=-16 sinr=-2 handover=3",),
        )

        report = classify(snapshot)

        self.assertIn(Category.CELLULAR_WIFI, {signal.category for signal in report.signals})


if __name__ == "__main__":
    unittest.main()


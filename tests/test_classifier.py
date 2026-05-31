from pathlib import Path
import unittest

from edgeprobe.classifier import classify
from edgeprobe.models import Category, Severity
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


if __name__ == "__main__":
    unittest.main()


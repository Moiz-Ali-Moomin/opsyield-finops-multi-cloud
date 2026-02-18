
import unittest
from datetime import datetime, timedelta, timezone
from opsyield.analysis.idle_scoring import IdleScorer
from opsyield.analysis.waste_detector import WasteDetector

class TestWastefinding(unittest.TestCase):
    def setUp(self):
        import inspect
        print(f"DEBUG: IdleScorer file: {inspect.getfile(IdleScorer)}")
        self.idle_scorer = IdleScorer()
        self.waste_detector = WasteDetector()

    def test_idle_scoring_stopped_but_costly(self):
        resource = {
            "name": "stopped-instance",
            "state": "terminated",
            "cost_30d": 100.0,
            "external_ip": "1.2.3.4", # has IP, so checking cost logic
            "type": "compute",
            "days_running": 0
        }
        score = self.idle_scorer.calculate_score(resource)
        # Should be high because it's stopped but costs money
        print(f"Score for stopped costly resource: {score}")
        self.assertTrue(score >= 50)

    def test_idle_scoring_dev_keyword(self):
        resource = {
            "name": "dev-test-vm",
            "state": "running",
            "days_running": 5,
            "external_ip": None, # +20
        }
        score = self.idle_scorer.calculate_score(resource)
        print(f"Score for dev resource: {score}")
        self.assertTrue(score >= 40) # 20 for name + 20 for no IP

    def test_waste_detector_zombie(self):
        resources = [{
            "name": "zombie-disk",
            "state": "stopped",
            "cost_30d": 50.0,
            "type": "disk",
            "created_at": datetime.now(timezone.utc) - timedelta(days=10)
        }]
        # Ensure no external IP is not the only reason
        waste = self.waste_detector.detect(resources)
        print(f"Waste detected: {waste}")
        self.assertEqual(len(waste), 1)
        reasons_str = "; ".join(waste[0]["reasons"])
        self.assertIn("Stopped but incurring cost", reasons_str)

    def test_waste_detector_old_tmp(self):
        resources = [{
            "name": "tmp-vm",
            "state": "running",
            "cost_30d": 10.0,
            "type": "compute",
            "created_at": datetime.now(timezone.utc) - timedelta(days=20) # > 14 days
        }]
        waste = self.waste_detector.detect(resources)
        print(f"Waste detected: {waste}")
        self.assertEqual(len(waste), 1)
        reasons_str = "; ".join(waste[0]["reasons"])
        self.assertIn("Temporary resource running for", reasons_str)

if __name__ == '__main__':
    unittest.main()

"""Small code-level sanity tests. Not a proof of physical MPPT performance."""
import csv
import tempfile
import unittest
from pathlib import Path
from mppt_reference.analysis import summarize_csv
from mppt_reference.core import Sample, PerturbObserve, estimated_power, limit_pwm


class ReferenceTest(unittest.TestCase):
    def test_pwm_bounds(self):
        self.assertEqual(limit_pwm(-100), 0)
        self.assertEqual(limit_pwm(300), 255)
        self.assertEqual(limit_pwm(128), 128)

    def test_power_calculation(self):
        self.assertAlmostEqual(estimated_power(4.0, 255), 0.4)
        self.assertAlmostEqual(estimated_power(4.0, 0), 0)
        with self.assertRaises(ValueError):
            estimated_power(4.0, 255, 0)

    def test_serial_csv(self):
        line = "1000,50,80,8.60000,0.02000,0.04500,2,6"
        sample = Sample.from_csv_line(line)
        self.assertEqual(sample.angle_deg, 50)
        self.assertEqual(sample.sweep_id, 6)
        self.assertIsNone(Sample.from_csv_line("hello Arduino"))

    def test_po_direction(self):
        obj = PerturbObserve(initial_pwm=80, step_size=4)
        self.assertEqual(obj.update(0.20), 80)
        self.assertEqual(obj.update(0.30), 84)
        self.assertEqual(obj.update(0.25), 80)
        obj.recommend(100)
        self.assertEqual(obj.update(0.40), 100)

    def test_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "sample.csv"
            with path.open("w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["pwm", "estimated_power_w"])
                writer.writeheader()
                writer.writerows([{"pwm": 10, "estimated_power_w": 0.2},
                                  {"pwm": 20, "estimated_power_w": 0.6}])
            out = summarize_csv(path)
            self.assertAlmostEqual(out["mean_power_w"], 0.4)
            self.assertAlmostEqual(out["power_range_w"], 0.4)
            self.assertAlmostEqual(out["mean_pwm"], 15)


if __name__ == "__main__":
    unittest.main()

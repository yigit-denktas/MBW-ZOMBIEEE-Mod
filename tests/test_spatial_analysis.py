import unittest, tempfile, json
from pathlib import Path
from telemetry.spatial_analysis import analyze, write_outputs

class SpatialAnalysisTests(unittest.TestCase):
    def test_analyze_and_outputs(self):
        points = []
        for i in range(4):
            points.append({"tick": i, "ts_ms": 1000 * i, "agent_id": i % 2,
                           "team": i % 2, "x": 10, "y": 10,
                           "dx": 5 if i else None, "dy": 0, "wave": 1,
                           "round": 0, "hp": 90, "class_id": 1})
        heartbeats = [
            {"tick": 1, "ts_ms": 1000, "wave": 1, "round": 0,
             "alive0": 1, "alive1": 3},
            {"tick": 2, "ts_ms": 2000, "wave": 1, "round": 0,
             "alive0": 3, "alive1": 1},
        ]
        data = {"schema": "zombieee.heatmap-input.v1", "run": {},
                "points": points, "heartbeats": heartbeats,
                "agents": {"0": {"team": 0, "movement_total": 5, "samples": 2},
                           "1": {"team": 1, "movement_total": 20, "samples": 2}},
                "gaps": []}
        result = analyze(data)
        self.assertEqual(result["points"], 4)
        self.assertTrue(result["occupancy"])
        self.assertTrue(result["chokepoint_candidates"])
        self.assertIn("outnumbered",
                      [p["situation"] for p in result["situations"]])
        self.assertTrue(result["movement"]["classes"])
        with tempfile.TemporaryDirectory() as td:
            out = write_outputs(result, Path(td))
            self.assertTrue(Path(out["json"]).is_file())
            self.assertTrue(Path(out["markdown"]).is_file())

    def test_empty_input_reports_gap(self):
        result = analyze({"schema": "zombieee.heatmap-input.v1",
                          "run": {}, "points": [], "heartbeats": [], "gaps": []})
        self.assertEqual(result["points"], 0)
        self.assertIn("spatial_has_no_points", result["gaps"])

if __name__ == "__main__":
    unittest.main()

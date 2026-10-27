"""PKG-103 Pages dependency-impact panel checks.

Scope
-----
* ``SnapshotIntegrityTests`` prove the committed ``progress/dependency-impact.json``
  is byte-identical to a fresh projection of ``progress/ledger.json`` and carries
  the structural summary, top blockers, cycles and explicit ``schedule_unknown``
  gap. No duration/effort/float/CPM field is invented.
* ``StaticMarkupTests`` guard the panel hooks, wording and table semantics.
* ``PublisherTests`` prove ``tools/publish_tracker.py`` copies the snapshot to
  the gh-pages tree and fails closed when it is missing.
* ``BrowserImpactTests`` drive ``site/index.html`` in headless Chrome over a
  local HTTP server: panel visible, stat numbers and table rows match the JSON,
  narrow reflow stays inside the page, and a missing snapshot degrades visibly
  instead of silently.

What these tests do NOT establish: deployment to the real gh-pages branch,
screen-reader speech, rendered-pixel contrast, or any acceptance claim.
Browser tests skip (never pass) when Playwright or a Chrome/Edge channel is
unavailable.
"""
import contextlib
import functools
import http.server
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_impact_snapshot import (  # noqa: E402
    SNAPSHOT_SCHEMA,
    build_snapshot,
    render_snapshot,
)

sys.path.insert(0, str(ROOT / "tools"))
from publish_tracker import PUBLISHED, main as publish_main  # noqa: E402

LEDGER = ROOT / "progress" / "ledger.json"
SNAPSHOT = ROOT / "progress" / "dependency-impact.json"
PAGE = ROOT / "site" / "index.html"
SCHEDULE_WORDING = "Schedule unknown — no durations, effort, float, or CPM"

PROBES = (
    "/site/progress/ledger.json",
    "/site/progress/dependency-impact.json",
    "/site/progress/publish-time.json",
    "/site/progress/publish-meta.json",
    "/site/progress/live-status.json",
)


def load_snapshot():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


class SnapshotIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_snapshot()
        cls.expected = build_snapshot(LEDGER)

    def test_committed_snapshot_matches_fresh_projection(self):
        self.assertEqual(SNAPSHOT.read_text(encoding="utf-8"),
                         render_snapshot(self.expected),
                         "progress/dependency-impact.json is stale; run "
                         "`python tools/build_impact_snapshot.py`")

    def test_snapshot_contract_fields(self):
        snapshot = self.snapshot
        self.assertEqual(snapshot["schema"], SNAPSHOT_SCHEMA)
        self.assertEqual(snapshot["report_schema"], "zombieee.dependency-impact.v1")
        self.assertEqual(snapshot["generated_by"], "tools/build_impact_snapshot.py")
        summary = snapshot["summary"]
        for key in ("items", "dependencies", "open", "impacted", "blocked",
                    "cycles", "consequential_blockers"):
            self.assertIsInstance(summary[key], int, key)
        self.assertEqual(summary["impacted"], self.expected["summary"]["impacted"])
        self.assertEqual(snapshot["blockers_total"],
                         self.expected["blockers_total"])
        self.assertEqual(snapshot["blockers_total"],
                         summary["consequential_blockers"])
        self.assertEqual(len(snapshot["top_blockers"]),
                         min(snapshot["top_blockers_limit"],
                             snapshot["blockers_total"]))
        self.assertEqual(len(snapshot["cycles"]), summary["cycles"])
        self.assertEqual(len(snapshot["top_blockers"]), 10)
        for row in snapshot["top_blockers"]:
            for key in ("rank", "id", "title", "state", "open_transitive_dependents_count",
                        "direct_dependents_count",
                        "required_open_transitive_dependents_count"):
                self.assertIn(key, row)

    def test_schedule_unknown_gap_is_explicit(self):
        snapshot = self.snapshot
        schedule = snapshot["schedule"]
        self.assertEqual(schedule["status"], "unknown")
        for flag in ("durations_used", "effort_estimated", "float_computed",
                     "cpm_computed"):
            self.assertFalse(schedule[flag], flag)
        self.assertEqual(schedule["fields_unavailable"],
                         ["duration", "effort", "start", "finish", "float",
                          "critical_path"])
        gaps = {gap["code"]: gap for gap in snapshot["gaps"]}
        self.assertIn("schedule_unknown", gaps)
        gap = gaps["schedule_unknown"]
        self.assertIn("duration", gap["details"]["fields_unavailable"])
        self.assertIn("no duration", gap["message"])
        self.assertFalse(gap["details"]["cpm_computed"])

    def test_top_blockers_are_ranked_by_open_downstream_work(self):
        rows = self.snapshot["top_blockers"]
        self.assertEqual([row["rank"] for row in rows],
                         list(range(1, len(rows) + 1)))
        opens = [row["open_transitive_dependents_count"] for row in rows]
        self.assertEqual(opens, sorted(opens, reverse=True))
        self.assertGreater(opens[0], 0, "top blocker should have open downstream work")

    def test_snapshot_has_no_local_absolute_paths(self):
        text = SNAPSHOT.read_text(encoding="utf-8")
        self.assertEqual(self.snapshot["source"]["path"], "progress/ledger.json")
        self.assertNotIn("C:\\\\", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("\\\\Users\\\\", text)


class StaticMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_panel_hooks_and_wording(self):
        for needle in (
            'id="dependency-impact"',
            'id="impact-heading"',
            'id="impact-status"',
            'role="status"',
            'aria-live="polite"',
            'id="impact-schedule"',
            'id="impact-items"',
            'id="impact-open"',
            'id="impact-impacted"',
            'id="impact-blockers"',
            'id="impact-cycle-count"',
            'id="impact-dependencies"',
            'id="impact-scroll"',
            'id="impact-blockers-table"',
            'id="impact-blockers-body"',
            'id="impact-cycles-note"',
            'id="impact-gaps"',
            'id="impact-source"',
            'progress/dependency-impact.json',
            SCHEDULE_WORDING,
        ):
            self.assertIn(needle, self.html, needle)

    def test_table_has_accessible_headers(self):
        for header in ("Open downstream", "Direct downstream", "Required open"):
            self.assertIn(header, self.html)
        self.assertIn('aria-label="Top consequential blockers by open downstream work"',
                      self.html)
        self.assertIn('aria-label="Top consequential blockers table, scrollable"',
                      self.html)

    def test_panel_makes_no_schedule_or_acceptance_claim(self):
        lowered = self.html.lower()
        self.assertIn("structural analysis only", lowered)
        self.assertIn("done</code> is not acceptance", lowered)
        self.assertNotIn("critical path estimate", lowered)
        self.assertNotIn("<script src=", self.html, "no third-party scripts")


class PublisherTests(unittest.TestCase):
    def _fixture(self, temp):
        root = Path(temp) / "root"
        pages = Path(temp) / "pages"
        for rel in PUBLISHED:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if rel.endswith("ledger.json"):
                target.write_text(json.dumps({
                    "contractVersion": "0.2.0",
                    "items": [{"id": "A", "state": "done"}],
                    "milestones": [],
                }), encoding="utf-8")
            elif rel.endswith(".json"):
                target.write_text(json.dumps({"stub": rel}), encoding="utf-8")
            else:
                target.write_text("<!doctype html><title>stub</title>\n",
                                  encoding="utf-8")
        snapshot_text = '{"schema":"stub-impact"}\n'
        (root / "progress" / "dependency-impact.json").write_text(
            snapshot_text, encoding="utf-8")
        return root, pages, snapshot_text

    def _publish(self, root, pages, sha="a" * 40):
        argv = ["publish_tracker.py", "--root", str(root),
                "--gh-pages", str(pages), "--source-sha", sha]
        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(io.StringIO()):
                return publish_main()

    def test_publish_copies_impact_snapshot_to_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            root, pages, snapshot_text = self._fixture(temp)
            self.assertEqual(self._publish(root, pages), 0)
            self.assertEqual((pages / "progress" / "dependency-impact.json")
                             .read_text(encoding="utf-8"), snapshot_text)
            self.assertTrue((pages / "index.html").is_file())
            self.assertTrue((pages / "progress" / "ledger.json").is_file())
            meta = json.loads((pages / "progress" / "publish-meta.json")
                              .read_text(encoding="utf-8"))
            self.assertEqual(meta["source_sha"], "a" * 40)
            self.assertEqual(meta["work_items"], 1)

    def test_publish_fails_closed_without_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root, pages, _snapshot = self._fixture(temp)
            (root / "progress" / "dependency-impact.json").unlink()
            with self.assertRaises(SystemExit) as caught:
                self._publish(root, pages)
            self.assertIn("dependency-impact.json", str(caught.exception))
            self.assertFalse((pages / "index.html").exists(),
                             "publisher must not copy a partial gh-pages tree")


# ------------------------------------------------------------------- browser
try:
    from playwright.sync_api import sync_playwright
    HAVE_PLAYWRIGHT = True
except Exception:  # pragma: no cover - environment dependent
    HAVE_PLAYWRIGHT = False


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_PLAYWRIGHT:
            raise unittest.SkipTest("Playwright not installed; DOM checks not run (UNKNOWN)")
        cls.snapshot = load_snapshot()
        cls.httpd = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        try:
            cls.pw = sync_playwright().start()
        except Exception as exc:
            cls.httpd.shutdown()
            raise unittest.SkipTest("Playwright browser driver unavailable: " + str(exc))
        cls.browser = None
        for channel in ("chrome", "msedge", None):
            try:
                cls.browser = (cls.pw.chromium.launch(channel=channel, headless=True)
                               if channel else cls.pw.chromium.launch(headless=True))
                break
            except Exception:
                continue
        if cls.browser is None:
            cls.pw.stop()
            cls.httpd.shutdown()
            raise unittest.SkipTest("No Chrome/Edge available; DOM checks not run (UNKNOWN)")
        cls.url = f"http://127.0.0.1:{cls.port}/site/index.html"

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "browser", None):
            cls.browser.close()
        if getattr(cls, "pw", None):
            cls.pw.stop()
        if getattr(cls, "httpd", None):
            cls.httpd.shutdown()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 1000})
        self.errors, self.bad_responses = [], []
        self.page.on("pageerror", lambda exc: self.errors.append(str(exc)))
        self.page.on("console", lambda msg: self.errors.append(msg.text)
                     if msg.type == "error" else None)
        self.page.on("response", lambda res: self.bad_responses.append((res.status, res.url))
                     if res.status >= 400 else None)
        self.page.goto(self.url, wait_until="load")
        self.page.wait_for_function(
            "() => document.getElementById('impact-status').textContent.includes('loaded')",
            timeout=15000)

    def tearDown(self):
        unexpected = [(status, url) for status, url in self.bad_responses
                      if not any(url.endswith(probe) for probe in PROBES)]
        network_errors = [text for text in self.errors
                          if "Failed to load resource" not in text]
        self.page.close()
        self.assertEqual(unexpected, [], "unexpected failed responses")
        self.assertEqual(network_errors, [], "browser/JavaScript errors")

    def test_panel_visible_and_numbers_match_snapshot(self):
        summary = self.snapshot["summary"]
        self.assertTrue(self.page.is_visible("#dependency-impact"))
        self.assertIn(SCHEDULE_WORDING,
                      self.page.inner_text("#impact-schedule"))

        shown = self.page.evaluate("""() => Object.fromEntries(
            ['impact-items','impact-open','impact-impacted','impact-blockers',
             'impact-cycle-count','impact-dependencies'].map(id =>
                [id, document.getElementById(id).textContent.trim()]))""")
        self.assertEqual(shown, {
            "impact-items": str(summary["items"]),
            "impact-open": str(summary["open"]),
            "impact-impacted": str(summary["impacted"]),
            "impact-blockers": str(summary["consequential_blockers"]),
            "impact-cycle-count": str(summary["cycles"]),
            "impact-dependencies": str(summary["dependencies"]),
        })

        rows = self.page.eval_on_selector_all(
            "#impact-blockers-body tr",
            "els => els.map(tr => [...tr.children].map(td => td.textContent.trim()))")
        expected = self.snapshot["top_blockers"][:5]
        self.assertEqual(len(rows), len(expected))
        for rendered, row in zip(rows, expected):
            self.assertEqual(rendered[0], str(row["rank"]))
            self.assertIn(row["id"], rendered[1])
            self.assertIn(row["title"], rendered[1])
            self.assertTrue(rendered[2].startswith(row["state"]))
            self.assertEqual(rendered[3], str(row["open_transitive_dependents_count"]))
            self.assertEqual(rendered[4], str(row["direct_dependents_count"]))
            self.assertEqual(rendered[5],
                             str(row["required_open_transitive_dependents_count"]))

        self.assertIn(f"Dependency cycles: {summary['cycles']}",
                      self.page.inner_text("#impact-cycles-note"))
        self.assertIn("schedule_unknown", self.page.inner_text("#impact-gaps"))
        status = self.page.inner_text("#impact-status")
        self.assertIn(f"top 5 of {self.snapshot['blockers_total']}", status)
        self.assertIn("schedule status unknown", status)

    def test_narrow_view_keeps_page_inside_viewport(self):
        page = self.browser.new_page(viewport={"width": 320, "height": 800})
        try:
            page.goto(self.url, wait_until="load")
            page.wait_for_function(
                "() => document.getElementById('impact-status').textContent.includes('loaded')",
                timeout=15000)
            self.assertLessEqual(
                page.evaluate("document.documentElement.scrollWidth"),
                page.evaluate("document.documentElement.clientWidth") + 1,
                "impact panel pushes the page wider than the 320 px viewport")
            self.assertTrue(page.is_visible("#dependency-impact"))
            self.assertGreater(
                page.eval_on_selector("#impact-scroll", "el => el.scrollWidth"),
                page.eval_on_selector("#impact-scroll", "el => el.clientWidth"),
                "blocker table should scroll inside its region, not overflow the page")
            self.assertGreaterEqual(
                page.eval_on_selector("#impact-scroll", "el => el.clientHeight"), 40)
        finally:
            page.close()

    def test_missing_snapshot_degrades_visibly(self):
        page = self.browser.new_page(viewport={"width": 1280, "height": 900})
        errors = []
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.route("**/dependency-impact.json", lambda route: route.abort())
        try:
            page.goto(self.url, wait_until="load")
            page.wait_for_function(
                "() => document.getElementById('impact-status').textContent"
                ".includes('unavailable')", timeout=15000)
            self.assertIn("No impact numbers inferred",
                          page.inner_text("#impact-status"))
            self.assertIn("Snapshot not loaded", page.inner_text("#impact-blockers-body"))
            self.assertIn(SCHEDULE_WORDING, page.inner_text("#impact-schedule"))
            self.assertEqual(errors, [], "missing snapshot must not raise a JS error")
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()

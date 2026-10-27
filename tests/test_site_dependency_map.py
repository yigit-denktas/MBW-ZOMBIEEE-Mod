"""PKG-102 layered dependency-map checks (offline ledger + real Chrome DOM).

Scope of these tests
--------------------
* `LedgerLayoutTests` recompute the expected depth, queue and path data from
  `progress/ledger.json` and compare it with what the page actually renders.
* `BrowserMapTests` drive `site/index.html` in headless Chrome over a local HTTP
  server: rendered depth columns, deterministic crossing-reduced order, focus
  path highlighting, keyboard navigation, zoom/pan, queue/handoff UI, and 320 px
  reflow.
* `StaticMarkupTests` guard the accessibility scaffolding and the declared
  palette contrast. They are structural checks, not rendered-pixel tests.

What these tests do NOT establish: screen-reader speech (NVDA/JAWS/VoiceOver
were not run), rendered-pixel contrast, 200 % text resizing, forced colours, or
any WCAG conformance claim. Browser tests skip (never pass) when Playwright or
a Chrome/Edge channel is unavailable.
"""
import functools
import http.server
import json
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "progress" / "ledger.json"
PAGE = ROOT / "site" / "index.html"
PROBES = (
    "/site/progress/ledger.json",
    "/site/progress/publish-time.json",
    "/site/progress/publish-meta.json",
    "/site/progress/live-status.json",
)


# ---------------------------------------------------------------- ledger model
def load_ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def by_id(data):
    return {item["id"]: item for item in data["items"]}


def displayed(data):
    req = [item for item in data["items"] if item.get("required")]
    disc = [item for item in data["items"]
            if item.get("workOrigin") == "discovered"
            and not item.get("archived") and not item.get("optional")]
    return req + disc


def frontier(data):
    index = by_id(data)
    nodes = displayed(data)
    seeds = [item for item in nodes if item["state"] != "done" and (
        item.get("required") or item["state"] in ("active", "review", "ready", "blocked"))]
    keep = set()

    def add(item):
        if item["id"] in keep:
            return
        keep.add(item["id"])
        for dep in item.get("dependsOn", []):
            if dep in index:
                add(index[dep])

    for seed in seeds:
        add(seed)
    return [item for item in nodes if item["id"] in keep]


def depths(nodes):
    index = {item["id"]: item for item in nodes}
    memo, visiting = {}, set()

    def calc(node_id):
        if node_id in memo:
            return memo[node_id]
        if node_id in visiting:  # cycle break, matches the page's guard
            return 0
        visiting.add(node_id)
        value = 0
        for dep in index[node_id].get("dependsOn", []):
            if dep in index:
                value = max(value, calc(dep) + 1)
        visiting.discard(node_id)
        memo[node_id] = value
        return value

    for item in nodes:
        calc(item["id"])
    return memo


def queue_of(item, index):
    if item["state"] == "done":
        return "done"
    if any(index.get(dep, {}).get("state") != "done" for dep in item.get("dependsOn", [])):
        return "waiting-dependency"
    handoff = item.get("handoff") or {}
    if handoff.get("status") == "waiting-external":
        return "waiting-external"
    if handoff.get("status") == "owner-action" or handoff.get("to") == "owner":
        return "owner-action"
    if item["state"] in ("active", "review"):
        return "in-progress"
    return "ready"


def queue_counts(data):
    index = by_id(data)
    counts = {}
    for item in data["items"]:
        key = queue_of(item, index)
        counts[key] = counts.get(key, 0) + 1
    return counts


def graph_edges(nodes):
    index = {item["id"]: item for item in nodes}
    edges = []
    for item in nodes:
        for dep in item.get("dependsOn", []):
            if dep in index:
                edges.append((dep, item["id"], "dep"))
        outcome = item.get("supportsOutcomeId")
        if outcome and outcome in index:
            edges.append((item["id"], outcome, "support"))
    return edges


def path_sets(root, nodes):
    edges = graph_edges(nodes)
    preds, succs = {}, {}
    for src, dst, _kind in edges:
        preds.setdefault(dst, []).append(src)
        succs.setdefault(src, []).append(dst)

    def reach(start, table):
        seen, queue = set(), [start]
        while queue:
            current = queue.pop()
            for nxt in table.get(current, []):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    return reach(root, preds), reach(root, succs)


def crossings(order_by_depth, edges):
    pos = {}
    for depth, ids in order_by_depth.items():
        for index, node_id in enumerate(ids):
            pos[node_id] = (depth, index)
    total = 0
    for i, (a, b, kind_a) in enumerate(edges):
        if kind_a != "dep":
            continue
        for c, d, kind_b in edges[i + 1:]:
            if kind_b != "dep":
                continue
            if (a not in pos or b not in pos or c not in pos or d not in pos):
                continue
            if pos[a][0] != pos[c][0] or pos[b][0] != pos[d][0]:
                continue
            if (pos[a][1] - pos[c][1]) * (pos[b][1] - pos[d][1]) < 0:
                total += 1
    return total


# ------------------------------------------------------------------- browser
try:
    from playwright.sync_api import sync_playwright
    HAVE_PLAYWRIGHT = True
except Exception:  # pragma: no cover - environment dependent
    HAVE_PLAYWRIGHT = False


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class BrowserMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not HAVE_PLAYWRIGHT:
            raise unittest.SkipTest("Playwright not installed; browser DOM checks not run (UNKNOWN)")
        cls.data = load_ledger()
        cls.nodes = frontier(cls.data)
        cls.node_ids = {item["id"] for item in cls.nodes}
        cls.depths = depths(cls.nodes)
        cls.expected_edges = graph_edges(cls.nodes)
        cls.httpd = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT)))
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.pw = sync_playwright().start()
        cls.browser = None
        for channel in ("chrome", "msedge", None):
            try:
                cls.browser = (cls.pw.chromium.launch(channel=channel, headless=True)
                               if channel else cls.pw.chromium.launch(headless=True))
                cls.channel = channel or "bundled-chromium"
                break
            except Exception:
                continue
        if cls.browser is None:
            cls.pw.stop()
            cls.httpd.shutdown()
            raise unittest.SkipTest("No Chrome/Edge available; browser DOM checks not run (UNKNOWN)")
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
        self.page.on("console", lambda msg: self.errors.append(msg.text) if msg.type == "error" else None)
        self.page.on("response", lambda res: self.bad_responses.append((res.status, res.url))
                     if res.status >= 400 else None)
        self.page.goto(self.url, wait_until="load")
        self.page.wait_for_function(
            "() => document.getElementById('dep-summary').textContent.includes('links')", timeout=15000)

    def tearDown(self):
        unexpected = [(status, url) for status, url in self.bad_responses
                      if not any(url.endswith(probe) for probe in PROBES)]
        network_errors = [text for text in self.errors if "Failed to load resource" not in text]
        self.page.close()
        self.assertEqual(unexpected, [], "unexpected failed responses")
        self.assertEqual(network_errors, [], "browser/JavaScript errors")

    # -- helpers ------------------------------------------------------------
    def rendered(self):
        return self.page.eval_on_selector_all(
            ".dep-column",
            "els => els.map(e => ({depth: Number(e.dataset.depth),"
            " ids: [...e.querySelectorAll('.dep-node')].map(n => n.dataset.workId)}))")

    def rendered_depths(self):
        return {n["id"]: n["depth"] for n in self.page.eval_on_selector_all(
            ".dep-node", "els => els.map(e => ({id: e.dataset.workId, depth: Number(e.dataset.depth)}))")}

    # -- tests --------------------------------------------------------------
    def test_columns_are_prerequisite_depth(self):
        columns = self.rendered()
        self.assertEqual([c["depth"] for c in columns], list(range(len(columns))))
        rendered_ids = [node_id for column in columns for node_id in column["ids"]]
        self.assertEqual(len(rendered_ids), len(self.nodes))
        self.assertEqual(set(rendered_ids), self.node_ids)

        actual = self.rendered_depths()
        self.assertEqual(actual, self.depths, "rendered column != longest prerequisite path")

        shown = set(rendered_ids)
        for src, dst, kind in self.expected_edges:
            if kind == "dep" and src in shown and dst in shown:
                self.assertLess(actual[src], actual[dst], f"edge {src}->{dst} not left-to-right")

    def test_order_is_deterministic_and_reduces_crossings(self):
        first = {c["depth"]: c["ids"] for c in self.rendered()}
        self.page.reload(wait_until="load")
        self.page.wait_for_function(
            "() => document.getElementById('dep-summary').textContent.includes('links')", timeout=15000)
        second = {c["depth"]: c["ids"] for c in self.rendered()}
        self.assertEqual(first, second, "column order is not deterministic across reloads")

        actual_crossings = crossings(first, self.expected_edges)
        naive = {depth: sorted(ids) for depth, ids in first.items()}
        naive_crossings = crossings(naive, self.expected_edges)
        self.assertGreater(naive_crossings, 0, "fixture has no crossings to reduce")
        self.assertLessEqual(actual_crossings, naive_crossings,
                             f"crossings {actual_crossings} worse than naive {naive_crossings}")

    def test_path_focus_matches_transitive_sets(self):
        candidates = [item["id"] for item in self.nodes
                      if len(path_sets(item["id"], self.nodes)[0]) >= 2
                      and len(path_sets(item["id"], self.nodes)[1]) >= 2]
        self.assertTrue(candidates, "no frontier task has both upstream and downstream paths")
        root = candidates[0]
        upstream, downstream = path_sets(root, self.nodes)
        self.page.focus(f'.dep-node[data-work-id="{root}"]')
        self.page.wait_for_function(
            "() => document.querySelectorAll('.dep-node.path-root').length === 1", timeout=5000)

        state = self.page.eval_on_selector_all(
            ".dep-node",
            "els => ({root: els.filter(e => e.classList.contains('path-root')).map(e => e.dataset.workId),"
            " up: els.filter(e => e.classList.contains('upstream')).map(e => e.dataset.workId),"
            " down: els.filter(e => e.classList.contains('downstream')).map(e => e.dataset.workId),"
            " unrelated: els.filter(e => e.classList.contains('unrelated')).map(e => e.dataset.workId)})")
        self.assertEqual(state["root"], [root])
        self.assertEqual(set(state["up"]), upstream)
        self.assertEqual(set(state["down"]), downstream)
        expected_unrelated = self.node_ids - {root} - upstream - downstream
        self.assertEqual(set(state["unrelated"]), expected_unrelated)
        status = self.page.inner_text("#dep-status")
        self.assertIn(root, status)
        self.assertIn(f"{len(upstream)} upstream", status)
        self.assertIn(f"{len(downstream)} downstream", status)
        self.assertGreater(
            self.page.eval_on_selector_all(".dep-edge.up, .dep-edge.down", "els => els.length"), 0,
            "path edges were not highlighted")

    def test_keyboard_path_navigation(self):
        columns = self.rendered()
        column = columns[0]
        first, second = column["ids"][0], column["ids"][1]
        self.page.focus(f'.dep-node[data-work-id="{first}"]')

        self.page.keyboard.press("ArrowDown")
        self.assertEqual(self.page.evaluate("document.activeElement.dataset.workId"), second)
        self.page.keyboard.press("Home")
        self.assertEqual(self.page.evaluate("document.activeElement.dataset.workId"), first)
        self.page.keyboard.press("End")
        self.assertEqual(self.page.evaluate("document.activeElement.dataset.workId"), column["ids"][-1])
        self.page.keyboard.press("Home")

        self.page.keyboard.press("ArrowRight")
        right = self.page.evaluate("document.activeElement.dataset.workId")
        self.assertIn(right, [dst for src, dst, _kind in self.expected_edges if src == first])
        self.page.keyboard.press("ArrowLeft")
        self.assertEqual(self.page.evaluate("document.activeElement.dataset.workId"), first)

        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(150)
        self.assertIn(first, self.page.inner_text("#detail h3"))
        self.assertEqual(self.page.evaluate("document.activeElement.dataset.workId"), first,
                         "Enter must not steal focus from the map")
        self.page.keyboard.press("Escape")
        self.assertIn("cleared", self.page.inner_text("#dep-status").lower())
        self.assertEqual(self.page.eval_on_selector_all(".dep-node.path-root", "els => els.length"), 0)

    def test_zoom_fit_and_pan(self):
        scroller = "#dep-scroll"
        self.assertGreater(self.page.eval_on_selector(scroller, "el => el.scrollWidth"),
                           self.page.eval_on_selector(scroller, "el => el.clientWidth"),
                           "map should need horizontal panning at 100%")

        self.page.click("#dep-zoom-out")
        self.page.wait_for_timeout(250)
        self.assertEqual(self.page.inner_text("#dep-zoom-level"), "80%")
        self.assertEqual(self.page.eval_on_selector("#dep-map", "el => el.style.transform"), "scale(0.8)")

        self.page.click("#dep-fit")
        self.page.wait_for_timeout(250)
        viewport_width = float(self.page.eval_on_selector("#dep-viewport", "el => parseFloat(el.style.width)"))
        client_width = self.page.eval_on_selector(scroller, "el => el.clientWidth")
        self.assertLessEqual(viewport_width, client_width + 2, "Fit did not fit the map width")

        self.page.click("#dep-zoom-reset")
        self.page.wait_for_timeout(250)
        self.assertEqual(self.page.inner_text("#dep-zoom-level"), "100%")

        box = self.page.locator(scroller).bounding_box()
        page_scroll_before = self.page.eval_on_selector(scroller, "el => el.scrollLeft")
        self.page.mouse.move(box["x"] + 6, box["y"] + 6)
        self.page.mouse.down()
        self.page.mouse.move(box["x"] - 200, box["y"] + 6, steps=5)
        self.page.mouse.up()
        self.assertGreater(self.page.eval_on_selector(scroller, "el => el.scrollLeft"), page_scroll_before,
                           "drag pan did not move the map")

    def test_queue_and_handoff_ui_preserved(self):
        counts = queue_counts(self.data)
        for key, expected in counts.items():
            if key == "done":
                continue
            self.assertEqual(
                int(self.page.inner_text(f"#queue-{key}-count")), expected, f"queue chip {key}")
        self.assertIn(f"waiting dependency {counts['waiting-dependency']}",
                      self.page.inner_text("#queue-count").lower())

        self.page.click('.queue-chip[data-queue="ready"]')
        self.page.wait_for_timeout(150)
        self.assertEqual(self.page.eval_on_selector_all("#items button", "els => els.length"),
                         counts.get("ready", 0))
        self.page.click('.queue-chip[data-queue=""]')
        self.page.wait_for_timeout(150)
        self.assertEqual(self.page.eval_on_selector_all("#items button", "els => els.length"),
                         len(self.data["items"]))

        handoff = next(item for item in self.data["items"] if item.get("handoff"))
        self.page.click(f'#items button[data-work-id="{handoff["id"]}"]')
        self.page.wait_for_timeout(150)
        detail = self.page.inner_text("#detail")
        self.assertIn("Handoff", detail)
        self.assertIn(str(handoff["handoff"]["status"]), detail)
        self.assertIn("Queue:", detail)
        self.assertIn(handoff["id"], self.page.inner_text("#detail h3"))

    def test_reflow_at_320_css_pixels(self):
        page = self.browser.new_page(viewport={"width": 320, "height": 800})
        try:
            page.goto(self.url, wait_until="load")
            page.wait_for_function(
                "() => document.getElementById('dep-summary').textContent.includes('links')", timeout=15000)
            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 321,
                                 "page overflows at 320 CSS px")
            self.assertGreater(page.eval_on_selector("#dep-scroll", "el => el.scrollWidth"),
                               page.eval_on_selector("#dep-scroll", "el => el.clientWidth"),
                               "map should scroll internally at 320 px")
        finally:
            page.close()


# -------------------------------------------------------------------- static
class StaticMarkupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")

    def test_accessible_scaffolding_present(self):
        for needle in (
            'id="dep-scroll"', 'role="region"', 'role="group"',
            'aria-roledescription="layered dependency graph"',
            'aria-label="Dependency graph arranged by prerequisite depth"',
            'id="dep-status"', 'role="status"', 'aria-live="polite"',
            'id="dep-help"', 'id="dep-columns"',
            'id="dep-zoom-in"', 'id="dep-zoom-out"', 'id="dep-fit"', 'id="dep-zoom-reset"',
            'id="dep-clear-focus"', 'aria-label="Map zoom"',
            "prefers-reduced-motion",
        ):
            self.assertIn(needle, self.html, needle)
        self.assertNotIn("<script src=", self.html, "page must not load third-party scripts")

    def test_no_wcag_conformance_claim(self):
        lowered = self.html.lower()
        for phrase in ("wcag aa", "wcag 2.2 aa", "wcag compliant", "conforms to wcag"):
            self.assertNotIn(phrase, lowered)
        self.assertIn("not a wcag conformance claim", lowered)

    def test_declared_palette_contrast(self):
        def lum(hex_color):
            value = hex_color.lstrip("#")
            channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
            linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def ratio(fg, bg):
            hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
            return (hi + 0.05) / (lo + 0.05)

        # Declared colours in the map CSS; these pairs carry map text / focus UI.
        text_pairs = [
            ("#f0efea", "#1d222c"),   # node title on node surface
            ("#bdc2c9", "#1d222c"),   # node meta on node surface
            ("#bdc2c9", "#171b22"),   # de-emphasised (unrelated) node text
            ("#8fb8ff", "#202a3a"),   # upstream text on upstream surface
            ("#f0b46a", "#2e2719"),   # downstream text on downstream surface
            ("#f4c29b", "#151922"),   # focus outline on map background
        ]
        for fg, bg in text_pairs:
            self.assertIn(fg, self.html)
            self.assertIn(bg, self.html)
            self.assertGreaterEqual(round(ratio(fg, bg), 2), 4.5, f"{fg} on {bg}")
        self.assertGreaterEqual(round(ratio("#687381", "#151922"), 2), 3.0,
                                "link stroke contrast (non-text)")


if __name__ == "__main__":
    unittest.main()

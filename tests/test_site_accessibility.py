"""Static accessibility checks for the Pages site (`site/index.html`).

Read-only by design: this module parses the page as source text and never writes
to `site/`. It exists so the package branch can record *what the markup declares*
without touching the page itself.

Verified here (source structure + WCAG 2.2 contrast arithmetic):
  * document language, one h1, and the banner/main/contentinfo/navigation
    landmark skeleton, with the skip link as the first tab stop and a target
    that resolves inside `main`;
  * accessible names for the dependency map, its labelled control groups, every
    button, every form control, the work-item list, and image alternatives;
  * keyboard focusability: native controls only, no positive tabindex, the map
    scroller is a focusable region, map cards are native buttons with a roving
    tabindex, and the detail panel is a programmatic focus target;
  * persistent polite live regions for status text that exist from first paint;
  * contrast of the declared text/border/focus palette against the WCAG 2.2
    A/AA thresholds (4.5:1 text, 3:1 non-text), plus the queue-chip and live
    status state colours;
  * an explicit "not a WCAG conformance claim" statement on the page and in
    `docs/ACCESSIBILITY_REPORT.md`, with no positive conformance claim anywhere.

NOT established here (these stay UNKNOWN in the report): NVDA/JAWS/VoiceOver
speech, rendered-pixel contrast (opacity compositing, antialiasing, forced
colours, display gamma), 200 % text-only resize, browser focus order and actual
key handling, target-size measurement, and screen-reader announcement of the
live regions and the detail-panel update. `tests/test_site_dependency_map.py`
runs a headless-Chrome DOM suite for the map itself; this module deliberately
stays offline and standard-library only.

Runtime ARIA mutations cannot be proven from source and are reported, not
asserted: the detail panel's `aria-labelledby` target is removed when an item is
selected (A11Y-02), and the empty-filter message is appended inside `role=list`
(A11Y-03). See `docs/ACCESSIBILITY_REPORT.md` for evidence and remediation.
"""
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "site" / "index.html"
REPORT = ROOT / "docs" / "ACCESSIBILITY_REPORT.md"

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}
# Roles that must carry an accessible name when declared explicitly.
NAMED_ROLES = {"group", "region", "list"}
# ARIA attributes whose tokens must resolve to an element id on the page.
IDREF_ATTRIBUTES = (
    "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns",
    "aria-flowto", "aria-activedescendant",
)


# --------------------------------------------------------------------- parsing
class Element:
    """Minimal element node: tag, attributes, children (str or Element)."""

    def __init__(self, tag, attrs, parent=None):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []

    def __repr__(self):  # pragma: no cover - debugging aid
        ident = self.attrs.get("id")
        return f"<{self.tag}{'#' + ident if ident else ''}>"

    @property
    def text(self):
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text)
        return re.sub(r"\s+", " ", "".join(parts)).strip()

    def walk(self):
        """Yield this node and every descendant in document order."""
        yield self
        for child in self.children:
            if isinstance(child, Element):
                yield from child.walk()

    def descendants(self):
        return [node for node in self.walk() if node is not self]

    def closest(self, tag):
        node = self.parent
        while node is not None:
            if node.tag == tag:
                return node
            node = node.parent
        return None


class _Builder(HTMLParser):
    def __init__(self):
        # convert_charrefs keeps "&amp;" / "&lt;" as characters in text nodes.
        super().__init__(convert_charrefs=True)
        self.root = Element("#document", {})
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        element = Element(tag, {key: (value or "") for key, value in attrs},
                          self._stack[-1])
        self._stack[-1].children.append(element)
        if tag not in VOID_TAGS:
            self._stack.append(element)

    def handle_endtag(self, tag):
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data):
        self._stack[-1].children.append(data)


def load_page():
    builder = _Builder()
    builder.feed(PAGE.read_text(encoding="utf-8"))
    builder.close()
    return builder.root


def index_by_id(root):
    return {node.attrs["id"]: node for node in root.walk() if "id" in node.attrs}


def accessible_name(node, root, ids):
    """Approximate accessible-name computation for static controls."""
    label = node.attrs.get("aria-label", "").strip()
    if label:
        return label
    refs = node.attrs.get("aria-labelledby", "").split()
    if refs:
        return " ".join(ids[ref].text for ref in refs if ref in ids).strip()
    if node.tag == "img":
        return node.attrs.get("alt", "").strip()
    if node.tag in ("input", "select", "textarea"):
        wrapper = node.closest("label")
        if wrapper is not None:
            return wrapper.text
        own_id = node.attrs.get("id", "")
        for candidate in root.walk():
            if candidate.tag == "label" and candidate.attrs.get("for") == own_id:
                return candidate.text
        return ""
    return node.text


def is_focusable(node):
    if node.tag in ("button", "select", "textarea", "summary"):
        return "disabled" not in node.attrs
    if node.tag == "input":
        return node.attrs.get("type") != "hidden" and "disabled" not in node.attrs
    if node.tag == "a":
        return "href" in node.attrs
    return "tabindex" in node.attrs


# ------------------------------------------------------------------- contrast
def relative_luminance(color):
    """WCAG 2.x relative luminance for an opaque #rrggbb colour."""
    value = color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"not a six-digit hex colour: {color}")
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
              for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(foreground, background):
    high, low = sorted((relative_luminance(foreground),
                        relative_luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def flatten(color, background, alpha):
    """Composite a translucent colour over an opaque one (sRGB channel blend)."""
    fg = [int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    bg = [int(background.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    mixed = [round(alpha * top + (1 - alpha) * bottom) for top, bottom in zip(fg, bg)]
    return "#" + "".join(f"{channel:02x}" for channel in mixed)


# --------------------------------------------------------------------- shared
class PageFixture(unittest.TestCase):
    """Parse the page once per class and expose common lookups."""

    @classmethod
    def setUpClass(cls):
        cls.source = PAGE.read_text(encoding="utf-8")
        cls.root = load_page()
        cls.body = next(node for node in cls.root.walk() if node.tag == "body")
        cls.elements = [node for node in cls.root.walk() if node.tag != "#document"]
        cls.ids = index_by_id(cls.root)
        cls.script = "\n".join(node.text for node in cls.elements if node.tag == "script")
        cls.style = "\n".join(node.text for node in cls.elements if node.tag == "style")

    def name_of(self, node):
        return accessible_name(node, self.root, self.ids)

    def visible_text(self):
        return self.body.text


# -----------------------------------------------------------------  structure
class StructureTests(PageFixture):
    def test_document_language_is_declared(self):
        html = [node for node in self.elements if node.tag == "html"]
        self.assertEqual(len(html), 1, "exactly one <html> element")
        lang = html[0].attrs.get("lang", "").strip()
        self.assertRegex(lang, r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*$",
                         "html@lang must be a BCP-47 language tag")
        self.assertTrue(lang.lower().startswith("en"),
                        f"page content is English but lang={lang!r}")

    def test_skip_link_is_first_tab_stop_and_lands_in_main(self):
        tab_stops = [node for node in self.body.walk() if is_focusable(node)]
        self.assertTrue(tab_stops, "the page must expose at least one tab stop")
        skip = tab_stops[0]
        self.assertEqual(skip.tag, "a", "the first tab stop must be the skip link")
        self.assertIn("skip", skip.attrs.get("class", "").split())
        self.assertIn("skip", skip.text.lower())
        href = skip.attrs.get("href", "")
        self.assertTrue(href.startswith("#"), "skip link must target a fragment")
        target = self.ids.get(href[1:])
        self.assertIsNotNone(target, f"skip link target {href!r} does not exist")
        mains = [node for node in self.elements if node.tag == "main"]
        self.assertEqual(len(mains), 1, "exactly one main landmark")
        main = mains[0]
        self.assertTrue(any(node is target for node in main.walk()),
                        f"skip link target {href!r} must live inside main")

    def test_landmark_and_heading_skeleton(self):
        tags = [node.tag for node in self.elements]
        self.assertEqual(tags.count("main"), 1, "one main landmark")
        self.assertEqual(tags.count("header"), 1, "one banner landmark")
        self.assertEqual(tags.count("footer"), 1, "one contentinfo landmark")
        self.assertGreaterEqual(tags.count("nav"), 1, "navigation landmark present")

        header = next(node for node in self.elements if node.tag == "header")
        main = next(node for node in self.elements if node.tag == "main")
        footer = next(node for node in self.elements if node.tag == "footer")
        order = {id(node): position for position, node in enumerate(self.elements)}
        self.assertIsNone(header.closest("main"), "header must sit outside main")
        self.assertLess(order[id(header)], order[id(main)], "header before main")
        self.assertLess(order[id(main)], order[id(footer)], "main before footer")

        for nav in (node for node in self.elements if node.tag == "nav"):
            self.assertTrue(self.name_of(nav), "each navigation landmark needs a name")

        h1 = [node for node in self.elements if node.tag == "h1"]
        self.assertEqual(len(h1), 1, "exactly one h1")
        self.assertTrue(h1[0].text.strip(), "h1 must carry text")
        h1_order = order[id(h1[0])]
        self.assertLess(order[id(header)], h1_order, "h1 belongs to the page header")
        self.assertLess(h1_order, order[id(main)], "h1 appears before main")

    def test_aria_id_references_resolve_statically(self):
        for attribute in IDREF_ATTRIBUTES:
            for node in self.elements:
                for token in node.attrs.get(attribute, "").split():
                    self.assertIn(token, self.ids,
                                  f"{attribute} points at missing #{token}")

    def test_no_third_party_or_hidden_focus_traps(self):
        self.assertNotIn("<script src=", self.source,
                         "the page must not load third-party scripts")
        self.assertEqual([node for node in self.elements if node.attrs.get("onclick")], [],
                         "inline onclick bypasses keyboard focusability")
        for node in self.elements:
            if node.attrs.get("aria-hidden") == "true" or "hidden" in node.attrs:
                reachable = [child for child in node.walk() if is_focusable(child)]
                self.assertEqual(reachable, [],
                                 f"focusable content inside hidden subtree {node!r}")


# ------------------------------------------------------------ names and labels
class AccessibleNameTests(PageFixture):
    def test_dependency_map_is_named_and_described(self):
        graph = self.ids["dep-map"]
        self.assertEqual(graph.attrs.get("role"), "group")
        name = self.name_of(graph).lower()
        self.assertIn("dependency graph", name)
        self.assertIn("dependency graph",
                      graph.attrs.get("aria-roledescription", "").lower())
        described = graph.attrs.get("aria-describedby", "").split()
        self.assertTrue(described, "the map must reference its keyboard help/status")
        for ref in described:
            self.assertIn(ref, self.ids)

        help_text = self.ids["dep-help"].text.lower()
        for needle in ("keyboard", "tab", "enter", "escape"):
            self.assertIn(needle, help_text,
                          f"map help must document {needle!r} operation")
        self.assertTrue(any(token in help_text for token in ("arrow", "\u2191", "\u2190")),
                        "map help must document arrow-key movement")

    def test_every_group_region_and_list_has_a_name(self):
        seen = 0
        for node in self.elements:
            role = node.attrs.get("role")
            if role in NAMED_ROLES:
                seen += 1
                self.assertTrue(self.name_of(node),
                                f"role={role} without accessible name: {node.attrs}")
        self.assertGreaterEqual(seen, 6, "map/controls/list groups must be present")

    def test_map_controls_are_labelled(self):
        controls = [node for node in self.elements
                    if "dep-controls" in node.attrs.get("class", "").split()]
        self.assertEqual(len(controls), 1)
        self.assertIn("dependency map controls", self.name_of(controls[0]).lower())

        legend = [node for node in self.elements
                  if "dep-legend" in node.attrs.get("class", "").split()]
        self.assertEqual(len(legend), 1)
        self.assertIn("legend", self.name_of(legend[0]).lower())

        zoom_group = [node for node in self.elements
                      if "dep-zoom" in node.attrs.get("class", "").split()
                      and node.attrs.get("role") == "group"]
        self.assertEqual(len(zoom_group), 1, "zoom controls form one labelled group")
        self.assertIn("zoom", self.name_of(zoom_group[0]).lower())

        for button_id, needle in (("dep-zoom-in", "zoom in"),
                                  ("dep-zoom-out", "zoom out")):
            name = self.name_of(self.ids[button_id]).lower()
            self.assertIn(needle, name, f"#{button_id} needs a distinct name")
        for button_id in ("dep-fit", "dep-zoom-reset", "dep-clear-focus",
                          "dep-expand", "dep-frontier", "dep-all"):
            self.assertTrue(self.name_of(self.ids[button_id]).strip(),
                            f"#{button_id} needs an accessible name")

    def test_every_button_and_form_control_has_a_name(self):
        for node in self.elements:
            if node.tag in ("button", "input", "select", "textarea"):
                self.assertTrue(self.name_of(node).strip(),
                                f"{node.tag} without accessible name: {node.attrs}")
        for image in (node for node in self.elements if node.tag == "img"):
            self.assertTrue(self.name_of(image).strip(), "images need a text alternative")

    def test_work_item_list_and_queue_filters_are_labelled(self):
        items = self.ids["items"]
        self.assertEqual(items.attrs.get("role"), "list")
        self.assertTrue(self.name_of(items))

        chips = [node for node in self.elements
                 if node.tag == "button"
                 and "queue-chip" in node.attrs.get("class", "").split()]
        self.assertGreaterEqual(len(chips), 6)
        for chip in chips:
            self.assertIn(chip.attrs.get("aria-pressed"), {"true", "false"},
                          "queue filters must expose their pressed state")
            self.assertIn("items", chip.attrs.get("aria-controls", "").split(),
                          "queue filters must point at the list they filter")
        self.assertIn("aria-pressed", self.script,
                      "work-item buttons must expose their selected state")


# -------------------------------------------------------------------- keyboard
class KeyboardTests(PageFixture):
    def test_no_positive_tabindex_and_native_controls(self):
        for node in self.elements:
            if "tabindex" in node.attrs:
                self.assertLessEqual(int(node.attrs["tabindex"]), 0,
                                     f"positive tabindex breaks reading order: {node.attrs}")
        fake_controls = [node for node in self.elements
                         if node.attrs.get("role") in ("button", "link", "checkbox",
                                                       "switch", "tab")]
        self.assertEqual(fake_controls, [],
                         "controls must stay native until keyboard handling is proven")
        for node in self.elements:
            if node.tag in ("button", "a", "input", "select", "textarea"):
                self.assertTrue(is_focusable(node),
                                f"{node.tag} is not keyboard focusable: {node.attrs}")

    def test_map_scroller_is_a_focusable_region(self):
        scroller = self.ids["dep-scroll"]
        self.assertEqual(scroller.attrs.get("tabindex"), "0")
        self.assertEqual(scroller.attrs.get("role"), "region")
        self.assertIn("dependency graph", self.name_of(scroller).lower())

    def test_detail_panel_is_a_programmatic_focus_target(self):
        detail = self.ids["detail"]
        self.assertEqual(detail.attrs.get("tabindex"), "-1")
        self.assertTrue(detail.attrs.get("aria-labelledby"),
                        "detail landmark must be named")
        self.assertIn("d.focus()", self.script,
                      "selection must be able to move focus to the detail panel")

    def test_map_cards_keep_one_tab_stop_and_declare_keys(self):
        # Cards are native buttons created at runtime; the roving tabindex keeps
        # exactly one card in the tab order instead of one stop per card.
        self.assertIn("document.createElement('button')", self.script)
        self.assertIn("b.className='dep-node '", self.script)
        self.assertRegex(self.script, r"tabIndex\s*=\s*n\s*===\s*target\s*\?\s*0\s*:\s*-1",
                         "map cards must use roving tabindex")
        self.assertIn("aria-current", self.script)
        for key in ("ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home",
                    "End", "Escape"):
            self.assertIn(key, self.script, f"no declared handler for {key}")
        self.assertIn("e.preventDefault()", self.script)
        self.assertIn("prefers-reduced-motion", self.script,
                      "scroll/zoom animation must respect reduced motion")

        queue = [node for node in self.elements
                 if "queue-summary" in node.attrs.get("id", "")]
        self.assertTrue(queue)
        self.assertIn("ArrowLeft", self.script)
        self.assertIn("ArrowRight", self.script)


# ------------------------------------------------------------------ live status
class LiveRegionTests(PageFixture):
    REQUIRED = {
        "live-status": "status",
        "dep-status": "status",
        "dep-summary": "status",
        "count": "status",
        "queue-count": "status",
        "dep-zoom-level": None,  # <output> has an implicit status role
    }

    def test_live_regions_are_present_from_first_paint(self):
        live = [node for node in self.elements if "aria-live" in node.attrs]
        self.assertGreaterEqual(len(live), 5)
        for node in live:
            self.assertIn(node.attrs["aria-live"], {"polite", "assertive"})
            self.assertNotEqual(node.attrs.get("aria-hidden"), "true")

        for element_id, expected_role in self.REQUIRED.items():
            node = self.ids.get(element_id)
            self.assertIsNotNone(node, f"missing live region #{element_id}")
            self.assertTrue("aria-live" in node.attrs
                            or node.attrs.get("role") in ("status", "alert"),
                            f"#{element_id} is not a live region")
            if expected_role:
                self.assertEqual(node.attrs.get("role"), expected_role,
                                 f"#{element_id} should be role={expected_role}")

    def test_help_text_is_not_a_live_region(self):
        # Help/instructions are static; they must not sit inside a live region,
        # otherwise every focus change would be announced as an update.
        help_node = self.ids["dep-help"]
        self.assertNotIn("aria-live", help_node.attrs)
        self.assertNotEqual(help_node.attrs.get("role"), "status")
        self.assertNotEqual(self.ids["dep-status"].text, "")

    def test_live_regions_have_initial_text_or_are_filled_from_data(self):
        for element_id in ("live-status", "dep-status", "queue-count"):
            self.assertTrue(self.ids[element_id].text.strip(),
                            f"#{element_id} must render text without JavaScript")
        self.assertIn("textContent", self.script,
                      "status regions must be updated in place, not replaced")


# --------------------------------------------------------------------- contrast
class ContrastTests(PageFixture):
    TEXT_MIN = 4.5      # WCAG 1.4.3 normal text
    NON_TEXT_MIN = 3.0  # WCAG 1.4.11 / 2.4.11 UI + focus indicators

    def tokens(self):
        return dict(re.findall(r"--([a-z][a-z0-9-]*)\s*:\s*(#[0-9a-fA-F]{6})\b",
                               self.style))

    def assert_ratio(self, label, foreground, background, minimum):
        self.assertIn(foreground.lower(), self.style.lower(),
                      f"{label}: {foreground} is not declared in the stylesheet")
        self.assertIn(background.lower(), self.style.lower(),
                      f"{label}: {background} is not declared in the stylesheet")
        ratio = round(contrast_ratio(foreground, background), 2)
        self.assertGreaterEqual(ratio, minimum,
                                f"{label}: {foreground} on {background} is {ratio}:1 "
                                f"(needs {minimum}:1)")

    def test_palette_tokens_are_declared_and_used(self):
        tokens = self.tokens()
        for name in ("bg", "surface", "text", "muted", "accent", "line", "focus"):
            self.assertIn(name, tokens, f"--{name} must be declared on :root")
            self.assertIn(f"var(--{name})", self.style,
                          f"--{name} is declared but never used")

    def test_declared_text_tokens_meet_aa(self):
        tokens = self.tokens()
        pairs = [
            ("body text on page", tokens["text"], tokens["bg"]),
            ("body text on surface", tokens["text"], tokens["surface"]),
            ("muted text on page", tokens["muted"], tokens["bg"]),
            ("muted text on surface", tokens["muted"], tokens["surface"]),
            ("muted text on map background", tokens["muted"], "#151922"),
            ("muted text on de-emphasised node", tokens["muted"], "#171b22"),
            ("muted text on path-focus node", tokens["muted"], "#2a3340"),
            ("accent link on page", tokens["accent"], tokens["bg"]),
            ("accent text on surface", tokens["accent"], tokens["surface"]),
            ("button text on pressed surface", tokens["text"], "#37272d"),
            ("handoff line on pressed item", tokens["focus"], "#37272d"),
            ("live status text", "#cfd6df", "#171c24"),
            ("live status ok", "#8fd3a8", "#171c24"),
            ("live status warn", "#e6b85c", "#171c24"),
            ("live status emphasis", tokens["focus"], "#171c24"),
            ("replay caption", "#9aa6b2", "#10151c"),
            ("replay pending", "#9aa6b2", "#151a22"),
            ("quick-lane list", "#9aa6b2", "#11161d"),
            ("queue chip ready", "#8fd3a8", tokens["surface"]),
            ("queue chip in progress", "#e6b85c", tokens["surface"]),
            ("queue chip waiting dependency", "#e67b70", tokens["surface"]),
            ("queue chip waiting external", "#e67e22", tokens["surface"]),
            ("queue chip owner action", "#c9a7ff", tokens["surface"]),
            ("queue chip ready pressed", "#8fd3a8", "#37272d"),
            ("queue chip in progress pressed", "#e6b85c", "#37272d"),
            ("queue chip waiting dependency pressed", "#e67b70", "#37272d"),
            ("queue chip waiting external pressed", "#e67e22", "#37272d"),
            ("queue chip owner action pressed", "#c9a7ff", "#37272d"),
        ]
        for label, foreground, background in pairs:
            with self.subTest(label=label):
                self.assert_ratio(label, foreground, background, self.TEXT_MIN)

    def test_declared_border_focus_and_state_tokens_meet_non_text_minimum(self):
        tokens = self.tokens()
        pairs = [
            ("focus ring on page", tokens["focus"], tokens["bg"]),
            ("focus ring on surface", tokens["focus"], tokens["surface"]),
            ("focus ring on map background", tokens["focus"], "#151922"),
            ("focus ring on pressed surface", tokens["focus"], "#37272d"),
            ("border line on page", tokens["line"], tokens["bg"]),
            ("border line on surface", tokens["line"], tokens["surface"]),
            ("state done edge", "#5bbf86", tokens["surface"]),
            ("state in-progress edge", "#e6b85c", tokens["surface"]),
            ("state waiting-dependency edge", "#e67b70", tokens["surface"]),
            ("state waiting-external edge", "#e67e22", tokens["surface"]),
            ("state ready-gate edge", "#7e8fc7", tokens["surface"]),
            ("state open edge", tokens["line"], tokens["surface"]),
            ("state owner edge", "#c9a7ff", tokens["surface"]),
            ("upstream edge against node", "#8fb8ff", "#202a3a"),
            ("downstream edge against node", "#f0b46a", "#2e2719"),
            # Declared stroke colour only: `.dep-edge` renders at opacity .18,
            # which composites to ~1.2:1 over #151922. That rendered state is
            # finding A11Y-01 in docs/ACCESSIBILITY_REPORT.md and still needs a
            # pixel probe; this assertion must not be read as a render result.
            ("graph edge stroke (declared, before opacity)", tokens["line"], "#151922"),
        ]
        for label, foreground, background in pairs:
            with self.subTest(label=label):
                self.assert_ratio(label, foreground, background, self.NON_TEXT_MIN)

    def test_opacity_compositing_is_not_silently_treated_as_passing(self):
        # Keep the arithmetic honest: the default map edge composite fails 3:1,
        # so no test may claim the rendered graph meets non-text contrast.
        rendered = flatten("#687381", "#151922", 0.18)
        self.assertLess(round(contrast_ratio(rendered, "#151922"), 2), self.NON_TEXT_MIN)
        self.assertRegex(self.style, r"\.dep-edge\{[^}]*opacity:\.18",
                         "default edge opacity changed: re-open finding A11Y-01")


# ------------------------------------------------------------- claim boundaries
class ClaimBoundaryTests(PageFixture):
    DISCLAIMER = "not a wcag conformance claim"
    POSITIVE_CLAIMS = ("wcag aa", "wcag 2.2 aa", "wcag compliant", "conforms to wcag",
                       "meets wcag", "passes wcag", "wcag 2.1 aa")

    def test_page_makes_no_conformance_claim(self):
        lowered = re.sub(r"\s+", " ", self.source.lower())
        self.assertIn(self.DISCLAIMER, lowered,
                      "the page must state that it is not a WCAG conformance claim")
        residual = re.sub(r"not a( wcag)? conformance claim", "", lowered)
        for phrase in self.POSITIVE_CLAIMS + ("conformance",):
            self.assertNotIn(phrase, residual,
                             f"positive accessibility claim on the page: {phrase!r}")
        visible = re.sub(r"\s+", " ", self.visible_text().lower())
        self.assertIn(self.DISCLAIMER, visible,
                      "the disclaimer must be visible text, not only a comment")

    def test_report_states_scope_unknowns_and_no_conformance(self):
        self.assertTrue(REPORT.exists(),
                        "docs/ACCESSIBILITY_REPORT.md is part of this package")
        report = REPORT.read_text(encoding="utf-8")
        lowered = re.sub(r"\s+", " ", report.lower())
        self.assertIn(self.DISCLAIMER, lowered)
        self.assertIn("unknown", lowered)
        for needle in ("nvda", "jaws", "voiceover", "rendered-pixel", "200%",
                       "forced colours", "f766776"):
            self.assertIn(needle, lowered,
                          f"report must name {needle!r} as tested or UNKNOWN")
        headings = [line.lower() for line in report.splitlines()
                    if line.startswith("#")]
        for needle in ("verified", "unknown", "finding", "remediation"):
            self.assertTrue(any(needle in heading for heading in headings),
                            f"report needs a {needle!r} section")
        self.assertRegex(report, r"A11Y-\d{2}",
                         "report must carry stable finding ids")
        self.assertIn("acceptance", lowered,
                      "report must state that this package grants no acceptance")


if __name__ == "__main__":
    unittest.main()

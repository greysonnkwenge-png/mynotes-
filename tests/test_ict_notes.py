"""Content, source-alignment and export checks for the revised learning book.

Run after building: .venv/bin/python -m unittest discover -s tests -v
These checks do not pretend to test classroom hardware or third-party services.
"""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import unicodedata
import unittest
from urllib.parse import urlsplit, unquote
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_ict_notes as book

SOURCE = ROOT / "notes/upper-sixth-ict"
SITE = ROOT / "examples/upper-sixth-ict/site"
OUTPUT = ROOT / "output"
NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}


def norm(text):
    """Ignore typography/spacing, not the actual letters or digits of the content."""
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", text).lower())


def plain_inline(text):
    return "".join(f"[{value}]" if kind == "link" else value
                   for kind, value, _ in book.inline_tokens(text))


def body_text(pdf):
    chunks = []
    for number, page in enumerate(pdf, 1):
        skip = {"UPPER SIXTH  ·  ICT", "FIRST TERM  ·  2026–2027",
                "Learning notes  ·  Based on the supplied progression", str(number)}
        chunks.append(" ".join(line for line in page.get_text().splitlines() if line not in skip))
    return " ".join(chunks)


class StrictPage(HTMLParser):
    """The supplied HTML uses explicit closing tags, so check them strictly."""
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.elements = []
        self.ids = []
        self.title = []
        self.feed(text)
        self.close()
        if self.stack:
            raise AssertionError(f"Unclosed elements: {self.stack}")

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            raise AssertionError(f"Mismatched closing tag {tag}; stack={self.stack}")
        self.stack.pop()

    def handle_data(self, data):
        if self.stack and self.stack[-1] == "title":
            self.title.append(data)


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum, cls.blocks = book.load_book()
        cls.parts = [SOURCE / part["file"] for part in cls.curriculum["parts"]]
        cls.text = "\n".join(path.read_text(encoding="utf-8") for path in cls.parts)
        cls.sections = {}
        for match in re.finditer(r"^## Lesson (\d+) — [^\n]+\n(.*?)(?=^## (?:Lesson |Evaluation )|\Z)",
                                 cls.text, re.M | re.S):
            cls.sections[int(match[1])] = match[2]

    def test_all_46_lessons_and_nine_integration_activities(self):
        self.assertEqual(list(self.sections), list(range(1, 47)))
        entries = self.curriculum["lessons"]
        self.assertEqual([e["number"] for e in entries if e["type"] == "integration"],
                         [6, 9, 12, 16, 20, 26, 34, 41, 45])
        self.assertEqual(sum(len(e["objectives"]) for e in entries), 113)
        self.assertTrue(all(1 <= e["week"] <= 13 for e in entries))
        self.assertEqual(self.curriculum["weekly_periods"], 8)

    def test_every_objective_matches_its_actual_supplied_pdf_page(self):
        with pymupdf.open(ROOT / self.curriculum["primary_source"]) as pdf:
            pages = [norm(page.get_text(sort=False)) for page in pdf]
            for entry in self.curriculum["lessons"]:
                for objective in entry["objectives"]:
                    with self.subTest(lesson=entry["number"], objective=objective):
                        self.assertIn(norm(objective), pages[entry["progression_page"] - 1])

    def test_source_discrepancy_and_verification_limits_are_disclosed(self):
        text = (SOURCE / "revision-and-sources.md").read_text()
        self.assertIn("LOWERSIXTH", text)
        self.assertIn("not supplied or verified", text)
        self.assertIn("locally authored", text)
        self.assertIn("not used as an authoritative Upper Sixth ICT guide", text)

    def test_explanations_practice_questions_and_answers_in_every_reading_lesson(self):
        for entry in self.curriculum["lessons"]:
            number = entry["number"]
            section = self.sections[number]
            with self.subTest(lesson=number):
                if entry["type"] == "lesson":
                    without_code = re.sub(r"```.*?```", "", section, flags=re.S)
                    self.assertGreaterEqual(len(without_code.split()), 600)
                    self.assertIn("### Check your understanding", section)
                    self.assertIn("### Answer guidance", section)
                    self.assertIn("### Worked example", section)
                    self.assertTrue(re.search(r"### (?:\d+\.\d+ )?Guided (?:activity|practical)", section),
                                    f"Lesson {number} needs a labelled guided activity or practical")
                else:
                    self.assertGreaterEqual(len(section.split()), 300)
                    self.assertIn("### Assessment criteria — 20 marks", section)

    def test_main_text_is_prose_not_table_markup_or_placeholders(self):
        self.assertNotRegex(self.text, r"(?m)^\s*\|")
        self.assertNotRegex(self.text, r"(?i)figure placeholder|insert (?:a )?diagram|\bTODO\b")
        prose_words = sum(len(b.text.split()) for b in self.blocks if b.kind == "paragraph")
        content_words = sum(len(b.text.split()) for b in self.blocks)
        self.assertGreater(content_words, 40000)
        self.assertGreater(prose_words / content_words, 0.60)

    def test_all_35_original_figures_exist_and_have_meaningful_captions(self):
        figures = [b for b in self.blocks if b.kind == "image"]
        self.assertEqual(len(figures), 35)
        self.assertEqual(len({b.target for b in figures}), 35)
        for figure in figures:
            with self.subTest(figure=figure.target):
                self.assertRegex(figure.text, r"^Figure \d+\.\d+ — .+")
                self.assertGreater(len(figure.text.split()), 13)
                with Image.open(SOURCE / figure.target) as image:
                    self.assertEqual(image.width, 1800)
                    self.assertGreaterEqual(image.height, 500)
                    self.assertEqual(image.mode, "RGB")

    def test_evaluations_are_at_the_right_points_and_marks_add_up(self):
        headings = [b.text for b in self.blocks if b.kind == "heading" and b.level == 2]
        for number, before, after, total in [(1, 17, 18, 40), (2, 34, 35, 50)]:
            evaluation = next(h for h in headings if h.startswith(f"Evaluation {number} —"))
            i = headings.index(evaluation)
            self.assertTrue(headings[i - 1].startswith(f"Lesson {before} —"))
            self.assertTrue(headings[i + 1].startswith(f"Lesson {after} —"))
            section = re.search(rf"^## Evaluation {number} — [^\n]+\n(.*?)(?=^## Lesson )",
                                self.text, re.M | re.S)[1]
            self.assertEqual(sum(map(int, re.findall(r"\*\*\[(\d+)\]\*\*", section))), total)
            self.assertIn("locally authored", section)

    def test_layout_groups_are_balanced_and_preserve_content(self):
        depth = 0
        for block in self.blocks:
            if block.kind == "group_start":
                depth += 1
            elif block.kind == "group_end":
                depth -= 1
            self.assertIn(depth, [0, 1])
        self.assertEqual(depth, 0)
        self.assertEqual(sum(b.kind == "group_start" for b in self.blocks), 46)

    def test_alignment_report_is_current(self):
        self.assertEqual((SOURCE / "alignment.md").read_text(),
                         book.alignment_report(self.curriculum))

    def test_arithmetic_examples_and_parity_values(self):
        self.assertEqual("10110100".count("1") % 2, 0)
        self.assertEqual("10100100".count("1") % 2, 1)
        self.assertEqual("11010100".count("1") % 2, 0)
        self.assertEqual("1001001".count("1"), 3)
        self.assertIn("**85%**", self.sections[4])
        self.assertIn("**80%**", self.sections[4])
        self.assertIn("**24 ports**", self.sections[19])
        self.assertIn("**78 direct links**", self.sections[15])
        self.assertIn("**12 seconds**", self.sections[28])


class ExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum, cls.blocks = book.load_book()
        cls.pages = {p.name: StrictPage(p.read_text()) for p in SITE.glob("*.html")}

    def test_examples_are_exactly_the_printed_code(self):
        examples = [b for b in self.blocks if b.kind == "code" and b.target]
        self.assertEqual({b.target for b in examples}, {"index.html", "about.html"})
        for block in examples:
            self.assertEqual((SITE / block.target).read_text(), block.text + "\n")

    def test_html_structure_and_accessibility_basics(self):
        self.assertEqual(set(self.pages), {"index.html", "about.html"})
        for filename, page in self.pages.items():
            with self.subTest(page=filename):
                self.assertTrue((SITE / filename).read_text().lower().startswith("<!doctype html>"))
                tags = Counter(tag for tag, _ in page.elements)
                self.assertEqual(tags["h1"], 1)
                self.assertTrue("".join(page.title).strip())
                self.assertEqual(len(page.ids), len(set(page.ids)))
                self.assertTrue(any(tag == "html" and attrs.get("lang") == "en"
                                    for tag, attrs in page.elements))
                for tag, attrs in page.elements:
                    self.assertNotIn(tag, ["script", "style", "iframe"])
                    if tag == "img":
                        self.assertTrue(attrs.get("alt"))
                    if tag == "nav":
                        self.assertTrue(attrs.get("aria-label"))
                    if tag == "th":
                        self.assertEqual(attrs.get("scope"), "col")

    def test_relative_links_fragments_and_images_work_without_network(self):
        for filename, page in self.pages.items():
            for tag, attrs in page.elements:
                for attribute in ["href", "src"]:
                    if attribute not in attrs:
                        continue
                    url = urlsplit(attrs[attribute])
                    self.assertEqual(url.scheme, "")
                    self.assertEqual(url.netloc, "")
                    target = SITE / (unquote(url.path) if url.path else filename)
                    self.assertTrue(target.resolve().is_relative_to(SITE.resolve()))
                    self.assertTrue(target.is_file(), (filename, attrs[attribute]))
                    if url.fragment:
                        self.assertIn(url.fragment, self.pages[target.name].ids)
        self.assertTrue(any(attrs.get("href") == "about.html"
                            for _, attrs in self.pages["index.html"].elements))
        self.assertTrue(any(attrs.get("href") == "index.html"
                            for _, attrs in self.pages["about.html"].elements))
        ET.parse(SITE / "images/club.svg")


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.curriculum, cls.blocks = book.load_book()
        cls.pdf = pymupdf.open(OUTPUT / f"{book.BASENAME}.pdf")
        cls.pdf_text = norm(body_text(cls.pdf))
        cls.archive = ZipFile(OUTPUT / f"{book.BASENAME}.docx")
        cls.xml = ET.fromstring(cls.archive.read("word/document.xml"))
        cls.word_text = norm(" ".join(t.text or "" for t in cls.xml.findall(".//w:t", NS)))

    @classmethod
    def tearDownClass(cls):
        cls.pdf.close()
        cls.archive.close()

    def test_docx_is_valid_with_no_layout_tables_and_35_described_images(self):
        self.assertIsNone(self.archive.testzip())
        self.assertEqual(self.xml.findall(".//w:tbl", NS), [])
        media = [n for n in self.archive.namelist() if n.startswith("word/media/")]
        self.assertEqual(len(media), 35)
        figures = self.xml.findall(".//wp:docPr", NS)
        self.assertEqual(len(figures), 35)
        self.assertTrue(all(f.get("descr", "").startswith("Figure ") for f in figures))

    def test_both_exports_contain_every_shared_text_block(self):
        for block in self.blocks:
            if block.kind not in ["paragraph", "item", "objective", "heading", "meta", "image", "code"]:
                continue
            expected = norm(block.text if block.kind == "code" else plain_inline(block.text))
            with self.subTest(kind=block.kind, beginning=block.text[:75]):
                self.assertIn(expected, self.word_text)
                self.assertIn(expected, self.pdf_text)

    def test_every_progression_objective_is_in_both_exports(self):
        for entry in self.curriculum["lessons"]:
            for objective in entry["objectives"]:
                with self.subTest(lesson=entry["number"], objective=objective):
                    self.assertIn(norm(objective), self.word_text)
                    self.assertIn(norm(objective), self.pdf_text)

    def test_word_contents_links_point_to_real_unique_bookmarks(self):
        bookmarks = self.xml.findall(".//w:bookmarkStart", NS)
        names = [b.get(qn_w("name")) for b in bookmarks]
        self.assertEqual(len(names), len(set(names)))
        links = [h.get(qn_w("anchor")) for h in self.xml.findall(".//w:hyperlink", NS)
                 if h.get(qn_w("anchor"))]
        self.assertEqual(len(links), 57)
        self.assertEqual(set(links), set(names))

    def test_pdf_has_all_lesson_destinations_figures_and_live_contents(self):
        self.assertGreaterEqual(len(self.pdf), 100)
        self.assertLessEqual(len(self.pdf), 190)
        toc = self.pdf.get_toc()
        lessons = [item for item in toc if item[1].startswith("Lesson ")]
        self.assertEqual([int(LESSON_NUMBER.search(item[1])[1]) for item in lessons], list(range(1, 47)))
        for _, title, number in toc:
            self.assertIn(norm(title), norm(self.pdf[number - 1].get_text()))
        self.assertEqual(sum(len(page.get_images()) for page in self.pdf), 35)
        links = [link for page in self.pdf for link in page.get_links()
                 if link["kind"] == pymupdf.LINK_GOTO]
        self.assertGreaterEqual(len(links), 57)
        self.assertTrue(all(0 <= link["page"] < len(self.pdf) for link in links))

    def test_pdf_has_no_blank_or_tiny_tail_pages_overflow_or_missing_glyphs(self):
        for number, page in enumerate(self.pdf, 1):
            with self.subTest(page=number):
                text = page.get_text()
                self.assertNotIn("\ufffd", text)
                self.assertGreaterEqual(len(text.split()), 70)
                for block in page.get_text("dict")["blocks"]:
                    if block["type"] != 0:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            x0, y0, x1, y1 = span["bbox"]
                            self.assertGreaterEqual(x0, 14)
                            self.assertLessEqual(x1, page.rect.width - 12)
                            self.assertGreaterEqual(y0, 8)
                            self.assertLessEqual(y1, page.rect.height - 8)


def qn_w(local):
    return "{" + NS["w"] + "}" + local


LESSON_NUMBER = re.compile(r"Lesson (\d+) —")

if __name__ == "__main__":
    unittest.main()

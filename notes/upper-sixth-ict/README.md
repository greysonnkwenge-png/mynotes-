# Upper Sixth ICT — revised first-term learning notes

## Deliverables

`output/Upper Sixth - ICT - First Term Teaching Notes.docx` replaces the earlier table-dominated Upper Sixth ICT document. A matching-content PDF is supplied beside it for reading and printing. The current PDF has 146 A4 pages, a paginated clickable contents and lesson bookmarks. Word has clickable lesson links, heading styles and editable text/figures; its pagination can differ with installed fonts and Word settings.

The teaching material contains roughly 42,000 exported words, **46 lessons**, **113 progression outcomes**, **35 original figures**, **9 integration activities** and **2 classroom evaluations with remediation**. There are no Word layout tables. The goal is explanatory depth and useful practice, not a target word count. A data table is taught in the HTML lesson because it is genuine subject content, not because the whole book is laid out as a table.

Only Upper Sixth ICT has been revised. The supplied PDFs, all other class documents and legacy build sources remain unchanged.

## How the source is organised

- `curriculum.json`: lesson numbers, weeks, supplied-PDF page references and transcribed learning outcomes. Integration lessons have no printed outcomes in the sheet, so their locally authored tasks are identified as such.
- `front-matter.md`: learner orientation and safe practical-work guidance.
- `01-artificial-intelligence.md` through `06-digital-services-and-html.md`: the actual explanations, worked reasoning, activities, checks and answer guidance.
- `revision-and-sources.md`: synthesis, extended practice, vocabulary, references and limitations.
- `alignment.md`: generated human-readable outcome mapping.
- `figures/`: 35 original labelled PNGs embedded in both exports. There are no figure placeholders or third-party stock images.
- `../../examples/upper-sixth-ict/site/`: the two linked HTML pages and original SVG used by Lesson 46. The code is extracted from the lesson's fenced examples, preventing the printed example and files from drifting apart.

Edit the Markdown or curriculum metadata, then rebuild. Do not treat the previous `.tn` files in `build/src/` as the revised source. The new renderer uses paragraph and heading styles rather than table-based callout cards.

## Reproduction

From the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-notes.txt
.venv/bin/python scripts/build_ict_notes.py
.venv/bin/python -m unittest discover -s tests -v
```

The builder can run from another directory because source paths are resolved from the script location. `--skip-diagrams` reuses the committed figures; `--output-dir PATH` writes the two exports to another folder. Set `ICT_NOTES_FONT_DIR` if the DejaVu TrueType files are installed elsewhere. Required files include DejaVu Sans regular/bold, Serif regular/bold and Sans Mono regular/bold. PDF fonts are embedded; Word uses the named fonts or the reader's available substitutions.

DOCX and PDF consume the same parsed text, objectives, examples and captions. The PDF is generated directly from that shared content, **not** by claiming to have run Microsoft Word or LibreOffice. Consequently its page numbers are specific to the PDF. Word's contents use real internal bookmarks without invented page numbers.

## Verification

The automated suite checks:

- all 46 lessons in order, the nine integration points and the two evaluation placements;
- every one of the 113 outcomes against its assigned page in the supplied PDF, ignoring only punctuation, spacing and letter case;
- substantive prose, worked examples, guided work, questions and answer guidance for every reading lesson;
- matching content in both exports, including every paragraph, objective, code block and figure caption;
- 35 real embedded figures, meaningful captions and Word image descriptions;
- valid internal lesson links, PDF destinations, no missing glyphs, no page-boundary text overflow and no near-empty tail pages;
- structurally checked offline HTML, valid local links/fragments, available image assets and exact agreement with the printed code;
- evaluation totals and the arithmetic/parity examples.

Representative PDF pages were also rasterised and visually reviewed, including the cover, reading text, topology drawings and HTML source. Hardware networking, authenticated VPN access, account creation and third-party platform transactions have **not** been performed by the build/tests. Their prerequisites, supervision and evidence requirements are stated in the lessons. Paper alternatives are explicitly distinguished from real practical completion.

## Curriculum and source cautions

The primary source is the repository's `2026-2027 ICT Upper Sixth Progression Sheet.pdf`, PDF pages 1–6 for first term. Its printed heading says LOWERSIXTH despite its Upper Sixth filename. Both the book and metadata disclose that discrepancy. The separate Lower Sixth file begins with a different sequence. No claim is made that an official heading correction has been obtained.

The GCE Board's official Advanced Level page was consulted for general expectations of application, synthesis and evaluation. The introduction/profile in a mirrored August 2020 MINESEC high-school ICT syllabus supplied pedagogical context only. Neither is presented as a verified current subject-specific 2026–2027 examination syllabus. The Form 1–5 Computer Science teacher guide is not substituted for an Upper Sixth ICT guide.

Questions, scenarios, recommended classroom timings, marks and remediation are original teaching material, not official GCE questions or marking allocations. Fictional school/clinic/cooperative examples are labelled. CSS, JavaScript, hosting and all content from Lesson 47 onward are excluded from first-term instruction. A teacher should pre-test available tools, check official administrative instructions and review the content for the school's actual equipment and learner needs.

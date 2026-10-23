# Teaching and learning notes

The repository contains the supplied progression sheets and teaching-note documents for several classes.

## Revised: Upper Sixth ICT, first term

The Upper Sixth ICT document has been rewritten as a **reading and practice resource**, not a sequence of summary tables. It covers Lessons 1–46 from the supplied 2026–2027 progression, with connected explanations, worked examples, 35 original labelled diagrams, guided practicals, questions and answer guidance, nine integration tasks and two classroom evaluations.

- **Read/print:** [Upper Sixth ICT — First Term Learning Notes (PDF)](output/Upper%20Sixth%20-%20ICT%20-%20First%20Term%20Teaching%20Notes.pdf)
- **Edit:** [Upper Sixth ICT — First Term Learning Notes (Word)](output/Upper%20Sixth%20-%20ICT%20-%20First%20Term%20Teaching%20Notes.docx)
- **Source and editorial notes:** [notes/upper-sixth-ict/README.md](notes/upper-sixth-ict/README.md)
- **Lesson/outcome mapping:** [notes/upper-sixth-ict/alignment.md](notes/upper-sixth-ict/alignment.md)
- **Working offline HTML example:** [examples/upper-sixth-ict/site/index.html](examples/upper-sixth-ict/site/index.html)

Other classes' existing documents are unchanged. Their revision is a separate task.

### Rebuild and check

Use Python 3.11 or later and the DejaVu TrueType fonts. On the Arena workspace the fonts are already installed under `/usr/share/fonts/truetype/dejavu`.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements-notes.txt
.venv/bin/python scripts/build_ict_notes.py
.venv/bin/python -m unittest discover -s tests -v
```

The new builder is the source of truth for **revised Upper Sixth ICT**. The older `build/render.py` and `.tn` files are retained as legacy material and are not used by this builder; running the legacy renderer on its old source would recreate the superseded table-based version.

### Source limits

The supplied PDF named Upper Sixth has a printed “LOWERSIXTH” heading. The inconsistency is documented rather than silently corrected. All 113 listed first-term outcomes are checked against the actual supplied PDF pages. Official GCE Board general expectations were consulted, but a separately authenticated current ICT examination syllabus was not verified. This resource does not claim official Board endorsement, current paper weightings or official marking schemes. See the book's source notes for details.

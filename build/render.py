#!/usr/bin/env python3
"""Teaching-notes renderer: lightweight markup (.tn) -> styled .docx

Usage: python3 build/render.py src.tn out.docx

Markup
  @title: ...        @subtitle: ...    @class: ...     @banner: ...
  @header: ...       @accent: RRGGBB   (default teal 0F9D8A; ICT uses 2F5BEA)
  @meta: Label | Value            (cover metadata table rows)
  @howto: paragraph text          (rendered under "How to use these notes")
  = Module title                  (amber module banner, auto-numbered; following
                                   **bold** lines rendered as meta lines)
  # / ## / ###                    headings 1-3
  - item / 1. item                bullet / numbered lists
  > TYPE: text                    callout; continuation lines indented; TYPE in
                                  OBJ DEF KEY EXAMPLE VISUAL ACTIVITY TIP
                                  MISCONCEPTION ASSESS
  | a | b | c |                   table (first row = header)
  ```  code  ```                  code block
  ---                             thin rule
  **bold** and *italic* inline
"""
import re, sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = "1B2A49"; INK = "222B38"; GREY = "5F6B7A"; AMBER = "F2A900"
ACCENT = "0F9D8A"

CALLOUTS = {
    "OBJ": ("LEARNING OBJECTIVES  |  By the end of this lesson, learners will be able to:", None, "FFFFFF"),
    "DEF": ("DEFINITION", NAVY, "F7F8FA"),
    "KEY": ("KEY CONCEPT", NAVY, "EEF1F7"),
    "EXAMPLE": ("REAL-WORLD EXAMPLE", None, "E8F6F3"),
    "VISUAL": ("VISUAL LEARNING  |  Figure placeholder", "6C5CE7", "F0EEFB"),
    "ACTIVITY": ("CLASSROOM ACTIVITY", AMBER, "FFF6E0"),
    "TIP": ("TEACHING TIP", None, "E8F6F3"),
    "MISCONCEPTION": ("COMMON MISCONCEPTION", "E05A47", "FDEDEA"),
    "ASSESS": ("CHECK FOR UNDERSTANDING", "8E44AD", "F4ECF7"),
}

def rgb(h): return RGBColor.from_string(h)

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill)
    tcPr.append(shd)

def set_borders(table, color="D5DAE3", sz=4, inside=True):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for e in ('top', 'left', 'bottom', 'right') + (('insideH', 'insideV') if inside else ()):
        el = OxmlElement(f'w:{e}'); el.set(qn('w:val'), 'single'); el.set(qn('w:sz'), str(sz)); el.set(qn('w:color'), color); b.append(el)
    for e in () if inside else ('insideH', 'insideV'):
        el = OxmlElement(f'w:{e}'); el.set(qn('w:val'), 'nil'); b.append(el)
    tblPr.append(b)

def no_borders(table):
    tblPr = table._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{e}'); el.set(qn('w:val'), 'nil'); b.append(el)
    tblPr.append(b)

def cell_margins(table, top=80, bottom=80, left=110, right=110):
    tblPr = table._tbl.tblPr
    m = OxmlElement('w:tblCellMar')
    for k, v in (('top', top), ('left', left), ('bottom', bottom), ('right', right)):
        el = OxmlElement(f'w:{k}'); el.set(qn('w:w'), str(v)); el.set(qn('w:type'), 'dxa'); m.append(el)
    tblPr.append(m)

def set_col_widths(table, widths_cm):
    table.autofit = False
    for row in table.rows:
        for i, w in enumerate(widths_cm):
            if i < len(row.cells):
                row.cells[i].width = Cm(w)

INLINE = re.compile(r'(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`)')

def add_inline(par, text, size=None, color=None, bold=None, italic=None):
    for tok in INLINE.split(text):
        if not tok: continue
        r = par.add_run()
        if tok.startswith('**') and tok.endswith('**') and len(tok) > 4:
            r.text = tok[2:-2]; r.bold = True
        elif tok.startswith('`') and tok.endswith('`') and len(tok) > 2:
            r.text = tok[1:-1]; r.font.name = 'Consolas'; r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas')
        elif tok.startswith('*') and tok.endswith('*') and len(tok) > 2:
            r.text = tok[1:-1]; r.italic = True
        else:
            r.text = tok
        if size: r.font.size = size
        if color: r.font.color.rgb = rgb(color)
        if bold is not None and r.bold is None: r.bold = bold
        if italic: r.italic = True

class Renderer:
    def __init__(self):
        self.doc = Document()
        self.meta = {"title": "Teaching Notes", "subtitle": "", "class": "", "banner": "", "header": "", "accent": ACCENT}
        self.metarows = []; self.howto = []; self.module_no = 0
        self.body_started = False

    # ---------- setup ----------
    def setup(self):
        d = self.doc; a = self.meta["accent"]
        s = d.sections[0]
        s.page_width = Emu(7560310); s.page_height = Emu(10692130)
        s.left_margin = s.right_margin = Emu(720090); s.top_margin = Emu(791845); s.bottom_margin = Emu(791845)
        st = d.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(11); st.font.color.rgb = rgb(INK)
        st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri'); st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.08
        for name, font, size, col, before, after in (('Heading 1', 'Calibri Light', 20, NAVY, 18, 6), ('Heading 2', 'Calibri', 14.5, a, 14, 4), ('Heading 3', 'Calibri', 12, NAVY, 10, 3)):
            h = d.styles[name]; h.font.name = font; h.font.size = Pt(size); h.font.color.rgb = rgb(col); h.font.bold = True
            h.element.rPr.rFonts.set(qn('w:eastAsia'), font); h.element.rPr.rFonts.set(qn('w:ascii'), font); h.element.rPr.rFonts.set(qn('w:hAnsi'), font)
            h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after); h.paragraph_format.keep_with_next = True
        for name in ('List Bullet', 'List Number'):
            d.styles[name].font.size = Pt(11); d.styles[name].paragraph_format.space_after = Pt(3)
        # header / footer
        hp = s.header.paragraphs[0]; r = hp.add_run(self.meta["header"]); r.font.size = Pt(8.5); r.font.color.rgb = rgb(GREY)
        fp = s.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = fp.add_run("Page "); r.font.size = Pt(8.5); r.font.color.rgb = rgb(GREY)
        self._field(fp, "PAGE")
        r = fp.add_run("  ·  " + self.meta["title"]); r.font.size = Pt(8.5); r.font.color.rgb = rgb(GREY)

    def _field(self, par, instr):
        r = par.add_run(); r.font.size = Pt(8.5); r.font.color.rgb = rgb(GREY)
        b = OxmlElement('w:fldChar'); b.set(qn('w:fldCharType'), 'begin')
        i = OxmlElement('w:instrText'); i.set(qn('xml:space'), 'preserve'); i.text = instr
        e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), 'end')
        r._r.append(b); r._r.append(i); r._r.append(e)

    def cover(self):
        d = self.doc; a = self.meta["accent"]
        for _ in range(3): d.add_paragraph()
        t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; no_borders(t); cell_margins(t, 160, 160, 200, 200)
        c = t.rows[0].cells[0]; shade(c, a); p = c.paragraphs[0]
        r = p.add_run(self.meta["banner"].upper()); r.bold = True; r.font.size = Pt(11); r.font.color.rgb = rgb("FFFFFF")
        p = d.add_paragraph(); r = p.add_run(self.meta["title"]); r.font.size = Pt(34); r.font.color.rgb = rgb(NAVY); r.font.name = 'Calibri Light'
        p.paragraph_format.space_before = Pt(18)
        p = d.add_paragraph(); r = p.add_run(self.meta["subtitle"]); r.font.size = Pt(15); r.font.color.rgb = rgb(a)
        p = d.add_paragraph(); r = p.add_run(self.meta["class"].upper()); r.font.size = Pt(13); r.font.color.rgb = rgb(GREY); r.bold = True
        for _ in range(2): d.add_paragraph()
        if self.metarows:
            t = d.add_table(rows=0, cols=2); set_borders(t, "E3E7EE", 4); cell_margins(t)
            for k, v in self.metarows:
                row = t.add_row().cells; shade(row[0], "EEF1F7")
                p = row[0].paragraphs[0]; r = p.add_run(k); r.bold = True; r.font.size = Pt(9.5); r.font.color.rgb = rgb(NAVY)
                add_inline(row[1].paragraphs[0], v, size=Pt(9.5), color=GREY)
            set_col_widths(t, [4.2, 12.6])
        for _ in range(5): d.add_paragraph()
        p = d.add_paragraph(); r = p.add_run("Teacher: ______________________________      School: ______________________________      Year: 2026–2027"); r.font.size = Pt(9.5); r.font.color.rgb = rgb(GREY)
        d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        if self.howto:
            d.add_heading("How to use these notes", 1)
            for h in self.howto:
                add_inline(d.add_paragraph(), h)
            d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ---------- blocks ----------
    def module(self, title):
        d = self.doc; self.module_no += 1
        if self.body_started:
            d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        self.body_started = True
        for _ in range(1): d.add_paragraph()
        t = d.add_table(rows=1, cols=1); no_borders(t); cell_margins(t, 90, 90, 200, 200)
        c = t.rows[0].cells[0]; shade(c, AMBER); p = c.paragraphs[0]
        label = f"MODULE {self.module_no}" if not title.lower().startswith(("first term", "consolidation")) else "TERM WRAP-UP"
        r = p.add_run(label); r.bold = True; r.font.size = Pt(10); r.font.color.rgb = rgb(NAVY)
        p = d.add_paragraph(); r = p.add_run(title); r.font.size = Pt(26); r.font.color.rgb = rgb(NAVY); r.font.name = 'Calibri Light'
        p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(6)

    def callout(self, typ, lines):
        d = self.doc; a = self.meta["accent"]
        label, strip, fill = CALLOUTS.get(typ, (typ, None, "F7F8FA")); strip = strip or a
        t = d.add_table(rows=1, cols=2); no_borders(t); cell_margins(t, 100, 100, 160, 160); t.autofit = False
        left, right = t.rows[0].cells
        shade(left, strip); shade(right, fill)
        left.width = Cm(0.35); right.width = Cm(16.45)
        p = right.paragraphs[0]; r = p.add_run(label); r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = rgb(strip if typ not in ("DEF", "KEY") else NAVY)
        p.paragraph_format.space_after = Pt(3)
        first = True
        for ln in lines:
            s = ln.strip()
            if not s: continue
            m = re.match(r'^(\d+)[.)]\s+(.*)', s); b = re.match(r'^[-•]\s+(.*)', s)
            if m:
                q = right.add_paragraph(style='List Number'); add_inline(q, m.group(2), size=Pt(10))
            elif b:
                q = right.add_paragraph(style='List Bullet'); add_inline(q, b.group(1), size=Pt(10))
            else:
                q = right.add_paragraph(); add_inline(q, s, size=Pt(10))
            q.paragraph_format.space_after = Pt(2)
        d.add_paragraph().paragraph_format.space_after = Pt(2)

    def table(self, rows):
        d = self.doc
        ncol = max(len(r) for r in rows)
        t = d.add_table(rows=0, cols=ncol); set_borders(t, "D5DAE3", 4); cell_margins(t, 60, 60, 90, 90)
        for i, r in enumerate(rows):
            cells = t.add_row().cells
            for j in range(ncol):
                txt = r[j] if j < len(r) else ""
                p = cells[j].paragraphs[0]; p.paragraph_format.space_after = Pt(0)
                if i == 0:
                    shade(cells[j], NAVY); rr = p.add_run(txt.replace('**', '')); rr.bold = True; rr.font.size = Pt(10); rr.font.color.rgb = rgb("FFFFFF")
                else:
                    if i % 2 == 0: shade(cells[j], "F7F8FA")
                    add_inline(p, txt, size=Pt(9.5))
        # width heuristics
        total = 16.8
        lens = [max(len((r[j] if j < len(r) else "")) for r in rows) for j in range(ncol)]
        lens = [min(max(l, 6), 60) for l in lens]; s = sum(lens)
        set_col_widths(t, [total * l / s for l in lens])
        d.add_paragraph().paragraph_format.space_after = Pt(2)

    def code(self, lines):
        d = self.doc
        t = d.add_table(rows=1, cols=1); no_borders(t); cell_margins(t, 100, 100, 160, 160)
        c = t.rows[0].cells[0]; shade(c, "F3F4F7")
        p = c.paragraphs[0]
        for k, ln in enumerate(lines):
            if k: p = c.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(ln); r.font.name = 'Consolas'; r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Consolas'); r.font.size = Pt(9)
        d.add_paragraph().paragraph_format.space_after = Pt(2)

    def rule(self):
        p = self.doc.add_paragraph(); pPr = p._p.get_or_add_pPr()
        b = OxmlElement('w:pBdr'); bt = OxmlElement('w:bottom'); bt.set(qn('w:val'), 'single'); bt.set(qn('w:sz'), '6'); bt.set(qn('w:color'), "D5DAE3"); b.append(bt); pPr.append(b)

    # ---------- parse ----------
    def render(self, src):
        lines = src.split('\n'); body = []
        for ln in lines:
            m = re.match(r'^@(\w+):\s*(.*)$', ln)
            if m:
                k, v = m.group(1), m.group(2)
                if k == 'meta': a, b = v.split('|', 1); self.metarows.append((a.strip(), b.strip()))
                elif k == 'howto': self.howto.append(v)
                else: self.meta[k] = v
            else: body.append(ln)
        self.setup(); self.cover()
        d = self.doc; i = 0; n = len(body)
        while i < n:
            ln = body[i]; s = ln.strip()
            if not s: i += 1; continue
            if s.startswith('```'):
                j = i + 1; buf = []
                while j < n and not body[j].strip().startswith('```'): buf.append(body[j]); j += 1
                self.code(buf); i = j + 1; continue
            if s.startswith('= '):
                self.module(s[2:].strip()); i += 1; continue
            if s == '---': self.rule(); i += 1; continue
            m = re.match(r'^(#{1,3})\s+(.*)', s)
            if m:
                lvl = len(m.group(1)); h = d.add_heading('', lvl)
                add_inline(h, m.group(2)); i += 1; continue
            m = re.match(r'^>\s*([A-Z]+):\s*(.*)$', s)
            if m:
                typ = m.group(1); buf = [m.group(2)] if m.group(2) else []
                j = i + 1
                while j < n and (body[j].startswith('  ') or body[j].startswith('\t')) and body[j].strip():
                    buf.append(body[j].strip()); j += 1
                self.callout(typ, buf); i = j; continue
            if s.startswith('|'):
                rows = []; j = i
                while j < n and body[j].strip().startswith('|'):
                    cells = [c.strip() for c in body[j].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c): rows.append(cells)
                    j += 1
                self.table(rows); i = j; continue
            m = re.match(r'^[-•]\s+(.*)', s)
            if m:
                p = d.add_paragraph(style='List Bullet'); add_inline(p, m.group(1)); i += 1; continue
            m = re.match(r'^(\d+)[.)]\s+(.*)', s)
            if m:
                p = d.add_paragraph(style='List Number'); add_inline(p, m.group(2)); i += 1; continue
            m = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', s)
            p = d.add_paragraph(); add_inline(p, s); i += 1
        return d

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    R = Renderer(); R.render(open(src, encoding='utf-8').read()).save(out); print('wrote', out)

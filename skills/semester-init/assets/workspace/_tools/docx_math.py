"""Справжні формули (рівняння Word / OMML) у .docx з LaTeX.

LaTeX → MathML (latex2mathml) → OMML (MML2OMML.XSL з Microsoft Office). Рівняння редагуються у Word
і в LibreOffice Writer як звичайні формули.

Використання в build_report.py (шлях від папки роботи <дисципліна>/<робота>/):
    import sys; sys.path.insert(0, "../../_tools")
    from docx_math import equation, inline_equation
    equation(doc.add_paragraph(), r"t_{\\text{пд}} = t_{\\text{н}} + m \\cdot t_{\\text{к}}", number="2.1")
    p = doc.add_paragraph("де "); inline_equation(p, r"t_{\\text{н}}"); p.add_run(" – латентність")

- без number – окремий абзац по центру (виносне рівняння);
- з number – таблиця 1×3 без рамок: порожня клітинка | рівняння по центру | «(number)» праворуч
  (звичний для звітів вигляд; дроби й суми повного розміру);
- equation() замінює переданий абзац, тож нею ж можна переробити текстову формулу в готовому .docx.
Кирилицю в індексах і словах писати через \\text{...}; множення – \\cdot; дроби – \\frac; кома в числах – 0{,}5.
"""
from pathlib import Path

from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm
from latex2mathml.converter import convert
from lxml import etree

_XSL_CANDIDATES = [
    r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files (x86)\Microsoft Office\root\Office16\MML2OMML.XSL",
    r"C:\Program Files\Microsoft Office\Office16\MML2OMML.XSL",
]
_xslt = None


def _transform():
    global _xslt
    if _xslt is None:
        path = next((p for p in _XSL_CANDIDATES if Path(p).exists()), None)
        if path is None:
            raise FileNotFoundError("MML2OMML.XSL не знайдено – потрібен встановлений Microsoft Office")
        _xslt = etree.XSLT(etree.parse(path))
    return _xslt


def omml(latex, size_pt=14):
    """LaTeX → елемент <m:oMath> (шрифт Cambria Math потрібного розміру)."""
    mathml = etree.fromstring(convert(latex).encode("utf-8"))
    root = _transform()(mathml).getroot()
    o_math = root if root.tag == qn("m:oMath") else root.find(qn("m:oMath"))
    for r in o_math.iter(qn("m:r")):
        rpr = r.find(qn("w:rPr"))
        if rpr is None:
            rpr = etree.Element(qn("w:rPr"))
            r.insert(0 if r.find(qn("m:rPr")) is None else 1, rpr)
        for child in list(rpr):
            if child.tag in (qn("w:rFonts"), qn("w:sz"), qn("w:szCs")):
                rpr.remove(child)
        fonts = etree.SubElement(rpr, qn("w:rFonts"))
        for a in ("ascii", "hAnsi", "cs", "eastAsia"):
            fonts.set(qn(f"w:{a}"), "Cambria Math")
        for tag in ("w:sz", "w:szCs"):
            etree.SubElement(rpr, qn(tag)).set(qn("w:val"), str(size_pt * 2))
    return o_math


def inline_equation(paragraph, latex, size_pt=14):
    """Рівняння всередині рядка тексту (дописується після наявних ранів)."""
    paragraph._p.append(omml(latex, size_pt))


def _clear(paragraph):
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)


def _display(paragraph, latex, size_pt):
    _clear(paragraph)
    pf = paragraph.paragraph_format
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para = etree.SubElement(paragraph._p, qn("m:oMathPara"))
    para.append(omml(latex, size_pt))
    return paragraph


def _no_borders(tbl):
    tbl_pr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tbl_pr.append(borders)


def equation(paragraph, latex, number=None, size_pt=14, text_width_cm=17.0, num_width_cm=1.3):
    """Замінити абзац виносним рівнянням; з number – рівнянням з номером праворуч. Повертає абзац рівняння."""
    if number is None:
        return _display(paragraph, latex, size_pt)
    doc = paragraph.part.document
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    _no_borders(table._tbl)
    widths = [num_width_cm, text_width_cm - 2 * num_width_cm, num_width_cm]
    for gc, w in zip(table._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w * 567)))
    cells = table.rows[0].cells
    for c, w in zip(cells, widths):
        c.width = Cm(w)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for c in (cells[0], cells[2]):  # без внутрішніх полів, щоб «(2.10)» не переносився
        mar = OxmlElement("w:tcMar")
        for side in ("left", "right"):
            el = OxmlElement(f"w:{side}")
            el.set(qn("w:w"), "0")
            el.set(qn("w:type"), "dxa")
            mar.append(el)
        c._tc.get_or_add_tcPr().append(mar)
    template = paragraph._p.pPr
    for c in cells:  # формат абзаців клітинок – як у вихідного абзацу (інтервал, без відступу)
        p = c.paragraphs[0]
        if template is not None:
            p._p.insert(0, etree.fromstring(etree.tostring(template)))
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0)
    eq_p = _display(cells[1].paragraphs[0], latex, size_pt)
    num_p = cells[2].paragraphs[0]
    num_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    num_p.add_run(f"({number})")
    paragraph._p.addprevious(table._tbl)
    paragraph._p.getparent().remove(paragraph._p)
    return eq_p

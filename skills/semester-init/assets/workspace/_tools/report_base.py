"""Каркас звіту (python-docx): ДСТУ-подібне оформлення, титул з _profile.json (university, department, city, group,
title_name, year). Студент пише зміст сам; каркас дає лише оформлення, структуру й рівняння Word.

Використання в <дисципліна>/<робота>/build_report.py:
    import sys; sys.path.insert(0, "../../_tools")
    from report_base import Report
    r = Report()
    r.title_page(discipline="Назва дисципліни", kind="ЛАБОРАТОРНА РОБОТА", number=2,
                 topic="ДОСЛІДЖЕННЯ …", variant_line="Варіант 3 – …",
                 teacher=["доц. каф. …, к.т.н.", "ПРІЗВИЩЕ І. Б."])
    r.heading("2 ДОСЛІДЖЕННЯ …", center=True); r.para()
    r.heading("2.1 Мета роботи"); r.para("…")
    r.equation(r"S_p = \\frac{T_1}{T_p}", number="2.1")
    r.table("Таблиця 2.1 – …", ["p", "T"], [[1, "3,4"]], widths=[3, 4])
    r.save("<група>_<Прізвище>_пз2.docx")           # потім PDF: _tools/docx_to_pdf.ps1
Оформлення: A4, Times New Roman 14, інтервал 1,5, абзац 1,25 см, поля 2,5/1,5/2/2 см, номер сторінки вгорі праворуч.
"""
import json
import os
import sys

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_math import equation as _equation, inline_equation  # noqa: E402

C, J, L = WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.LEFT
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def profile():
    return json.load(open(os.path.join(ROOT, '_profile.json'), encoding='utf-8'))


def fmt(x, d=2):
    """Число з комою: fmt(3.14159) -> '3,14'."""
    return f"{x:.{d}f}".replace(".", ",")


class Report:
    def __init__(self):
        self.doc = doc = Document()
        st = doc.styles["Normal"]
        st.font.name, st.font.size = "Times New Roman", Pt(14)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.paragraph_format.space_after = st.paragraph_format.space_before = Pt(0)
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(2.5), Cm(1.5), Cm(2), Cm(2)
        sec.different_first_page_header_footer = True
        hp = sec.header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run = hp.add_run()
        for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
            el = OxmlElement("w:fldChar" if tag else "w:instrText")
            if tag:
                el.set(qn("w:fldCharType"), tag)
            else:
                el.set(qn("xml:space"), "preserve"); el.text = text
            run._r.append(el)

    def para(self, text="", align=J, indent=True, bold=False, spacing=1.5, italic=False, keep=False):
        p = self.doc.add_paragraph()
        p.alignment = align
        pf = p.paragraph_format
        pf.line_spacing, pf.keep_with_next = spacing, keep
        pf.first_line_indent = Cm(1.25) if indent else Cm(0)
        if text:
            r = p.add_run(text)
            r.bold, r.italic = bold, italic
        return p

    def heading(self, text, center=False):
        return self.para(text, C if center else J, indent=not center, bold=True, keep=True)

    def bullet(self, text):
        return self.para("– " + text)

    def picture(self, path, width_cm, caption):
        p = self.para(align=C, indent=False, spacing=1.0, keep=True)
        p.add_run().add_picture(path, width=Cm(width_cm))
        self.para(caption, C, indent=False)

    def equation(self, latex, number=None):
        """Справжнє рівняння Word; з number – з номером праворуч."""
        return _equation(self.doc.add_paragraph(), latex, number=number)

    def inline(self, paragraph, latex):
        inline_equation(paragraph, latex)

    def table(self, caption, header, rows, widths=None, size=12):
        """Таблиця з повтором шапки при переносі; рядки не розриваються."""
        self.para(caption, L, keep=True)
        t = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        t.style, t.alignment, t.autofit = "Table Grid", WD_TABLE_ALIGNMENT.CENTER, False
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for i, row in enumerate([header] + rows):
            for j, val in enumerate(row):
                c = t.cell(i, j)
                c.text = ""
                p = c.paragraphs[0]
                p.alignment = C
                p.paragraph_format.first_line_indent = Cm(0)
                r = p.add_run(str(val))
                r.font.size, r.bold = Pt(size), i == 0
                if widths:
                    c.width = Cm(widths[j])
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        if widths:
            for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
                gc.set(qn("w:w"), str(int(w * 567)))
        self.para()
        return t

    def code(self, path, size=9):
        """Лістинг (лише якщо код вимагає завдання)."""
        for line in open(path, encoding="utf-8-sig").read().rstrip("\n").split("\n"):
            p = self.doc.add_paragraph()
            p.paragraph_format.line_spacing, p.paragraph_format.first_line_indent = 1.0, Cm(0)
            r = p.add_run(line or " ")
            r.font.name, r.font.size = "Courier New", Pt(size)
            r.element.rPr.rFonts.set(qn("w:eastAsia"), "Courier New")

    def title_page(self, discipline, kind, number, topic, teacher, variant_line=None, year=None):
        """Титул: МОН → ЗВО → кафедра → дисципліна → робота → Виконав / Прийняв → Харків."""
        pr = profile()
        year = year or pr.get("year", 2026)
        for t in ("Міністерство освіти і науки України",
                  pr["university"]):
            self.para(t, C, False, spacing=1.0)
        for _ in range(3):
            self.para(spacing=1.0)
        self.para(pr["department"], C, False, spacing=1.0)
        for _ in range(4):
            self.para(spacing=1.0)
        self.para("Дисципліна:", C, False, spacing=1.0)
        self.para(f"«{discipline}»", C, False, spacing=1.0)
        for _ in range(4):
            self.para(spacing=1.0)
        self.para(f"{kind} №{number}", C, False, bold=True)
        self.para(f"«{topic}»", C, False, bold=True)
        if variant_line:
            self.para(variant_line, C, False)
        for _ in range(8):
            self.para(spacing=1.0)
        sign = self.doc.add_table(rows=1, cols=2)
        left = ["Виконав:", f"ст. гр. {pr['group']}", pr["title_name"]]
        right = ["Прийняв:", *teacher, "з оцінкою «__________»", f"«___» ______________ {year} р."]
        for cell, lines in zip(sign.rows[0].cells, (left, right)):
            cell.text = ""
            for i, line in enumerate(lines):
                p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
                p.paragraph_format.first_line_indent = Cm(0)
                p.add_run(line)
        for _ in range(8):
            self.para(spacing=1.0)
        self.para(f"{pr['city']} {year}", C, False, spacing=1.0).runs[0].add_break(WD_BREAK.PAGE)

    def save(self, path):
        self.doc.save(path)
        print("->", path)

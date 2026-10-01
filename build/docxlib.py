"""Minimal WordprocessingML writer on top of python-docx, reusing the styles,
header, footer and page setup of the companion TRI article (template docx)."""
from __future__ import annotations

import copy
import re
from xml.sax.saxutils import escape

from docx import Document
from docx.oxml import parse_xml
from docx.shared import Emu
from PIL import Image

import texmath

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')

TOKEN = re.compile(r"(\$[^$]+\$|\[\[[^\]]+\]\]|\*\*[^*]+\*\*|\*[^*]+\*)")


def run_xml(text, italic=False, bold=False, sub=False, sup=False, font=None, size=None, color=None):
    rpr = ""
    if font:
        rpr += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}" w:cs="{font}"/>'
    if bold:
        rpr += "<w:b/><w:bCs/>"
    if italic:
        rpr += "<w:i/><w:iCs/>"
    if color:
        rpr += f'<w:color w:val="{color}"/>'
    if size:
        rpr += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if sub:
        rpr += '<w:vertAlign w:val="subscript"/>'
    elif sup:
        rpr += '<w:vertAlign w:val="superscript"/>'
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


class Cites:
    def __init__(self, refs):
        self.refs = refs
        self.order = []

    def number(self, key):
        if key not in self.refs:
            raise KeyError(f"unknown reference {key}")
        if key not in self.order:
            self.order.append(key)
        return self.order.index(key) + 1

    def label(self, keys):
        nums = sorted({self.number(k.strip()) for k in keys.split(",")})
        parts, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            if j - i >= 2:
                parts.append(f"{nums[i]}–{nums[j]}")
            else:
                parts.extend(str(n) for n in nums[i:j + 1])
            i = j + 1
        return ",".join(parts)


def markup_runs(text, cites, **base):
    """Inline markup: $tex$ symbols, [[refkeys]] citations, **bold**, *italic*."""
    out = []
    for tok in TOKEN.split(text):
        if not tok:
            continue
        if tok.startswith("$"):
            for t, st in texmath.inline(tok[1:-1]):
                out.append(run_xml(t, italic=st["italic"] or base.get("italic", False),
                                   bold=base.get("bold", False), sub=st["sub"], sup=st["sup"],
                                   font=base.get("font"), size=base.get("size"), color=base.get("color")))
        elif tok.startswith("[["):
            out.append(run_xml(cites.label(tok[2:-2]), sup=True, font=base.get("font"),
                               size=base.get("size"), color=base.get("color")))
        elif tok.startswith("**"):
            out.extend(markup_runs(tok[2:-2], cites, **dict(base, bold=True)))
        elif tok.startswith("*"):
            out.extend(markup_runs(tok[1:-1], cites, **dict(base, italic=True)))
        else:
            out.append(run_xml(tok, **{k: v for k, v in base.items() if k in
                                       ("italic", "bold", "font", "size", "color")}))
    return "".join(out)


class Builder:
    def __init__(self, template, refs, header_title):
        self.doc = Document(template)
        body = self.doc.element.body
        for child in list(body):
            if child.tag.endswith("}sectPr"):
                continue
            body.remove(child)
        # drop relationships of the template body (images, hyperlinks)
        part = self.doc.part
        keep_types = ("styles", "numbering", "settings", "webSettings", "fontTable", "theme",
                      "footnotes", "comments", "header", "footer")
        for rId, rel in list(part.rels.items()):
            if not any(rel.reltype.endswith("/" + k) for k in keep_types):
                part.rels.pop(rId)
        # header text
        hdr = self.doc.sections[0].header
        for t in hdr._element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
            if t.text and t.text.strip() and t.text != "Padilla-Villanueva":
                t.text = header_title
        self.body = body
        self.sect = body[-1]
        self.cites = Cites(refs)
        self.refs = refs

    def _append(self, xml):
        el = parse_xml(f'<w:wrap {NS}>{xml}</w:wrap>')
        for child in list(el):
            self.sect.addprevious(child)

    def par(self, text, style="BodyText", ppr_extra="", **base):
        runs = markup_runs(text, self.cites, **base)
        self._append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr_extra}</w:pPr>{runs}</w:p>')

    def heading(self, text, level=1):
        self.par(text, style=f"Heading{level}")

    def equation(self, tex, number):
        omml = texmath.display(tex)
        xml = (
            '<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="9360"/><w:jc w:val="center"/>'
            '<w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/>'
            '<w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>'
            '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="0" w:type="dxa"/>'
            '<w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr>'
            '<w:tblGrid><w:gridCol w:w="8660"/><w:gridCol w:w="700"/></w:tblGrid>'
            '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
            '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="8660"/><w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:keepLines/><w:spacing w:before="60" w:after="60"/>'
            '<w:jc w:val="center"/></w:pPr>'
            f'<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>{omml}</m:oMathPara></w:p></w:tc>'
            '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="700"/><w:vAlign w:val="center"/></w:tcPr>'
            '<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:before="60" w:after="60"/><w:jc w:val="right"/></w:pPr>'
            f'{run_xml(f"({number})")}</w:p></w:tc></w:tr></w:tbl>')
        self._append(xml)

    def figure(self, path, width_in):
        rId, _ = self.doc.part.get_or_add_image(path)
        with Image.open(path) as im:
            w, h = im.size
        cx = int(width_in * 914400)
        cy = int(cx * h / w)
        xml = (
            '<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:keepNext/><w:spacing w:before="160" w:after="60"/>'
            '<w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            '<wp:docPr id="101" name="Figure 1" descr="Figure 1"/><wp:cNvGraphicFramePr>'
            '<a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="102" name="fig1.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rId}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic>'
            '</wp:inline></w:drawing></w:r></w:p>')
        self._append(xml)

    def table(self, col_widths, header_rows, rows, align=None, font="Calibri", size=17):
        """header_rows: list of lists of (text, span); rows: list of lists of text."""
        n = len(col_widths)
        align = align or (["left"] + ["center"] * (n - 1))
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)
        xml = ('<w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:type="dxa" w:w="%d"/>'
               '<w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
               '<w:tblBorders><w:top w:val="single" w:sz="10" w:space="0" w:color="1F3864"/>'
               '<w:bottom w:val="single" w:sz="10" w:space="0" w:color="1F3864"/>'
               '<w:insideH w:val="single" w:sz="2" w:space="0" w:color="C8C8C8"/>'
               '<w:left w:val="nil"/><w:right w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders>'
               '<w:tblCellMar><w:top w:w="25" w:type="dxa"/><w:left w:w="50" w:type="dxa"/>'
               '<w:bottom w:w="25" w:type="dxa"/><w:right w:w="50" w:type="dxa"/></w:tblCellMar>'
               '<w:tblLook w:val="0020" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" '
               'w:noHBand="0" w:noVBand="0"/></w:tblPr>' % sum(col_widths)) + f"<w:tblGrid>{grid}</w:tblGrid>"

        def cell(text, width, span=1, header=False, al="left", bottom_rule=False, top_rule=False):
            base = {"font": font, "size": size}
            if header:
                base.update(bold=True, color="1F3864")
            runs = markup_runs(text, self.cites, **base)
            borders = ""
            if bottom_rule or top_rule:
                borders = "<w:tcBorders>"
                if top_rule:
                    borders += '<w:top w:val="nil"/>'
                if bottom_rule:
                    borders += '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="1F3864"/>'
                borders += "</w:tcBorders>"
            gs = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
            return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{width}"/>{gs}{borders}<w:vAlign w:val="bottom"/></w:tcPr>'
                    f'<w:p><w:pPr><w:pStyle w:val="Compact"/><w:keepNext/><w:spacing w:before="20" w:after="20" '
                    f'w:line="240" w:lineRule="auto"/><w:jc w:val="{al}"/></w:pPr>{runs}</w:p></w:tc>')

        for hi, hr in enumerate(header_rows):
            xml += '<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>'
            c = 0
            for text, span in hr:
                width = sum(col_widths[c:c + span])
                al = align[c] if span == 1 else "center"
                rule = hi < len(header_rows) - 1 and span > 1 and text != ""
                xml += cell(text, width, span, header=True, al=al, bottom_rule=rule)
                c += span
            xml += "</w:tr>"
        for row in rows:
            xml += '<w:tr><w:trPr><w:cantSplit/></w:trPr>'
            for c, text in enumerate(row):
                xml += cell(text, col_widths[c], al=align[c])
            xml += "</w:tr>"
        xml += "</w:tbl>"
        self._append(xml)

    def references(self, formatter):
        for i, key in enumerate(self.cites.order, 1):
            text = formatter(self.refs[key])
            self.par(f"{i}.\t{text}", style="Bibliography", ppr_extra='<w:spacing w:before="0" w:after="30"/>')

    def save(self, path, core):
        cp = self.doc.core_properties
        for k, v in core.items():
            setattr(cp, k, v)
        self.doc.save(path)

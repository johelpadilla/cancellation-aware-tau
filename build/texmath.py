"""A small LaTeX-subset translator for the note.

display(tex) -> OMML (<m:oMath>) XML string, used for numbered display equations.
inline(tex)  -> list of (text, style) runs, used for symbols inside prose, where
               style is a dict with keys italic / sub / sup.

Supported: letters, digits, operators, Greek (\\alpha ...), \\frac{}{}, \\sqrt{},
_{} and ^{} (also single-token), \\sum and \\max/\\min with limits, \\bar{},
\\hat{}, \\mathrm{}, \\text{}, \\left( \\right) (and | [ ] \\{ \\}), \\quad, \\,,
relations (\\le \\ge \\approx \\in \\subseteq \\setminus \\cdot \\to \\infty \\ne).
"""
from __future__ import annotations

from xml.sax.saxutils import escape

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "zeta": "ζ",
    "eta": "η", "theta": "θ", "kappa": "κ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ",
    "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ", "phi": "φ", "chi": "χ", "psi": "ψ",
    "omega": "ω", "Delta": "Δ", "Gamma": "Γ", "Theta": "Θ", "Lambda": "Λ", "Sigma": "Σ",
    "Phi": "Φ", "Omega": "Ω", "Pi": "Π",
}
SYMS = {
    "le": "≤", "ge": "≥", "leq": "≤", "geq": "≥", "approx": "≈", "in": "∈", "notin": "∉", "ni": "∋",
    "subseteq": "⊆", "subset": "⊂", "setminus": "∖", "cdot": "·", "to": "→", "infty": "∞",
    "ne": "≠", "neq": "≠", "pm": "±", "times": "×", "mid": "|", "sim": "∼", "ldots": "…",
    "cdots": "⋯", "equiv": "≡", "Leftrightarrow": "⇔", "Rightarrow": "⇒", "lvert": "|",
    "rvert": "|", "vert": "|", "lbrace": "{", "rbrace": "}", "{": "{", "}": "}", "cup": "∪",
    "cap": "∩", "emptyset": "∅", "partial": "∂", "prime": "′", "ell": "ℓ", "propto": "∝",
}
FUNCS = {"min", "max", "sgn", "arg", "exp", "log", "Var", "SD", "E", "Pr", "cov"}
UPRIGHT_GREEK = set("ΔΓΘΛΣΦΩΠ")
OPS = set("+−=<>()[]{},.;:!|/·≤≥≈∈∋∉⊆⊂∖→∞≠±×∼…⋯≡⇔⇒∪∩∅′'")


# ---------------------------------------------------------------- tokenizer / parser
def tokenize(s):
    toks, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            j = i + 1
            if j < len(s) and not s[j].isalpha():
                toks.append(("cmd", s[j]))
                i = j + 1
                continue
            while j < len(s) and s[j].isalpha():
                j += 1
            toks.append(("cmd", s[i + 1:j]))
            i = j
        elif c in "{}^_":
            toks.append((c, c))
            i += 1
        elif c == " ":
            i += 1
        else:
            toks.append(("chr", "−" if c == "-" else c))
            i += 1
    return toks


class Parser:
    def __init__(self, s):
        self.t = tokenize(s)
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.i += 1
        return tok

    def group(self):
        """Parse a {...} group or a single atom."""
        k, v = self.peek()
        if k == "{":
            self.take()
            seq = self.seq(stop="}")
            self.take()
            return ("seq", seq)
        return self.atom()

    def seq(self, stop=None):
        out = []
        while True:
            k, v = self.peek()
            if k is None or (stop == "}" and k == "}") or (stop == "right" and k == "cmd" and v == "right"):
                return out
            a = self.atom()
            if a is None:
                continue
            # scripts
            sub = sup = None
            while self.peek()[0] in ("_", "^"):
                kk, _ = self.take()
                g = self.group()
                if kk == "_":
                    sub = g
                else:
                    sup = g
            if sub is not None or sup is not None:
                if a[0] == "nary":
                    a = ("nary", a[1], sub, sup)
                elif a[0] == "func" and a[1] in ("max", "min", "arg max"):
                    a = ("limlow", a, sub)
                else:
                    a = ("script", a, sub, sup)
            out.append(a)

    def atom(self):
        k, v = self.take()
        if k == "chr":
            return ("chr", v)
        if k == "{":
            seq = self.seq(stop="}")
            self.take()
            return ("seq", seq)
        if k == "cmd":
            if v in GREEK:
                return ("chr", GREEK[v])
            if v in SYMS:
                return ("chr", SYMS[v])
            if v == "frac":
                return ("frac", self.group(), self.group())
            if v == "sqrt":
                return ("sqrt", self.group())
            if v in ("bar", "overline"):
                return ("bar", self.group())
            if v == "hat":
                return ("hat", self.group())
            if v == "tilde":
                return ("tilde", self.group())
            if v in ("mathrm", "text", "operatorname"):
                g = self.group()
                return ("rm", g, v == "text")
            if v == "sum":
                return ("nary", "∑", None, None)
            if v in FUNCS:
                return ("func", v)
            if v == "argmax":
                return ("func", "arg max")
            if v == "left":
                _, d1 = self.take()
                d1 = {"lvert": "|", "vert": "|", "{": "{", "lbrace": "{"}.get(d1, d1)
                inner = self.seq(stop="right")
                self.take()
                _, d2 = self.take()
                d2 = {"rvert": "|", "vert": "|", "}": "}", "rbrace": "}"}.get(d2, d2)
                return ("delim", d1, d2, inner)
            if v == "quad":
                return ("space", "\u2003")
            if v == "qquad":
                return ("space", "\u2003\u2003")
            if v in (",", ";", ":"):
                return ("space", "\u2009")
            if v == " ":
                return ("space", " ")
            if v == "!":
                return None
            raise ValueError(f"unsupported command \\{v}")
        if k in ("_", "^"):
            raise ValueError("script without base")
        return None


# ---------------------------------------------------------------- OMML output
def _mr(text, plain=False, normal=False):
    rpr = ""
    if normal:
        rpr = "<m:rPr><m:nor/></m:rPr>"
    elif plain:
        rpr = '<m:rPr><m:sty m:val="p"/></m:rPr>'
    return f'<m:r>{rpr}<m:t xml:space="preserve">{escape(text)}</m:t></m:r>'


def _opfix(g):
    """A script that consists only of operator characters is emitted as text."""
    if g is None:
        return None
    items = g[1] if g[0] == "seq" else [g]
    if items and all(n[0] == "chr" and n[1] in "+−=*" for n in items):
        return ("rm", ("seq", items), True)
    return g


def _o(node, rm=False):
    kind = node[0]
    if kind == "chr":
        c = node[1]
        plain = rm or c in OPS or c.isdigit() or c in UPRIGHT_GREEK
        return _mr(c, plain=plain)
    if kind == "space":
        return _mr(node[1], normal=True)
    if kind == "seq":
        return "".join(_o(n, rm) for n in node[1])
    if kind == "rm":
        g, is_text = node[1], node[2]
        try:
            return _mr(_plain_text(g), normal=True)
        except ValueError:
            return _o(g, rm=True)
    if kind == "func":
        return _mr(node[1], normal=True)
    if kind == "frac":
        return f"<m:f><m:num>{_o(node[1], rm)}</m:num><m:den>{_o(node[2], rm)}</m:den></m:f>"
    if kind == "sqrt":
        return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{_o(node[1], rm)}</m:e></m:rad>'
    if kind == "bar":
        return f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{_o(node[1], rm)}</m:e></m:bar>'
    if kind in ("hat", "tilde"):
        ch = "̂" if kind == "hat" else "̃"
        return f'<m:acc><m:accPr><m:chr m:val="{ch}"/></m:accPr><m:e>{_o(node[1], rm)}</m:e></m:acc>'
    if kind == "delim":
        d1, d2, inner = node[1], node[2], node[3]
        return (f'<m:d><m:dPr><m:begChr m:val="{escape(d1)}"/><m:endChr m:val="{escape(d2)}"/></m:dPr>'
                f"<m:e>{''.join(_o(n, rm) for n in inner)}</m:e></m:d>")
    if kind == "script":
        base, sub, sup = node[1], node[2], node[3]
        b = _o_full(base, rm)
        sub = _opfix(sub)
        sup = _opfix(sup)
        if sub is not None and sup is not None:
            return f"<m:sSubSup><m:e>{b}</m:e><m:sub>{_o(sub, rm)}</m:sub><m:sup>{_o(sup, rm)}</m:sup></m:sSubSup>"
        if sub is not None:
            return f"<m:sSub><m:e>{b}</m:e><m:sub>{_o(sub, rm)}</m:sub></m:sSub>"
        return f"<m:sSup><m:e>{b}</m:e><m:sup>{_o(sup, rm)}</m:sup></m:sSup>"
    if kind == "nary":
        chr_, sub, sup = node[1], node[2], node[3]
        pr = f'<m:naryPr><m:chr m:val="{chr_}"/><m:limLoc m:val="undOvr"/>'
        pr += '<m:subHide m:val="1"/>' if sub is None else ""
        pr += '<m:supHide m:val="1"/>' if sup is None else ""
        pr += "</m:naryPr>"
        # the summand is whatever follows; OMML needs it inside <m:e>; we emit an
        # empty body and let the following runs flow (renders correctly in Word/LO)
        return (f"<m:nary>{pr}<m:sub>{_o(sub, rm) if sub is not None else ''}</m:sub>"
                f"<m:sup>{_o(sup, rm) if sup is not None else ''}</m:sup><m:e/></m:nary>")
    if kind == "limlow":
        f, sub = node[1], node[2]
        return f"<m:limLow><m:e>{_o(f)}</m:e><m:lim>{_o(sub, rm)}</m:lim></m:limLow>"
    raise ValueError(kind)


def _attach_nary_bodies(nodes):
    """Move the terms that follow a sum into its body, up to a top-level
    relation or separator, so that OMML sums contain their summands."""
    out, i = [], 0
    stops = {"=", "≤", "≥", "≈", ",", ";", "⇔", "<", ">", "\u2003"}
    while i < len(nodes):
        n = nodes[i]
        if n[0] == "nary":
            j = i + 1
            body = []
            while j < len(nodes):
                m = nodes[j]
                if (m[0] == "chr" and m[1] in stops) or (m[0] == "space" and m[1].startswith("\u2003")):
                    break
                if m[0] == "chr" and m[1] in "+−" and body:
                    break
                body.append(m)
                j += 1
            out.append(("nary_full", n, _attach_nary_bodies(body)))
            i = j
        else:
            if n[0] == "seq":
                n = ("seq", _attach_nary_bodies(n[1]))
            elif n[0] == "delim":
                n = ("delim", n[1], n[2], _attach_nary_bodies(n[3]))
            elif n[0] == "script":
                n = ("script", _attach_nary_bodies([n[1]])[0], n[2], n[3])
            elif n[0] == "frac":
                n = ("frac", ("seq", _attach_nary_bodies(_as_list(n[1]))), ("seq", _attach_nary_bodies(_as_list(n[2]))))
            out.append(n)
            i += 1
    return out


def _as_list(g):
    return g[1] if g[0] == "seq" else [g]


def _o_full(node, rm=False):
    if node[0] == "nary_full":
        nary, body = node[1], node[2]
        chr_, sub, sup = nary[1], nary[2], nary[3]
        pr = f'<m:naryPr><m:chr m:val="{chr_}"/><m:limLoc m:val="undOvr"/>'
        pr += '<m:subHide m:val="1"/>' if sub is None else ""
        pr += '<m:supHide m:val="1"/>' if sup is None else ""
        pr += "</m:naryPr>"
        return (f"<m:nary>{pr}<m:sub>{_o_full(sub) if sub is not None else ''}</m:sub>"
                f"<m:sup>{_o_full(sup) if sup is not None else ''}</m:sup>"
                f"<m:e>{''.join(_o_full(b, rm) for b in body)}</m:e></m:nary>")
    if node[0] == "seq":
        return "".join(_o_full(n, rm) for n in node[1])
    if node[0] == "delim":
        d1, d2, inner = node[1], node[2], node[3]
        return (f'<m:d><m:dPr><m:begChr m:val="{escape(d1)}"/><m:endChr m:val="{escape(d2)}"/></m:dPr>'
                f"<m:e>{''.join(_o_full(n, rm) for n in inner)}</m:e></m:d>")
    if node[0] == "frac":
        return f"<m:f><m:num>{_o_full(node[1], rm)}</m:num><m:den>{_o_full(node[2], rm)}</m:den></m:f>"
    return _o(node, rm)


def _is_bar(n):
    return n[0] == "chr" and n[1] == "|"


def _pair_bars(nodes):
    """Turn bare |...| pairs into delimiter nodes (LibreOffice cannot import bare bars)."""
    def rec(n):
        k = n[0]
        if k == "seq":
            return ("seq", _pair_bars(n[1]))
        if k == "delim":
            return ("delim", n[1], n[2], _pair_bars(n[3]))
        if k == "frac":
            return ("frac", rec(n[1]), rec(n[2]))
        if k in ("sqrt", "bar", "hat", "tilde"):
            return (k, rec(n[1]))
        if k == "script":
            return ("script", rec(n[1]), rec(n[2]) if n[2] is not None else None,
                    rec(n[3]) if n[3] is not None else None)
        if k == "nary":
            return ("nary", n[1], rec(n[2]) if n[2] is not None else None, rec(n[3]) if n[3] is not None else None)
        if k == "rm":
            return ("rm", rec(n[1]), n[2])
        return n
    nodes = [rec(n) for n in nodes]
    out, i = [], 0
    while i < len(nodes):
        n = nodes[i]
        if _is_bar(n):
            j = i + 1
            while j < len(nodes):
                m = nodes[j]
                if _is_bar(m) or (m[0] == "script" and _is_bar(m[1])):
                    break
                j += 1
            if j < len(nodes):
                d = ("delim", "|", "|", nodes[i + 1:j])
                m = nodes[j]
                out.append(d if _is_bar(m) else ("script", d, m[2], m[3]))
                i = j + 1
                continue
        out.append(n)
        i += 1
    return out


def display(tex: str) -> str:
    nodes = _pair_bars(Parser(tex).seq())
    nodes = _attach_nary_bodies(nodes)
    body = "".join(_o_full(n) for n in nodes)
    return f"<m:oMath>{body}</m:oMath>"


# ---------------------------------------------------------------- inline output (text runs)
def _plain_text(g):
    if g[0] == "seq":
        return "".join(_plain_text(n) for n in g[1])
    if g[0] in ("chr", "space"):
        return g[1]
    if g[0] == "rm":
        return _plain_text(g[1])
    if g[0] == "func":
        return g[1]
    raise ValueError(f"cannot flatten {g[0]}")


def _runs(node, style, rm=False):
    kind = node[0]
    if kind == "chr":
        c = node[1]
        it = (not rm) and (c.isalpha() and c not in UPRIGHT_GREEK)
        return [(c, dict(style, italic=it))]
    if kind == "space":
        return [(node[1] if node[1] != "\u2003" else "  ", dict(style, italic=False))]
    if kind == "seq":
        out = []
        for n in node[1]:
            out += _runs(n, style, rm)
        return out
    if kind == "rm":
        return _runs(node[1], style, rm=True)
    if kind == "func":
        return [(node[1], dict(style, italic=False))]
    if kind == "bar":
        inner = _runs(node[1], style, rm)
        t, s = inner[-1]
        inner[-1] = (t + "\u0304", s)
        return inner
    if kind == "hat":
        inner = _runs(node[1], style, rm)
        t, s = inner[-1]
        inner[-1] = (t + "\u0302", s)
        return inner
    if kind == "tilde":
        inner = _runs(node[1], style, rm)
        t, s = inner[-1]
        inner[-1] = (t + "\u0303", s)
        return inner
    if kind == "script":
        base, sub, sup = node[1], node[2], node[3]
        out = _runs(base, style, rm)
        if sub is not None:
            out += _runs(sub, dict(style, sub=True, sup=False), rm)
        if sup is not None:
            out += _runs(sup, dict(style, sup=True, sub=False), rm)
        return out
    if kind == "frac":
        return _runs(node[1], style, rm) + [("/", dict(style, italic=False))] + _runs(node[2], style, rm)
    if kind == "sqrt":
        return [("√", dict(style, italic=False))] + _runs(node[1], style, rm)
    if kind == "delim":
        out = [(node[1], dict(style, italic=False))]
        for n in node[3]:
            out += _runs(n, style, rm)
        return out + [(node[2], dict(style, italic=False))]
    if kind == "nary":
        out = [("Σ", dict(style, italic=False))]
        if node[2] is not None:
            out += _runs(node[2], dict(style, sub=True), rm)
        return out
    if kind == "limlow":
        return _runs(node[1], style, rm) + _runs(node[2], dict(style, sub=True), rm)
    raise ValueError(kind)


def inline(tex: str):
    nodes = Parser(tex).seq()
    base = {"italic": False, "sub": False, "sup": False}
    runs = []
    for n in nodes:
        runs += _runs(n, base)
    # merge adjacent runs with equal style
    merged = []
    for t, s in runs:
        if merged and merged[-1][1] == s:
            merged[-1] = (merged[-1][0] + t, s)
        else:
            merged.append((t, s))
    return merged

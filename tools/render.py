"""Gera o PDF 'Questões de Medicina Legal – Provas de Concursos'.

As questões são recortadas diretamente das páginas originais (vetorial, via
show_pdf_page), preservando texto, figuras e tabelas sem redigitação.
"""
import sys, re, json, collections
sys.path.insert(0, 'tools')
import pymupdf, locate, cfg, gab, provas

A4 = pymupdf.paper_rect("a4")
M_L, M_R, M_T, M_B = 48, 48, 58, 52
AVAIL_W = A4.width - M_L - M_R
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TITLE = "Questões de Medicina Legal – Provas de Concursos"
C_DARK = (0.12, 0.16, 0.24)
C_ACC = (0.10, 0.33, 0.55)
C_GRAY = (0.40, 0.40, 0.40)
C_GAB = (0.05, 0.40, 0.20)

SEL = {}
for line in open('tools/sel.txt', encoding='utf-8'):
    f, r = line.strip().split('|')
    s = set()
    for part in r.split(','):
        a, b = (part.split('-') + [part])[:2]
        s |= set(range(int(a), int(b) + 1))
    SEL[f] = s

# ---------------------------------------------------------------- fontes
def textwidth(t, size, bold=False):
    return pymupdf.Font(fontfile=FONT_B if bold else FONT).text_length(t, fontsize=size)

class Out:
    def __init__(self):
        self.doc = pymupdf.open()
        self.page = None
        self.y = 0
        self.toc = []
        self.stats = []

    def new_page(self):
        self.page = self.doc.new_page(width=A4.width, height=A4.height)
        self.page.insert_font(fontname="dj", fontfile=FONT)
        self.page.insert_font(fontname="djb", fontfile=FONT_B)
        self.y = M_T

    def room(self):
        return A4.height - M_B - self.y

    def ensure(self, h):
        if self.page is None or self.room() < h:
            self.new_page()

    def text(self, t, size=10, bold=False, color=C_DARK, indent=0, gap=3, width=None):
        """Texto com quebra de linha automática."""
        width = width or (AVAIL_W - indent)
        font = pymupdf.Font(fontfile=FONT_B if bold else FONT)
        words = t.split(' ')
        lines, cur = [], ''
        for w in words:
            cand = (cur + ' ' + w).strip()
            if font.text_length(cand, fontsize=size) <= width:
                cur = cand
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        lh = size * 1.32
        self.ensure(lh * min(len(lines), 2) + gap)
        for ln in lines:
            self.ensure(lh)
            self.page.insert_text((M_L + indent, self.y + size), ln, fontname="djb" if bold else "dj",
                                  fontsize=size, color=color)
            self.y += lh
        self.y += gap

    def rule(self, color=(0.8, 0.82, 0.86), w=0.6, gap=6):
        self.ensure(gap * 2)
        self.page.draw_line((M_L, self.y), (A4.width - M_R, self.y), color=color, width=w)
        self.y += gap

    def clip(self, src, pno, rect, scale, cuts=(), reserve=0):
        """Insere recorte da página original; divide em cortes de linha se não couber.
        'reserve' mantém espaço para a linha de gabarito junto do último pedaço."""
        top = rect.y0
        full = A4.height - M_T - M_B
        while top < rect.y1 - 0.5:
            rem = (rect.y1 - top) * scale
            if rem <= self.room() - 2 - reserve:
                part = pymupdf.Rect(rect.x0, top, rect.x1, rect.y1)
            else:
                limit = top + (self.room() - 2 - reserve) / scale
                opts = [c for c in cuts if top + 20 < c <= limit and (rect.y1 - c) * scale > 14]
                if not opts:
                    if self.y > M_T + 5:
                        self.new_page(); continue
                    limit = top + (full - 2) / scale
                    opts = [c for c in cuts if top + 20 < c <= limit] or [min(limit, rect.y1)]
                part = pymupdf.Rect(rect.x0, top, rect.x1, max(opts))
            dest = pymupdf.Rect(M_L, self.y, M_L + part.width * scale, self.y + part.height * scale)
            self.page.show_pdf_page(dest, src, pno, clip=part, keep_proportion=True)
            self.y += dest.height + 2
            top = part.y1

# ---------------------------------------------------------------- origem
def clean_source(path):
    """Abre a prova e remove a marca d'água de fundo (imagem repetida em todas as páginas)."""
    d = pymupdf.open(path)
    cnt = collections.Counter()
    for p in d:
        for info in p.get_image_info(xrefs=True):
            cnt[(info['xref'], tuple(round(v) for v in info['bbox']))] += 1
    n = len(d)
    wm = {x for (x, bb), c in cnt.items() if n >= 3 and c >= n * 0.8 and x}
    for p in d:
        for x in {i['xref'] for i in p.get_image_info(xrefs=True)} & wm:
            try:
                p.delete_image(x)
            except Exception:
                pass
    # marcas d'água em texto grande (ex.: "PROVA APLICADA") em formulários curtos e compartilhados
    for xref in range(1, d.xref_length()):
        try:
            if d.xref_get_key(xref, "Subtype")[1] != "/Form": continue
            s = d.xref_stream(xref)
        except Exception:
            continue
        if s and len(s) < 400 and re.search(rb'/\w+ (\d{2,3})(\.\d+)? Tf', s) and \
                int(re.search(rb'/\w+ (\d{2,3})(\.\d+)? Tf', s).group(1)) >= 40 and b'Tj' in s:
            d.update_stream(xref, b"")
    return d

HEAD = re.compile(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 \-–—/,.()ºª]+$')

def is_heading(l):
    t = l["t"].strip()
    if not t or re.match(r'^\(?[A-Ea-e][\)\.\]]|^\[[A-E]\]', t):
        return False
    if l.get("bold") and len(t) < 45 and not re.search(r'[.:;,?]$', t) and re.match(r'^[A-ZÁÉÍÓÚ][\w-]*( (d[aeo]s?|e|[A-ZÁÉÍÓÚ][\w-]*))*$', t) \
            and len(t.split()) <= 5 and not re.match(r'^(QUEST|Quest)', t):
        return True
    return (HEAD.match(t) and len(t) > 6 and sum(c.isalpha() for c in t) > 5) or \
           re.match(r'^(Área livre|RASCUNHO|Rascunho|Questões de \d+ a \d+|Quest[õo]es \d+ a \d+)$', t)

ALT_LAST = re.compile(r'^\s*(\(E\)\)?|E\)|\[E\]|e\)|E\s|E$|\(D\)\)?|D\)|\[D\]|d\))')
STOP = re.compile(r'^\s*(_{5,}|-{5,}|Atenção|ATENÇÃO|Instrução|INSTRUÇÃO|Instruções|Texto\b|TEXTO\b|Leia |Para responder|Considere o texto|Área livre|Espaço livre|RASCUNHO|Rascunho)')
CODE = re.compile(r'^\s*(\|\||\d{3}_[A-Z0-9_]+|\d{1,3}\s*$|PROVA TIPO|\d+ – PROVA TIPO)')

def trim_tail(lines):
    """Remove textos alheios após a última alternativa: corta somente a partir de um título de
    seção, instrução, código de impressão, rodapé ou grande espaço em branco."""
    if len(lines) < 3:
        return lines
    alts = [i for i, l in enumerate(lines) if l["t"] and ALT_LAST.match(l["t"]) and i > 0]
    start = alts[-1] + 1 if alts else 1
    hs = sorted(l["b"][3] - l["b"][1] for l in lines if l["t"])
    lh = hs[len(hs) // 2] if hs else 10
    prev = lines[start - 1]
    for i in range(start, len(lines)):
        l = lines[i]
        if l["t"] and (STOP.match(l["t"]) or is_heading(l) or CODE.match(l["t"])):
            return lines[:i]
        if l["t"] and l["p"] == prev["p"] and l["col"] == prev["col"] and l["b"][1] - prev["b"][3] > lh * 2.6 and alts:
            return lines[:i]
        if l["t"]:
            prev = l
    return lines

def segments(doc, q, seq_index, seq, ce=False):
    """Agrupa as linhas da questão por página/coluna e calcula retângulos de recorte."""
    lines = trim_tail([l for l in q["lines"]])
    if ce:
        # itens Certo/Errado: continuação recuada; linha na margem = comando do próximo bloco
        st = lines[0]
        for i, l in enumerate(lines[1:], 1):
            if l["t"] and (l["p"] != st["p"] or l["col"] == st["col"]) and l["b"][0] <= st["b"][0] + 2:
                lines = lines[:i]; break
    while len(lines) > 1 and is_heading(lines[-1]):
        lines.pop()
    # linha "F" (atravessa o vão) em página de duas colunas: se houver texto da outra coluna na mesma
    # altura, a linha pertence à coluna esquerda (caixa de texto apenas extrapolada)
    for l in lines:
        if l["col"] == 'F' and l.get("split"):
            same = [o for o in seq if o["p"] == l["p"] and o["col"] == 'R' and o["t"]
                    and o["b"][1] < l["b"][3] - 1 and o["b"][3] > l["b"][1] + 1]
            same = [o for o in same if 0 < l["b"][2] - o["b"][0] < 30]
            if same and l["b"][0] < l["split"]:
                l["col"] = 'L'; l["b"][2] = min(l["b"][2], min(o["b"][0] for o in same) - 3)
    groups = []
    for l in lines:
        key = (l["p"], 'F' if l["col"] in 'FS' else l["col"])
        if groups and groups[-1][0] == key:
            groups[-1][1].append(l)
        else:
            groups.append((key, [l]))
    segs = []
    for gi, ((p, col), ls) in enumerate(groups):
        page = doc[p]
        W = page.rect.width
        pl = [l for l in seq if l["p"] == p and l["t"]] or ls
        lm = min(l["b"][0] for l in pl); rm = max(l["b"][2] for l in pl)
        if col == 'L':
            x0 = lm - 4; x1 = max([l["b"][2] for l in pl if l["col"] == 'L'] or [rm]) + 4
        elif col == 'R':
            x0 = min([l["b"][0] for l in pl if l["col"] == 'R'] or [lm]) - 4; x1 = rm + 4
        else:
            x0 = lm - 4; x1 = rm + 4
        # colunas: incluir largura total das linhas da questão
        x0 = min(x0, min(l["b"][0] for l in ls) - 2); x1 = max(x1, max(l["b"][2] for l in ls) + 2)
        lsz = [l for l in ls if not l["t"] or re.search(r'\w', l["t"])] or ls
        y0 = min(l["b"][1] for l in lsz) - 3
        y1 = max(l["b"][3] for l in lsz) + 3
        # próxima linha na mesma página/coluna (limite para figuras sem texto)
        last = ls[-1]
        idx = seq_index[id(last)]
        nxt = next((l for l in seq[idx + 1:] if l["t"]), None)
        limit = nxt["b"][1] - 2 if nxt and nxt["p"] == p and (nxt["col"] == last["col"] or col == 'F') and nxt["b"][1] > y1 else None
        if limit is None and gi == len(groups) - 1:
            limit = None
        if limit is not None:
            for dr in page.get_drawings():
                r = dr["rect"]
                if r.x0 >= x0 - 2 and r.x1 <= x1 + 2 and r.y0 >= y1 - 4 and r.y1 <= limit and r.height > 4:
                    y1 = max(y1, r.y1 + 2)
        rect = pymupdf.Rect(max(0, x0), max(0, y0), min(W, x1), min(page.rect.height, y1))
        cuts = sorted({l["b"][3] + 1.5 for l in ls})
        segs.append((p, rect, cuts))
    return segs

def fmt_gab(a):
    if a is None:
        return "não localizado"
    if a in ('*', 'X', 'NULA', 'ANULADA'):
        return f"questão anulada (no gabarito oficial: “{a}”)"
    if a == 'C': a2 = a
    return a

def gab_text(pv, n, d):
    if d is None:
        return "Gabarito: não localizado"
    a = d.get(n)
    if a is None:
        return "Gabarito: não localizado"
    if a in ('*', 'X', 'NULA'):
        return f"Gabarito: questão anulada (marcação “{a}” no gabarito oficial)"
    if pv.get("ce"):
        return f"Gabarito: {a} ({'Certo' if a == 'C' else 'Errado'})"
    return f"Gabarito: {a}"

# ---------------------------------------------------------------- extras (discursivas, prova digitalizada)
def find_rect(doc, pno, start_pat, end_pat=None, col=None):
    page = doc[pno]
    ls = locate.page_lines(page)
    ys = [l for l in ls if re.search(start_pat, l["t"])]
    if not ys: return None
    y0 = ys[0]["b"][1] - 3
    y1 = page.rect.height - 40
    if end_pat:
        ye = [l for l in ls if re.search(end_pat, l["t"]) and l["b"][1] > y0 + 5]
        if ye: y1 = ye[0]["b"][1] - 3
    xs = [l for l in ls if y0 <= l["b"][1] <= y1 and l["t"] and not re.search('pciconcursos|pcimark', l["t"])]
    x0 = min(l["b"][0] for l in xs) - 4; x1 = max(l["b"][2] for l in xs) + 4
    return pymupdf.Rect(x0, y0, x1, y1)

EXTRAS = {}

def extras_ma2012(doc):
    out = []
    p = 10
    r1 = find_rect(doc, p, r'^Quest[ãa]o 01', r'^Quest[ãa]o 02')
    r2 = find_rect(doc, p, r'^Quest[ãa]o 02', r'^Aten')
    if r1: out.append(("Discursiva – Questão 01", [(p, r1)]))
    if r2: out.append(("Discursiva – Questão 02", [(p, r2)]))
    return out

def extras_ma2018(doc):
    p = 10
    r = find_rect(doc, p, r'^A história da medicina legal', None)
    return [("Prova Discursiva", [(p, r)])] if r else []

EXTRAS["p2/medico_legista (3).pdf"] = extras_ma2012
EXTRAS["p2/medico_legista (2).pdf"] = extras_ma2018

# Prova digitalizada (PCDF 2008): regiões definidas a partir das imagens das páginas.
PCDF = json.load(open('tools/pcdf_regions.json', encoding='utf-8'))

# Textos introdutórios compartilhados, necessários para responder a um bloco de questões.
PREFIX = {
    # FCC 2006: "Atenção: Para as questões de números 40 a 50 ... use a chave abaixo" (fica ao fim da Q39)
    "p2/prova_ml02_tipo_001.pdf": (r'^Atenção:', 39, range(40, 51)),
}

def prefix_segments(f, doc, qs, seq):
    if f not in PREFIX:
        return {}
    pat, owner, rng = PREFIX[f]
    q = [q for q in qs if q["n"] == owner][0]
    ls = q["lines"]
    i = next(i for i, l in enumerate(ls) if re.match(pat, l["t"]))
    blk = [l for l in ls[i:] if l["t"] and not re.match(r'^_{5,}', l["t"])]
    p = blk[0]["p"]
    blk = [l for l in blk if l["p"] == p]
    rect = pymupdf.Rect(min(l["b"][0] for l in blk) - 4, min(l["b"][1] for l in blk) - 3,
                        max(l["b"][2] for l in blk) + 4, max(l["b"][3] for l in blk) + 3)
    seg = [(p, rect, sorted({l["b"][3] + 1.5 for l in blk}))]
    return {n: list(seg) for n in rng}

# ---------------------------------------------------------------- principal
def main(outpath):
    out = Out()
    report = []
    body_start = None
    order = provas.PROVAS
    for k, pv in enumerate(order, 1):
        f = pv["arq"]
        sel = SEL.get(f, set())
        d, gsrc = gab.get(f)
        out.new_page()
        if body_start is None: body_start = out.doc.page_count - 1
        out.toc.append([1, f"Prova {k} – {pv['fonte']}", out.doc.page_count])
        # cabeçalho da prova
        band = pymupdf.Rect(M_L - 6, out.y - 6, A4.width - M_R + 6, out.y + 26)
        out.page.draw_rect(band, color=None, fill=(0.91, 0.94, 0.97))
        out.page.insert_text((M_L, out.y + 15), f"PROVA {k}", fontname="djb", fontsize=15, color=C_ACC)
        out.y += 32
        for lab, val in (("Concurso", pv["concurso"]), ("Órgão", pv["orgao"]), ("Cargo", pv["cargo"]),
                         ("Banca", pv["banca"]), ("Ano", pv["ano"])):
            out.text(f"{lab}: {val}", size=10, gap=1)
        arqs = f.split('/')[-1] + (f"  (arquivo idêntico: {pv['dup'].split('/')[-1]})" if pv.get("dup") else "")
        out.text(f"Arquivo da prova: {arqs}", size=8.5, color=C_GRAY, gap=1)
        out.text(f"Gabarito utilizado: {gsrc if d else 'não localizado na pasta'}", size=8.5, color=C_GRAY, gap=1)
        if pv.get("scanned"):
            out.text("Observação: arquivo digitalizado (imagem). O exemplar contém marcações manuscritas do candidato, "
                     "preservadas nos recortes.", size=8.5, color=C_GRAY, gap=1)
        if pv.get("ce"):
            out.text("Observação: prova no modelo Certo/Errado; cada item é julgado isoladamente (C = Certo, E = Errado).",
                     size=8.5, color=C_GRAY, gap=1)
        out.y += 6
        out.rule(color=C_ACC, w=1.2, gap=12)
        count = 0; withg = 0
        items = []
        if pv.get("scanned"):
            src = pymupdf.open(f)
            for it in PCDF:
                items.append((it["label"], it.get("n"), [(r["p"], pymupdf.Rect(*r["rect"]), []) for r in it["regions"]]))
        else:
            src = clean_source(f)
            doc, qs, seq, st = locate.questions(f, **cfg.KW.get(f, {}))
            seq_index = {id(l): i for i, l in enumerate(seq)}
            pref = prefix_segments(f, doc, qs, seq)
            for q in qs:
                if q["n"] in sel:
                    items.append((None, q["n"], pref.get(q["n"], []) + segments(doc, q, seq_index, seq, ce=pv.get("ce", False))))
            if f in EXTRAS:
                for label, regs in EXTRAS[f](src):
                    items.append((label, None, [(p, r, []) for p, r in regs]))
        for label, n, segs in items:
            head = f"Questão {n:02d} – Medicina Legal" if n else f"{label} – Medicina Legal"
            need = 40 + min(sum(r.height for _, r, _ in segs), 120)
            out.ensure(need)
            out.text(head, size=11.5, bold=True, color=C_ACC, gap=1)
            src_lbl = f"Fonte: {pv['fonte']} – " + (f"Questão {n}" if n else label)
            out.text(src_lbl, size=8, color=C_GRAY, gap=4)
            maxw = max(r.width for _, r, _ in segs)
            scale = min(1.22, AVAIL_W / maxw)
            for si, (p, r, cuts) in enumerate(segs):
                out.clip(src, p, r, scale, cuts, reserve=26 if si == len(segs) - 1 else 0)
            out.y += 3
            if n is not None and (pv.get("scanned") and label and label.startswith("Discursiva")):
                gt = "Gabarito: não localizado (questão discursiva)"
            elif n is None:
                gt = "Gabarito: não localizado (questão discursiva)"
            else:
                gt = gab_text(pv, n, d)
            out.ensure(20)
            out.text(gt, size=10.5, bold=True, color=C_GAB if 'não localizado' not in gt else (0.6, 0.25, 0.1), gap=6)
            out.rule(gap=10)
            count += 1
            if 'não localizado' not in gt: withg += 1
        report.append(dict(k=k, fonte=pv["fonte"], arq=f, n=count, g=withg))
    # ------------------------------------------------ capa e índice (inseridos no início)
    ncover = build_cover(out, report)
    for t in out.toc: t[2] += ncover
    # cabeçalho/rodapé
    N = out.doc.page_count
    for i, pg in enumerate(out.doc):
        pg.insert_font(fontname="dj", fontfile=FONT)
        if i >= ncover:
            pg.insert_text((M_L, 30), TITLE, fontname="dj", fontsize=7.5, color=C_GRAY)
            pg.draw_line((M_L, 35), (A4.width - M_R, 35), color=(0.85, 0.86, 0.9), width=0.5)
        pg.draw_line((M_L, A4.height - 34), (A4.width - M_R, A4.height - 34), color=(0.85, 0.86, 0.9), width=0.5)
        foot = f"Página {i + 1} de {N}"
        pg.insert_text((A4.width - M_R - textwidth(foot, 7.5), A4.height - 22), foot, fontname="dj", fontsize=7.5, color=C_GRAY)
    out.doc.set_toc([[1, "Capa e índice", 1]] + out.toc)
    out.doc.set_metadata({"title": TITLE, "subject": "Banco de questões de Medicina Legal organizado por prova"})
    out.doc.save(outpath, garbage=4, deflate=True)
    json.dump(report, open('work/report.json', 'w'), ensure_ascii=False, indent=1)
    return report

def build_cover(out, report):
    doc = out.doc
    total = sum(r["n"] for r in report); tg = sum(r["g"] for r in report)
    rows = [(r["k"], r["fonte"], r["n"], None) for r in report]
    # páginas de início de cada prova (antes da inserção)
    starts = {t[1].split(' – ')[0]: t[2] for t in out.toc}
    per_page = 34
    npages = 1 + (len(rows) + per_page - 1) // per_page
    for i in range(npages):
        doc.new_page(pno=i, width=A4.width, height=A4.height)
    pg = doc[0]
    pg.insert_font(fontname="dj", fontfile=FONT); pg.insert_font(fontname="djb", fontfile=FONT_B)
    y = 200
    pg.draw_rect(pymupdf.Rect(0, 150, A4.width, 330), color=None, fill=(0.91, 0.94, 0.97))
    pg.insert_text((M_L, y), "QUESTÕES DE MEDICINA LEGAL", fontname="djb", fontsize=24, color=C_ACC)
    pg.insert_text((M_L, y + 32), "PROVAS DE CONCURSOS", fontname="djb", fontsize=17, color=C_DARK)
    pg.insert_text((M_L, y + 62), "Banco de questões organizado por prova, com gabarito oficial quando disponível",
                   fontname="dj", fontsize=10.5, color=C_GRAY)
    y = 380
    info = [f"Provas com questões de Medicina Legal: {len(report)}",
            f"Questões selecionadas: {total}",
            f"Questões com gabarito localizado: {tg}   ·   sem gabarito localizado: {total - tg}",
            "",
            "Como usar este material",
            "• As questões foram recortadas diretamente dos cadernos originais, sem redigitação:",
            "  enunciados, alternativas, figuras e tabelas aparecem exatamente como na prova.",
            "• A numeração é a original de cada caderno; a linha “Fonte” permite localizar a questão.",
            "• O gabarito indicado é o do arquivo oficial encontrado na pasta; a origem (definitivo,",
            "  preliminar, após recursos) está informada no cabeçalho de cada prova.",
            "• Provas ordenadas por ano de aplicação; provas sem ano identificado estão ao final."]
    for ln in info:
        bold = ln == "Como usar este material"
        pg.insert_text((M_L, y), ln, fontname="djb" if bold else "dj", fontsize=10.5 if not bold else 11.5,
                       color=C_ACC if bold else C_DARK)
        y += 17 if ln else 10
    # índice
    for i in range(1, npages):
        p = doc[i]; p.insert_font(fontname="dj", fontfile=FONT); p.insert_font(fontname="djb", fontfile=FONT_B)
        y = 70
        if i == 1:
            p.insert_text((M_L, y), "ÍNDICE DAS PROVAS", fontname="djb", fontsize=15, color=C_ACC); y += 28
        chunk = rows[(i - 1) * per_page: i * per_page]
        for k, fonte, n, _ in chunk:
            pgn = starts[f"Prova {k}"] + npages
            left = f"Prova {k:>2} – {fonte}"
            while textwidth(left, 9.2) > AVAIL_W - 110:
                left = left[:-2]
            right = f"{n} quest. · p. {pgn}"
            p.insert_text((M_L, y), left, fontname="dj", fontsize=9.2, color=C_DARK)
            p.insert_text((A4.width - M_R - textwidth(right, 9.2), y), right, fontname="dj", fontsize=9.2, color=C_GRAY)
            p.draw_line((M_L, y + 5), (A4.width - M_R, y + 5), color=(0.9, 0.9, 0.92), width=0.4)
            y += 19
    return npages

if __name__ == "__main__":
    rep = main(sys.argv[1])
    print(sum(r["n"] for r in rep), sum(r["g"] for r in rep))

"""Localiza questões (número + regiões na página) em PDFs de provas."""
import pymupdf, re, json, sys, collections

START = re.compile(r'^\s*(?:QUEST[ÃA]O|Quest[ãa]o)?\s*0*(\d{1,3})\s*(?:[\.\)\-–—:]|\s|$)')
JUNK = re.compile(r'pcimark|pciconcursos|^\s*P[áa]gina\s+\d+\s*(de|/)\s*\d+\s*$|^\s*Planejamento e Execução', re.I)

def page_lines(page, gap=11.5):
    d = page.get_text("dict")
    out = []
    for b in d["blocks"]:
        if b["type"] == 1:
            out.append({"t": "", "b": list(b["bbox"]), "img": True})
            continue
        for l in b["lines"]:
            t = "".join(s["text"] for s in l["spans"]).strip()
            if t:
                bold = any(s["flags"] & 16 or "Bold" in s["font"] for s in l["spans"] if s["text"].strip())
                out.append({"t": t, "b": list(l["bbox"]), "bold": bold})
    # junta palavras separadas (texto justificado) na mesma linha de base
    out.sort(key=lambda l: (round(l["b"][3]), l["b"][0]))
    merged = []
    for l in out:
        m = merged[-1] if merged else None
        W2 = page.rect.width / 2
        if (m and l["t"] and m["t"] and abs(m["b"][3] - l["b"][3]) < 1.5
                and 0 <= l["b"][0] - m["b"][2] < gap
                and not (l["b"][0] - m["b"][2] >= 4 and m["b"][2] <= W2 + 8 and l["b"][0] >= W2 - 8)):
            m["t"] += " " + l["t"]; m["b"][2] = max(m["b"][2], l["b"][2])
            m["b"][1] = min(m["b"][1], l["b"][1])
        else:
            merged.append(dict(l, b=list(l["b"])))
    return merged

def norm(t): return re.sub(r'\d+', '#', t)

def analyze(path, mode="band", gap=11.5):
    doc = pymupdf.open(path)
    pages = []
    for i, p in enumerate(doc):
        pages.append(page_lines(p, gap))
    # header/footer: textos repetidos em muitas páginas
    cnt = collections.Counter()
    def edge(l, pi):
        H = doc[pi].rect.height
        return l["b"][1] < H * 0.1 or l["b"][3] > H * 0.9
    for pi, pl in enumerate(pages):
        for k in {norm(l["t"]) for l in pl if l["t"] and edge(l, pi)}: cnt[k] += 1
    n = len(pages)
    rep = {k for k, c in cnt.items() if n >= 3 and c >= max(3, n * 0.5) and len(k) > 3}
    # imagens repetidas (marca d'água do site) em muitas páginas
    ik = lambda l: tuple(round(v / 6) for v in l["b"])
    icnt = collections.Counter(ik(l) for pl in pages for l in pl if l.get("img"))
    irep = {bb for bb, c in icnt.items() if c >= max(2, n * 0.4)}
    for pi in range(len(pages)):
        pages[pi] = [l for l in pages[pi] if not (l.get("img") and ik(l) in irep)
                     and not (l["t"] and (l["b"][3] - l["b"][1]) > 60 and len(l["t"]) < 40)]
    seq = []  # linhas em ordem de leitura
    for pi, pl in enumerate(pages):
        W = doc[pi].rect.width; mid = W / 2
        H = doc[pi].rect.height
        content = [l for l in pl if not (l["t"] and (JUNK.search(l["t"]) or (norm(l["t"]) in rep and edge(l, pi) and not STYLES[0].match(l["t"]) and not all(ord(c) < 32 for c in l["t"].replace(" ", "")))
                   or (re.fullmatch(r'[-–\s]*\d{1,3}[-–\s]*', l["t"]) and (l["b"][3] < H*0.04 or l["b"][3] > H*0.93))))]
        # imagens muito grandes (fundo de página) descartadas
        content = [l for l in content if not (l.get("img") and (l["b"][2]-l["b"][0]) > W*0.9 and (l["b"][3]-l["b"][1]) > doc[pi].rect.height*0.8)]
        texts = [l for l in content if l["t"]]
        best = None
        for s in range(int(W*0.35), int(W*0.65), 2):
            lf = sum(1 for l in texts if l["b"][2] <= s + 2)
            rt = sum(1 for l in texts if l["b"][0] >= s - 2)
            cross = len(texts) - lf - rt
            if lf >= 5 and rt >= 5:
                key = (cross, abs(s - mid))
                if best is None or key < best[0]: best = (key, s)
        if mode == "single":
            twocol = False
        elif mode == "band":
            twocol = best is not None and (len(texts) - best[0][0]) >= 0.6 * len(texts)
        else:
            twocol = best is not None and best[0][0] <= max(3, len(texts) * 0.15)
        split = best[1] if best else mid
        for l in content:
            x0, y0, x1, y1 = l["b"]
            if twocol and x0 >= split - 2: col = "R"
            elif twocol and x1 <= split + 2: col = "L"
            else: col = "F" if twocol else "S"
            l["col"] = col; l["p"] = pi; l["split"] = split
        if twocol and mode == "simple":
            seq += sorted([l for l in content if l["col"] in "LF"], key=lambda l: (round(l["b"][1]), l["b"][0]))
            seq += sorted([l for l in content if l["col"] == "R"], key=lambda l: (round(l["b"][1]), l["b"][0]))
        elif twocol:
            full = sorted([l for l in content if l["col"] == "F"], key=lambda l: l["b"][1])
            cols = [l for l in content if l["col"] in "LR"]
            prev = -1e9
            for fl in full + [None]:
                lim = fl["b"][1] if fl else 1e9
                band = [l for l in cols if prev <= (l["b"][1] + l["b"][3]) / 2 < lim]
                seq += sorted([l for l in band if l["col"] == "L"], key=lambda l: (round(l["b"][1]), l["b"][0]))
                seq += sorted([l for l in band if l["col"] == "R"], key=lambda l: (round(l["b"][1]), l["b"][0]))
                if fl: seq.append(fl); prev = lim
        else:
            seq += sorted(content, key=lambda l: (round(l["b"][1]), l["b"][0]))
    return doc, pages, seq

STYLES = [
    re.compile(r'^\s*QUEST[ÃA]O\s*0*(\d{1,3})\b', re.I),
    re.compile(r'^\s*0*(\d{1,3})\s*[\.\)]\s*(?:\S|$)'),
    re.compile(r'^\s*0*(\d{1,3})\s*[-–—]\s*\S'),
    re.compile(r'^\s*0*(\d{1,3})\s*$'),
    re.compile(r'^\s*0*(\d{1,3})\s+\S'),
]

def chain_for(seq, rx, lo=1):
    best = {}
    for i, l in enumerate(seq):
        if not l["t"]: continue
        m = rx.match(l["t"])
        if not m: continue
        num = int(m.group(1))
        if num < lo or num > 200: continue
        prevs = [best[k] for k in (num - 1, num - 2, num - 3) if k in best]
        prev = max(prevs, key=lambda c: c[0]) if prevs else None
        chain = (prev[0] + 1, prev[1] + [(i, num)]) if prev else (1, [(i, num)])
        if num not in best or chain[0] > best[num][0]:
            best[num] = chain
    return max(best.values(), key=lambda c: c[0])[1] if best else []

def glyph_chain(seq):
    out = []
    for i, l in enumerate(seq):
        t2 = l["t"].replace(" ", "").replace("\t", "")
        if len(t2) >= 4 and all(ord(c) < 32 for c in t2):
            out.append((i, len(out) + 1))
    return out

def find_starts(seq, style=None):
    if style == "glyph": return glyph_chain(seq)
    """Escolhe, entre os estilos de numeração, a maior cadeia 1,2,3... em ordem de leitura."""
    styles = [STYLES[style]] if style is not None else STYLES
    chains = [chain_for(seq, rx) for rx in styles]
    return max(chains, key=len)

def questions(path, style=None, mode=None, first_page=1, gaps=(11.5, 18, 0)):
    best = None
    for md, gap in [(m, g) for m in ([mode] if mode else ["band", "simple"]) for g in gaps]:
        doc, pages, seq = analyze(path, md, gap)
        seq = [l for l in seq if l["p"] >= first_page - 1]
        starts = find_starts(seq, style)
        if best is None or len(starts) > len(best[3]):
            best = (doc, pages, seq, starts)
    doc, pages, seq, starts = best
    W = doc[0].rect.width
    if not mode and starts and all(seq[i]["b"][0] < W * 0.4 for i, _ in starts):
        for gap in (11.5, 18, 0):
            d2, p2, s2 = analyze(path, "single", gap)
            s2 = [l for l in s2 if l["p"] >= first_page - 1]
            st2 = find_starts(s2, style)
            if len(st2) == len(starts):
                doc, pages, seq, starts = d2, p2, s2, st2
                break
    qs = []
    for k, (i, num) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(seq)
        qs.append({"n": num, "lines": seq[i:end]})
    return doc, qs, seq, starts

def missing(qs):
    ns = [q["n"] for q in qs]
    return [n for n in range(ns[0], ns[-1]) if n not in ns] if ns else []

if __name__ == "__main__":
    kw = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    doc, qs, seq, starts = questions(sys.argv[1], **kw)
    print("MISSING", missing(qs))
    for q in qs:
        txt = " ".join(l["t"] for l in q["lines"])
        print(f'{q["n"]:>3} p{q["lines"][0]["p"]+1}: {txt[:int(sys.argv[2]) if len(sys.argv)>2 else 90]}')

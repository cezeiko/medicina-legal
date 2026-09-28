"""Extração dos gabaritos oficiais: devolve {questão: resposta} por prova."""
import re, pymupdf, functools

def clean(path):
    d = pymupdf.open(path)
    t = " ".join(p.get_text() for p in d)
    t = re.sub(r'pcimarkpci \S+|www\.pciconcursos\.com\.br', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return re.sub(r'( 0){5,}', ' ', t)

ANS = r'([A-E]|\*|X|NULA|ANULADA)'

def pairs(seg, rx=r'\b0*(\d{1,3})\s*[-–:]?\s*' + ANS + r'(?=\s|$)'):
    out = {}
    for m in re.finditer(rx, seg):
        n = int(m.group(1))
        if n not in out: out[n] = m.group(2)
    return out

def split_run(s, last):
    """Divide números colados ('0102...10', '36373839...100') em sequência consecutiva."""
    nums = []; j = 0
    while j < len(s):
        for w in (1, 2, 3):
            v = s[j:j+w]
            exp = (nums[-1] + 1) if nums else (last + 1 if last else None)
            if len(v) == w and v.isdigit() and ((exp is None and int(v) >= 1) or int(v) == exp):
                if exp is None and w == 1 and s[j] == '0':
                    continue
                nums.append(int(v)); j += w; break
        else:
            return None
    return nums

def grid(seg):
    """Blocos de números seguidos das respectivas respostas (fila FIFO)."""
    out = {}; queue = []; last = 0
    for tok in seg.split():
        if re.fullmatch(r'\d{1,3}', tok):
            queue.append(int(tok)); last = int(tok)
        elif re.fullmatch(r'\d{4,}', tok):
            ns = split_run(tok, last)
            if ns: queue += ns; last = ns[-1]
        elif re.fullmatch(r'[A-E]|\*|X|NULA', tok) and queue:
            out.setdefault(queue.pop(0), tok)
    return out

funcab = grid

def after(t, key, n=4000, occ=0):
    i = [m.start() for m in re.finditer(key, t)][occ]
    return t[i:i+n]

G = "P1/", "p2/"
@functools.lru_cache(None)
def T(f): return clean(f)

def get(prova):
    """Retorna (dict, descrição da fonte) para o arquivo de prova."""
    if prova == "P1/prova8.pdf":
        t = T("P1/gab8.pdf"); rows = re.findall(r'\b(\d{1,2}) ([A-D]) ([A-D]) ([A-D]) ([A-D])\b', t)
        return {int(r[0]): r[1] for r in rows}, "gab8.pdf (Prova Tipo 1)"
    if prova == "P1/perito_medico_legista (2).pdf":
        seg = after(T("P1/gabarito (5).pdf"), r'13 - Perito Médico - Legista ', 900)
        seg = seg.split('(*)')[0]
        return pairs(seg), "gabarito (5).pdf – Gabaritos Definitivos, cargo 13 – Perito Médico-Legista"
    if prova == "P1/perito_medico_legista (3).pdf":
        seg = after(T("P1/gabarito_definitivo (2).pdf"), r'Cargo: 3 - Perito Médico-Legista ', 2400)
        return pairs(seg, r'\b(\d{1,2}) ' + ANS + r' [A-ZÁ-Úa-z]'), "gabarito_definitivo (2).pdf – Gabaritos Retificativos, cargo 3 – Perito Médico-Legista"
    if prova == "P1/perito_medico_legista_de_policia_civil.pdf":
        seg = after(T("P1/gabarito_definitivo (1).pdf"), r'Perito Médico Legista de Polícia Civil', 1500)
        return pairs(seg, r'\b(\d{2,3}): ' + ANS), "gabarito_definitivo (1).pdf – Gabarito final, Perito Médico Legista de Polícia Civil"
    if prova in ("P1/perito_medico_legista_e_patologia.pdf", "P1/perito_medico_legista_e_psiquiatria.pdf", "p2/perito_medico_legista.pdf"):
        key = {"P1/perito_medico_legista_e_patologia.pdf": r'Legista/Patologia',
               "P1/perito_medico_legista_e_psiquiatria.pdf": r'Legista/Psiquiatria',
               "p2/perito_medico_legista.pdf": r'Legista \(Geral\)'}[prova]
        seg = after(T("P1/gabarito (3).pdf"), key, 1400)
        return pairs(seg.split('Página')[0] if 'Página' in seg[40:] else seg, r'\b(\d{1,2}) ' + ANS), f"gabarito (3).pdf – Gabarito Definitivo ({key.replace(chr(92),'')})"
    if prova in ("P1/perito_oficial_criminal_medico_legista_ou_medicina_legal.pdf",
                 "P1/perito_oficial_criminal_medico_legista_ou_medicina_legal_psiquiatria.pdf"):
        t = T("P1/gabarito (7).pdf")
        key = r'Perfil: Medicina Legal - Psiquiatria' if 'psiquiatria' in prova else r'Perfil: Medicina Legal CONHECIMENTOS'
        seg = after(t, key, 900)
        return grid(seg), "gabarito (7).pdf – Gabarito PRELIMINAR (único disponível na pasta)"
    if prova in ("P1/s22_01_perito_oficial_medico_legista_medico.pdf",
                 "P1/s23_01_perito_oficial_medico_legista_medico_psiquiatria (1).pdf"):
        key = 'S23 - P. OFIC' if 's23' in prova else 'S22 - P. OFIC'
        seg = after(T("P1/gab_apos_recursos.pdf"), key, 800).split('Questão com')[0]
        return funcab(seg), "gab_apos_recursos.pdf – Gabarito após recursos (" + key.split(' -')[0] + ")"
    if prova == "P1/sgapcac_c_1_perito_caderno_a.pdf":
        seg = after(T("P1/gabaritos (3).pdf"), r'^', 800).split('Gabarito')[0]
        return grid(seg), "gabaritos (3).pdf – Gabaritos oficiais definitivos, Perito Médico-Legista"
    if prova == "P1/prova_pcdf_perito_2008_funiversa.pdf":
        seg = T("P1/gabarito (6).pdf").split('Legenda')[0]
        return grid(seg), "gabarito (6).pdf – Gabarito oficial definitivo após recursos"
    if prova == "p2/caderno_30_medico_legista_a_20130528_143535.pdf":
        seg = after(T("p2/093_13_gabarito_prova_objetiva_ml_20130528_125521.pdf"), r'Prova Tipo A', 600).split('Prova Tipo B')[0]
        return pairs(seg, r'\b(\d{2}) ' + ANS), "093_13_gabarito_prova_objetiva_ml.pdf – Gabarito oficial, Prova Tipo A"
    if prova == "p2/m29_p_medico_perito_legista.pdf":
        seg = after(T("p2/gabaritos_preliminares.pdf"), r'M29 - MÉDICO PERITO', 700).split('GABARITO')[0]
        return funcab(seg), "gabaritos_preliminares.pdf – Gabarito PRELIMINAR (M29)"
    if prova == "p2/medico_legista (2).pdf":
        t = T("p2/gabarito_oficial (1).pdf")
        out = {}
        for code in ('373_SSPMA_APC_CG3_01', '373_SSPMA_APC_003_01'):
            i = t.find(code); seg = t[max(0, i-700):i]
            seg = seg[seg.rfind('Aplicação: 28/1/2018') + 20:] if 'Aplicação: 28/1/2018' in seg else seg
            out.update(grid(seg.split('Gabarito')[0]))
        return out, "gabarito_oficial (1).pdf – Gabaritos oficiais definitivos (CG3 e cargo 003)"
    if prova in ("p2/medico_legista (3).pdf", "p2/policia_civil_medico_legista_caderno_01.pdf"):
        seg = after(T("p2/gabarito.pdf"), r'POLÍCIA CIVIL MÉDICO LEGISTA GABARITO DEFINITIVO TIPO 01', 700).split('* = ')[0]
        return pairs(seg, r'\b(\d{1,2}) – ' + ANS), "gabarito.pdf – Gabarito definitivo, Médico Legista, Tipo 01"
    if prova == "p2/medico_legista.pdf":
        seg = after(T("p2/gabarito_oficial.pdf"), r'Prova Tipo 1', 600).split('Questão anulada')[0]
        return pairs(seg, r'\b(\d{1,2}) ' + ANS), "gabarito_oficial.pdf – Gabarito oficial definitivo, Prova Tipo 1"
    if prova == "p2/medico_legista_3_categoria.pdf":
        seg = after(T("p2/gabaritos (1).pdf"), r'S04 - MÉDICO LEGISTA', 700).split('GABARITO')[0]
        return funcab(seg), "gabaritos (1).pdf – Gabarito da prova objetiva (S04 – Médico Legista 3ª Categoria)"
    if prova in ("p2/medico_legista_de_3_classe_generalista.pdf", "p2/medico_legista_de_3_classe_especialista_em_psiquiatria.pdf"):
        key = r'201 – Médico Legista de 3a Classe – Geral Prova Tipo “A”' if 'generalista' in prova else r'203 – Médico Legista de 3a Classe – Especialista em Psiquiatria Prova Tipo “U”'
        seg = after(T("p2/gabarito (1).pdf"), key, 600)
        seg = re.split(r'Prova Tipo|Brasília-DF|\d{3} – Médico', seg[len(key)-5:])[0]
        return grid(seg), "gabarito (1).pdf – Gabaritos PRELIMINARES (" + key.split(' Prova')[0] + ")"
    if prova == "p2/medico_legista_de_policia_civil (1).pdf":
        seg = after(T("p2/gabarito_preliminar.pdf"), r'005\. PROVA OBJETIVA MÉDICO LEGISTA', 700).split('Data da')[0]
        return pairs(seg, r'\b(\d{1,2}) - ' + ANS), "gabarito_preliminar.pdf – Gabarito PRELIMINAR (005 – Médico Legista de Polícia Civil)"
    if prova == "p2/medico_legista_de_policia_civil.pdf":
        seg = after(T("p2/gabarito (10).pdf"), r'062\. CURSO DE FORMAÇÃO MÉDICO LEGISTA', 1100).split('Pág.')[0]
        return pairs(seg, r'\b(\d{1,3}) - ' + ANS), "gabarito (10).pdf – Gabarito (062 – Curso de Formação Médico Legista)"
    if prova == "p2/perito_medico_legista (1).pdf":
        # o rótulo do cargo aparece no rodapé, DEPOIS da respectiva tabela
        t = T("p2/gabarito (8).pdf"); i = t.find('1064 - Perito Médico Legista')
        seg = t[:i]; seg = seg[seg.rfind('Qst T1 T2 T3 T4'):]
        rows = re.findall(r'\b(\d{1,2}) ([A-D*X]) ([A-D*X]) ([A-D*X]) ([A-D*X])\b', seg)
        out = {}
        for r in rows:
            if int(r[0]) not in out: out[int(r[0])] = r[1]
        return out, "gabarito (8).pdf – Gabarito das provas, 1064 – Perito Médico Legista (coluna T1)"
    if prova == "p2/perito_medico_legista_de_3_classe_medico_legista.pdf":
        seg = after(T("P1/gabarito_oficial (2).pdf"), r'TIPO “01” CARGO: PERITO MÉDICO LEGISTA DE 3ª CLASSE – MÉDICO LEGISTA', 700).split('Universidade')[0]
        return pairs(seg, r'\b(\d{2}) ' + ANS), "gabarito_oficial (2).pdf – Gabarito, Tipo 01, Perito Médico Legista de 3ª Classe – Médico Legista"
    if prova == "p2/prova_medico_legista_versao1.pdf":
        seg = after(T("p2/gabaritos.pdf"), r'Versão 1 ', 900).split('Versão 2')[0]
        return pairs(seg, r'\b(\d{1,3}) - ' + ANS), "gabaritos.pdf – Gabarito oficial da Prova Preambular, Versão 1"
    if prova == "p2/prova_ml02_tipo_001.pdf":
        seg = T("p2/gabarito_ml02_tipo_1_folha_1.pdf")
        return pairs(seg, r'\b(\d{3}) - ' + ANS), "gabarito_ml02_tipo_1_folha_1.pdf – ML02, Tipo 1"
    if prova == "p2/pv_conhec_espec_cargo_4_med_legista.pdf":
        # 1ª página do arquivo = código 260SDSPE_001_01 / CARGO 4: MÉDICO LEGISTA (mesmo código do caderno)
        seg = T("p2/gab_preliminar_conhec_espec_todos_cargos.pdf").split('Gabarito')[0]
        return grid(seg), "gab_preliminar_conhec_espec_todos_cargos.pdf – Gabarito oficial PRELIMINAR, Cargo 4: Médico Legista"
    if prova == "p2/medico_legista (1).pdf":
        # tabela transcrita da imagem do PDF (texto do arquivo usa fonte sem mapeamento de caracteres)
        s = ("B D E A C B A E D D B D A E C * D C B C E A E C E B A C B E B D A C A D E C C D "
             "A D E B A C D A B E D B A C E B D A C A D B E C C C E C E A A B A * A C * D B A").split()
        return {i + 1: a for i, a in enumerate(s)}, "gabarito_definitivo.pdf – Gabarito Oficial Definitivo (Edital n. 10/2021 – SAD/SEJUSP/CGP/POF-PML)"
    if prova == "p2/s01_medico_perito_legista_de_1a_classe.pdf":
        seg = after(T("p2/gab_preliminar_todos_cargos.pdf"), r'LEGISTA', 900).split('GABARITO')[0]
        return funcab(seg), "gab_preliminar_todos_cargos.pdf – Gabarito PRELIMINAR (PEFOCE 2011)"
    if prova == "p2/s01_v_medico_legista.pdf":
        seg = after(T("p2/gabarito_policia_civil.pdf"), r'S01 - MÉDICO', 700).split('GABARITO')[0]
        return funcab(seg), "gabarito_policia_civil.pdf – Gabarito da prova objetiva (S01 – Médico Legista, Prova V)"
    return None, None

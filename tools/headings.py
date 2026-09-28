import sys, re, glob; sys.path.insert(0,'tools'); import locate, cfg
for f in sys.argv[1:]:
    doc, qs, seq, st = locate.questions(f, **cfg.KW.get(f, {}))
    out = []
    for q in qs:
        for l in q["lines"][1:]:
            t = l["t"].strip()
            if 4 < len(t) < 70 and (l.get("bold") or t.isupper()) and not re.match(r'^\(?[A-Ea-e][\)\.]|^[IVX]+[\.\-– ]', t) and sum(c.isalpha() for c in t) > 4:
                out.append(f"{t[:45]}@>{q['n']+1}")
    print("==", f, len(qs), "q | " + " | ".join(out))

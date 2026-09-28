import sys, re; sys.path.insert(0,'tools'); import locate, cfg
f=sys.argv[1]; W=int(sys.argv[3]) if len(sys.argv)>3 else 120
rng=set()
for part in sys.argv[2].split(','):
    a,b=(part.split('-')+[part])[:2]; rng|=set(range(int(a),int(b)+1))
doc,qs,seq,st=locate.questions(f,**cfg.KW.get(f,{}))
for q in qs:
    if q["n"] in rng:
        t=re.sub(r'\s+',' '," ".join(l["t"] for l in q["lines"]))
        t=re.sub(r'^\s*(QUEST[ÃA]O|Quest[ãa]o)?\s*0*\d+\s*[\.\-–—:)]?\s*','',t)
        print(f'{q["n"]}: {t[:W]}')

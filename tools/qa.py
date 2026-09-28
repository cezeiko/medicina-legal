import sys, collections; sys.path.insert(0,'tools')
import render, locate, cfg, provas, pymupdf
issues=collections.Counter(); out=[]
for pv in provas.PROVAS:
    f=pv["arq"]
    if pv.get("scanned"): continue
    sel=render.SEL[f]
    doc,qs,seq,st=locate.questions(f,**cfg.KW.get(f,{}))
    idx={id(l):i for i,l in enumerate(seq)}
    owner={}
    for q in qs:
        for l in q["lines"]: owner[id(l)]=q["n"]
    for q in qs:
        if q["n"] not in sel: continue
        segs=render.segments(doc,q,idx,seq)
        for p,r,c in segs:
            for l in seq:
                if l["p"]!=p or not l["t"]: continue
                cx=(l["b"][0]+l["b"][2])/2; cy=(l["b"][1]+l["b"][3])/2
                if r.contains(pymupdf.Point(cx,cy)) and owner.get(id(l),-1)!=q["n"]:
                    out.append(f'{f.split("/")[1][:28]} Q{q["n"]} p{p+1}: intruso(Q{owner.get(id(l))}) "{l["t"][:50]}"')
                    issues[f]+=1
print(len(out))
for o in out[:400]: print(o)

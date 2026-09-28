import sys; sys.path.insert(0,'tools')
import render, locate, cfg, provas, pymupdf
bad=[]
for pv in provas.PROVAS:
    f=pv["arq"]
    if pv.get("scanned"): continue
    doc,qs,seq,st=locate.questions(f,**cfg.KW.get(f,{}))
    idx={id(l):i for i,l in enumerate(seq)}
    pages={}
    for q in qs:
        if q["n"] not in render.SEL[f]: continue
        for p,r,c in render.segments(doc,q,idx,seq):
            if p not in pages: pages[p]=locate.page_lines(doc[p])
            for l in pages[p]:
                if not l["t"].strip(): continue
                x0,y0,x1,y1=l["b"]
                if x1<r.x0+2 or x0>r.x1-2: continue
                h=y1-y0
                for edge in (r.y0,r.y1):
                    if y0+h*0.25<edge<y1-h*0.25:
                        bad.append(f'{f.split("/")[1][:26]} Q{q["n"]} p{p+1} edge{round(edge)}: "{l["t"][:50]}"')
                # corte lateral
                if y1>r.y0+2 and y0<r.y1-2 and (x0<r.x0-1 and x1>r.x0+5 or x1>r.x1+1 and x0<r.x1-5):
                    bad.append(f'{f.split("/")[1][:26]} Q{q["n"]} p{p+1} LATERAL: "{l["t"][:50]}" {[round(v) for v in l["b"]]} rect {[round(v) for v in r]}')
print(len(bad)); print("\n".join(bad[:150]))

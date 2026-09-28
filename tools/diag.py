import sys; sys.path.insert(0,'tools'); import locate
f=sys.argv[1]; st=int(sys.argv[2])
doc,pages,seq=locate.analyze(f)
rx=locate.STYLES[st]
ch=locate.chain_for(seq,rx)
print('chain',len(ch),ch[0][1] if ch else None,ch[-1][1] if ch else None)
have={n for _,n in ch}
mx=max(have) if have else 0
miss=[n for n in range(1,mx+2) if n not in have]
print('missing',miss[:20])
for n in miss[:4]:
  for i,l in enumerate(seq):
    m=rx.match(l['t'])
    if m and int(m.group(1))==n: print(' cand',n,i,'p',l['p']+1,l['col'],[round(x) for x in l['b']],repr(l['t'][:40]))

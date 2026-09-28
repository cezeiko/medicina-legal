import sys, pymupdf
sys.path.insert(0,'tools'); import locate
doc=pymupdf.open(sys.argv[1]); p=int(sys.argv[2])-1; n=int(sys.argv[3]) if len(sys.argv)>3 else 40
for l in locate.page_lines(doc[p])[:n]: print([round(x) for x in l['b']], repr(l['t'][:60]))

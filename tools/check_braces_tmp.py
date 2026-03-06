import sys
p = sys.argv[1] if len(sys.argv)>1 else 'ui/index.html'
text = open(p, 'r', encoding='utf-8').read()
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
bal = 0
lines = text.splitlines()
for i,line in enumerate(lines,1):
    for ch in line:
        if ch == '{': bal += 1
        elif ch == '}': bal -= 1
        if bal < 0:
            print('NEGATIVE at line', i)
            sys.exit(0)
    # print per-line balance for diagnosis
    print(f"{i:04d}: BAL={bal} | {line.strip()}")
print('\nFINAL_BALANCE', bal)
if bal>0:
    opens=[(i+1,line) for i,line in enumerate(lines) if '{' in line]
    for ln,l in opens[-20:]:
        print('OPEN_AT', ln, l.strip())

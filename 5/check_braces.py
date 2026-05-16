path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\Other.txt'
balance = 0
out = []
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f, 1):
        balance += line.count('{') - line.count('}')
        if i % 4000 == 0:
            out.append((i, balance))
        if i >= 40700:
            out.append((i, balance))
out.append(('final', balance))
with open(r'c:\Games\Vic2LV2\Victoria 2\mod\6\brace_balance.txt', 'w') as f:
    for x in out:
        f.write(str(x) + '\n')

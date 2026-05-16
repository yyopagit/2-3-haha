# -*- coding: utf-8 -*-
path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\Other.txt'
out_path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\brace_result.txt'
balance = 0
min_balance = 0
min_line = 0
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    for i, line in enumerate(f, 1):
        balance += line.count('{') - line.count('}')
        if balance < min_balance:
            min_balance = balance
            min_line = i
with open(out_path, 'w') as f:
    f.write('Min balance: %d at line: %d\n' % (min_balance, min_line))
    f.write('Final balance: %d\n' % balance)

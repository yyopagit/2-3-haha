# Remove extra closing-brace-only lines: "}\n...\n}\n...\ntitle" -> keep first }, remove the duplicate }
path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\Other.txt'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
out = []
i = 0
removed = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()
    if stripped == '}' and i + 1 < len(lines):
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and lines[j].strip().startswith('title'):
            k = i - 1
            while k >= 0 and not lines[k].strip():
                k -= 1
            if k >= 0 and lines[k].strip() == '}':
                removed += 1
                i += 1
                continue
    out.append(line)
    i += 1
with open(path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(out)
with open(path.replace('Other.txt', 'fix_braces_log.txt'), 'w') as lf:
    lf.write('Removed %d extra brace lines\n' % removed)
print('Removed', removed)

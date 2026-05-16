# Insert missing "}" before each nested event line (descending order to preserve positions)
path = r'c:\Games\Vic2LV2\Victoria 2\mod\6\events\Other.txt'
# Line numbers from validator (1-based); 18834 already fixed manually. Rest: insert "}" before each.
lines_to_fix = [
    18788, 18774, 18745, 18696, 18678, 18656, 18618, 18587, 18552, 18511, 18487, 18424, 18391, 18364, 18291, 18268, 18247, 18225, 18197, 18123, 18071, 18053, 18035, 17980, 17925, 17870, 17786, 17727, 17655, 17585, 17519, 17449, 17409, 17342, 17264, 17149, 17108, 17073, 17012, 16957, 16896, 16799, 16739, 16681, 16583, 16482, 16384, 16320, 16251, 16153, 16087, 16041, 15915, 15858, 15822, 15793, 15754, 15685, 15613, 15544, 15489, 15415, 15347, 15310, 15237, 15173, 15103, 15050, 14983, 14926, 14876, 14827, 14770, 14719, 14662, 14593, 14542, 14485, 14434, 14360, 14305, 14242, 14175, 14131, 14071, 13976, 13921, 13861, 13812, 13762, 13688, 13629, 13568, 13497, 13462, 13403, 13317, 13257, 13218, 13161, 13094, 13062, 13040, 13019, 12970, 12927, 12905, 12883, 12862, 12826, 12804, 12783, 12731
]
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()
# Insert in descending order so indices stay valid
for pos in sorted(lines_to_fix, reverse=True):
    idx = pos - 1
    if idx >= 0 and idx <= len(lines):
        lines.insert(idx, '}\n')
with open(path, 'w', encoding='utf-8', newline='') as f:
    f.writelines(lines)
print('Inserted', len(lines_to_fix), 'closing braces')

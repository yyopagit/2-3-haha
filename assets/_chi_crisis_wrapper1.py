# -*- coding: utf-8 -*-
"""China crisis wrapper 1: linear province modifiers + selector actions."""
from pathlib import Path
import re

ROOT = Path(r"c:\Games\Vic2LV2\Victoria 2\mod\5")
MARK = "CHI_CRISIS_WRAPPER1"

# sep, famine, water, weak (0 = none), extras, pirate (0 skip / 1-3 if coastal)
LEVELS = {
    "CHI_1612": (0, 0, 0, 0, [], 0),
    "CHI_1613": (0, 2, 2, 0, ["waterfam"], 1),
    "CHI_1614": (0, 2, 3, 0, ["yellow", "canal", "waterfam"], 0),
    "CHI_1576": (0, 4, 1, 0, [], 0),
    "CHI_1513": (0, 3, 4, 0, ["yellow", "canal", "waterfam"], 0),
    "CHI_1539": (0, 0, 2, 0, ["canal", "yangtze", "waterfam"], 2),
    "CHI_1608": (0, 0, 1, 0, [], 2),
    "CHI_1550": (0, 1, 2, 0, ["yangtze"], 0),
    "CHI_1522": (0, 1, 3, 0, ["yangtze", "waterfam"], 0),
    "CHI_1578": (1, 0, 0, 0, [], 0),
    "CHI_1618": (0, 0, 0, 0, [], 0),  # unused key guard
    "CHI_1581": (1, 0, 1, 2, [], 0),
    "CHI_1473": (0, 1, 2, 2, ["yangtze"], 0),
    "CHI_1523": (0, 1, 3, 2, ["yangtze", "waterfam"], 0),
    "CHI_1553": (1, 0, 0, 2, [], 1),
    "CHI_1538": (0, 0, 1, 2, [], 2),
    "CHI_1566": (0, 1, 2, 3, ["yellow"], 2),
    "CHI_1563": (0, 2, 2, 3, ["yellow", "waterfam"], 2),
    "CHI_1559": (1, 3, 1, 3, [], 0),
    "CHI_1482": (1, 0, 1, 3, [], 3),
    "CHI_1529": (1, 1, 2, 3, ["yangtze", "waterfam"], 0),
    "CHI_1481": (1, 0, 0, 3, [], 1),
    "CHI_2221": (0, 1, 4, 3, ["canal", "yangtze", "yellow", "waterfam"], 2),
    "CHI_1494": (2, 1, 1, 4, [], 3),
    "CHI_1493": (2, 1, 1, 4, [], 3),
    "CHI_1490": (3, 3, 2, 4, ["waterfam"], 0),
    "CHI_1472": (1, 4, 3, 4, ["canal", "waterfam"], 0),
    "CHI_1532": (2, 1, 1, 4, [], 0),
    "CHI_2562": (2, 1, 0, 4, [], 3),
    "CHI_1496": (0, 0, 0, 3, [], 2),
    "CHI_1498": (0, 0, 0, 3, [], 2),
    "CHI_1600": (4, 1, 2, 5, ["waterfam"], 0),
    "CHI_2608": (4, 1, 1, 5, [], 0),
    "CHI_1601": (3, 2, 1, 5, [], 0),
    "CHI_1504": (3, 4, 1, 5, [], 3),
    "CHI_1557": (3, 1, 1, 5, [], 0),
    "CHI_1082": (2, 0, 0, 5, [], 1),
}

SKIP = {"CHI_1618"}


def parse_chi_regions():
    text = (ROOT / "map" / "region.txt").read_text(encoding="utf-8", errors="replace")
    out = {}
    for m in re.finditer(
        r"^(CHI_\d+)\s*=\s*\{([^}]*)\}", text, flags=re.M
    ):
        key = m.group(1)
        ids = [int(x) for x in re.findall(r"\d+", m.group(2))]
        if key in ("CHI_corruption_high", "CHI_corruption_medium", "CHI_corruption_low"):
            continue
        if not ids:
            continue
        if key in ("CHI_1086",):
            continue
        out[key] = ids
    return out


def bar(level, maxl, width=16):
    """Fallback fill for loc_line (strips §). Modifier cards should use recog_bar + loc_mod_line."""
    if maxl <= 0:
        return "[" + "." * width + "]"
    filled = int(round(width * max(0, int(level)) / maxl))
    filled = max(0, min(width, filled))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def recog_bar(filled, width=20):
    """Same as recognition progress: green pipes done, red pipes left."""
    filled = max(0, min(width, int(round(filled))))
    return "§G" + "|" * filled + "§R" + "|" * (width - filled) + "§W"


def loc_line(key, text):
    clean = re.sub(r"§.", "", text.replace("\\n", ". ").replace("\n", ". "))
    while "  " in clean:
        clean = clean.replace("  ", " ")
    clean = clean.replace(" .", ".").strip()
    return f"{key};{clean};X;X;X;X;X;X\r\n"


def loc_mod_line(key, text):
    """Country/province modifier tooltip: keep § colours and Vic2 \\n."""
    text = text.replace("\r\n", "\n").replace("\n", "\\n")
    return f"{key};{text};X;X;X;X;X;X\r\n"


def replace_marked(text, new_block, comment_prefix="#"):
    start = f"{comment_prefix} {MARK}_START"
    end = f"{comment_prefix} {MARK}_END"
    if start in text and end in text:
        return re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            start + "\n" + new_block.rstrip() + "\n" + end,
            text,
            count=1,
            flags=re.S,
        )
    return None


MODIFIERS = r"""
# Linear crisis wrappers (province + country). Actions go through selector 144408.
CHI_patchwork_empire = {
	land_organisation = -0.10
	reinforce_speed = 0.10
	mobilisation_size = -0.04
	icon = 17
}
CHI_inefficient_bureaucracy = {
	icon = 9
}
CHI_separatism_peripheral = {
	tax_efficiency = -0.05
	land_organisation = -0.05
	reinforce_speed = -0.05
	icon = 16
}
CHI_separatism_medium = {
	tax_efficiency = -0.10
	land_organisation = -0.10
	reinforce_speed = -0.10
	icon = 16
}
CHI_separatism_large = {
	tax_efficiency = -0.15
	land_organisation = -0.15
	reinforce_speed = -0.15
	icon = 16
}
CHI_separatism_1 = {
	pop_militancy_modifier = 0.02
	immigrant_attract = -0.10
	icon = 16
}
CHI_separatism_2 = {
	pop_militancy_modifier = 0.04
	immigrant_attract = -0.20
	local_RGO_output = -0.05
	icon = 16
}
CHI_separatism_3 = {
	pop_militancy_modifier = 0.07
	immigrant_attract = -0.35
	local_RGO_output = -0.10
	icon = 16
}
CHI_separatism_4 = {
	pop_militancy_modifier = 0.10
	immigrant_attract = -0.50
	local_RGO_output = -0.15
	icon = 16
}
CHI_famine_1 = {
	population_growth = -0.001
	immigrant_attract = -0.25
	life_rating = -0.2
	icon = 7
}
CHI_famine_2 = {
	population_growth = -0.0013
	immigrant_attract = -0.45
	life_rating = -0.4
	farm_RGO_eff = -0.05
	icon = 7
}
CHI_famine_3 = {
	population_growth = -0.0017
	immigrant_attract = -0.70
	life_rating = -0.6
	farm_RGO_eff = -0.10
	icon = 7
}
CHI_famine_4 = {
	population_growth = -0.002
	immigrant_attract = -1.00
	life_rating = -0.8
	farm_RGO_eff = -0.15
	icon = 7
}
CHI_water_1 = {
	farm_RGO_eff = -0.08
	immigrant_attract = -0.10
	icon = 8
}
CHI_water_2 = {
	farm_RGO_eff = -0.15
	immigrant_attract = -0.20
	local_factory_throughput = -0.05
	icon = 8
}
CHI_water_3 = {
	farm_RGO_eff = -0.22
	immigrant_attract = -0.30
	local_factory_throughput = -0.10
	icon = 8
}
CHI_water_4 = {
	farm_RGO_eff = -0.30
	immigrant_attract = -0.40
	local_factory_throughput = -0.15
	icon = 8
}
CHI_water_canal_silt = {
	local_factory_throughput = -0.25
	local_RGO_output = -0.15
	farm_RGO_eff = -0.10
	icon = 8
}
CHI_water_yangtze_nav = {
	local_factory_throughput = -0.20
	local_RGO_output = -0.10
	icon = 8
}
CHI_water_yellow_dikes = {
	farm_RGO_eff = -0.20
	population_growth = -0.0006
	immigrant_attract = -0.15
	icon = 8
}
CHI_famine_tied_to_water = {
	icon = 5
}
CHI_weak_rule_1 = {
	local_RGO_output = -0.04
	farm_RGO_eff = -0.04
	pop_militancy_modifier = 0.01
	icon = 10
}
CHI_weak_rule_2 = {
	local_RGO_output = -0.08
	farm_RGO_eff = -0.08
	pop_militancy_modifier = 0.02
	icon = 10
}
CHI_weak_rule_3 = {
	local_RGO_output = -0.12
	farm_RGO_eff = -0.12
	pop_militancy_modifier = 0.03
	local_factory_throughput = -0.05
	icon = 10
}
CHI_weak_rule_4 = {
	local_RGO_output = -0.18
	farm_RGO_eff = -0.18
	pop_militancy_modifier = 0.04
	local_factory_throughput = -0.10
	icon = 10
}
CHI_weak_rule_5 = {
	local_RGO_output = -0.25
	farm_RGO_eff = -0.25
	pop_militancy_modifier = 0.05
	local_factory_throughput = -0.15
	icon = 10
}
CHI_piracy_1 = {
	local_RGO_output = -0.04
	immigrant_attract = -0.10
	icon = 13
}
CHI_piracy_2 = {
	local_RGO_output = -0.08
	immigrant_attract = -0.20
	local_factory_throughput = -0.05
	icon = 13
}
CHI_piracy_3 = {
	local_RGO_output = -0.14
	immigrant_attract = -0.35
	local_factory_throughput = -0.10
	icon = 13
}
CHI_piracy_4 = {
	local_RGO_output = -0.20
	immigrant_attract = -0.50
	local_factory_throughput = -0.15
	icon = 13
}
CHI_great_granary = {
	population_growth = 0.0015
	farm_RGO_eff = 0.08
	immigrant_attract = 0.15
	icon = 11
}
CHI_famine_infra_relief = {
	population_growth = 0.001
	immigrant_attract = 0.10
	farm_RGO_eff = 0.04
	icon = 11
}
CHI_port_anti_piracy = {
	local_RGO_output = 0.04
	icon = 13
}
CHI_hydro_cd = {
	icon = 8
}
CHI_sep_cd = {
	icon = 16
}
CHI_sep_tax_cut = {
	tax_efficiency = -0.04
	icon = 9
}
CHI_sep_revolt_cd = {
	icon = 16
}
CHI_sep_uprising = {
	pop_militancy_modifier = 0.20
	icon = 16
}
CHI_click_mark = {
	icon = 9
}
CHI_lvl_dropped = {
	icon = 9
}
CHI_sep_revolt_pending = {
	icon = 16
}
CHI_sep_revolt_won = {
	icon = 16
}
"""


def fill_corruption(text):
    repl = {
        "CHI_corruption_high": "\tadministrative_efficiency_modifier = -0.25\n\ticon = 9\n",
        "CHI_corruption_medium": "\tadministrative_efficiency_modifier = -0.15\n\ticon = 9\n",
        "CHI_corruption_low": "\tadministrative_efficiency_modifier = -0.05\n\ticon = 9\n",
    }
    for name, body in repl.items():
        text = re.sub(
            rf"{name} = \{{[^{{}}]*\}}",
            f"{name} = {{\n{body}}}",
            text,
            count=1,
        )
    return text


def indent_or_ids(ids, pad="\t\t\t\t\t"):
    chunks = []
    line = []
    for i, pid in enumerate(ids):
        line.append(str(pid))
        if len(line) == 8:
            chunks.append(pad + " ".join(f"province_id = {x}" for x in line))
            line = []
    if line:
        chunks.append(pad + " ".join(f"province_id = {x}" for x in line))
    return "\n".join(chunks)


_USED_REGIONS = None


def regions_used():
    """rid string -> list of province ids for crisis regions."""
    global _USED_REGIONS
    if _USED_REGIONS is None:
        raw = parse_chi_regions()
        _USED_REGIONS = {
            k.split("_")[1]: v
            for k, v in raw.items()
            if k in LEVELS and k not in SKIP
        }
    return _USED_REGIONS


def rids_used():
    return list(regions_used().keys())


def ids_trigger(ids, pad="\t\t\t\t\t"):
    """ProvinceTrigger matching any of the ids. No single-element OR."""
    if not ids:
        raise ValueError("ids_trigger: empty province list")
    if len(ids) == 1:
        return f"{pad}province_id = {ids[0]}"
    inner = indent_or_ids(ids, pad=pad + "\t")
    return f"{pad}OR = {{\n{inner}\n{pad}}}"


def setup_province_block(rid, ids, sep, fam, wat, weak, extras, pirate):
    # Province flags are not in this engine's ProvinceCommand/ProvinceTrigger.
    # Regions are matched by province_id lists from map/region.txt.
    mods = []
    if sep:
        mods.append(
            f"\t\t\t\tadd_province_modifier = {{ name = CHI_separatism_{sep} duration = -1 }}"
        )
    if fam:
        mods.append(
            f"\t\t\t\tadd_province_modifier = {{ name = CHI_famine_{fam} duration = -1 }}"
        )
    if wat:
        mods.append(
            f"\t\t\t\tadd_province_modifier = {{ name = CHI_water_{wat} duration = -1 }}"
        )
    if weak:
        mods.append(
            f"\t\t\t\tadd_province_modifier = {{ name = CHI_weak_rule_{weak} duration = -1 }}"
        )
    extra_map = {
        "canal": "CHI_water_canal_silt",
        "yangtze": "CHI_water_yangtze_nav",
        "yellow": "CHI_water_yellow_dikes",
        "waterfam": "CHI_famine_tied_to_water",
    }
    for e in extras:
        mods.append(
            f"\t\t\t\tadd_province_modifier = {{ name = {extra_map[e]} duration = -1 }}"
        )
    or_ids = "\n".join(
        "\t\t\t\t\t" + " ".join(f"province_id = {x}" for x in ids[i : i + 6])
        for i in range(0, len(ids), 6)
    )
    body = "\n".join(mods)
    return f"""			any_owned = {{
				limit = {{
					OR = {{
{or_ids}
					}}
				}}
{body}
			}}"""


def build_setup(regions):
    blocks = []
    for key, ids in regions.items():
        if key not in LEVELS or key in SKIP:
            continue
        sep, fam, wat, weak, extras, pirate = LEVELS[key]
        rid = key.split("_")[1]
        blocks.append(setup_province_block(rid, ids, sep, fam, wat, weak, extras, pirate))
    pirate_high = []
    pirate_mid = []
    pirate_low = []
    for key, ids in regions.items():
        if key not in LEVELS or key in SKIP:
            continue
        pirate = LEVELS[key][5]
        if pirate == 3:
            pirate_high.extend(ids)
        elif pirate == 2:
            pirate_mid.extend(ids)
        elif pirate == 1:
            pirate_low.extend(ids)

    def pirate_block(ids, level):
        if not ids:
            return ""
        or_ids = "\n".join(
            "\t\t\t\t\t" + " ".join(f"province_id = {x}" for x in ids[i : i + 6])
            for i in range(0, len(ids), 6)
        )
        return f"""			any_owned = {{
				limit = {{
					is_coastal = yes
					OR = {{
{or_ids}
					}}
				}}
				add_province_modifier = {{ name = CHI_piracy_{level} duration = -1 }}
			}}"""

    inner = "\n".join(blocks)
    return f"""			CHI = {{
				add_country_modifier = {{
					name = CHI_MGL_separatism
					duration = -1
				}}
				add_country_modifier = {{
					name = CHI_TIB_separatism
					duration = -1
				}}
				add_country_modifier = {{
					name = CHI_MCK_separatism
					duration = -1
				}}
				add_country_modifier = {{
					name = CHI_corruption_high
					duration = -1
				}}
				add_country_modifier = {{
					name = CHI_separatism_peripheral
					duration = -1
				}}
				add_country_modifier = {{
					name = CHI_patchwork_empire
					duration = -1
				}}
{inner}
{pirate_block(pirate_high, 3)}
{pirate_block(pirate_mid, 2)}
{pirate_block(pirate_low, 1)}
			}}
			country_event = {{ id = 144405 days = 0 }}"""


def region_ids_list(regions):
    return [k.split("_")[1] for k in regions if k in LEVELS and k not in SKIP]


def gen_set_act(rids):
    regs = regions_used()
    lines = []
    for rid in rids:
        idb = ids_trigger(regs[rid], pad="\t\t\t\t\t")
        lines.append(
            f"""			random_owned = {{
				limit = {{
					has_building = province_selector
{idb}
				}}
				owner = {{ set_country_flag = CHI_act_{rid} }}
			}}"""
        )
    return "\n".join(lines)


def gen_region_or(rids, extra_indent=""):
    regs = regions_used()
    parts = []
    for rid in rids:
        idb = ids_trigger(regs[rid], pad=f"{extra_indent}\t\t\t\t\t\t\t")
        parts.append(
            f"""{extra_indent}						AND = {{
{idb}
{extra_indent}							owner = {{ has_country_flag = CHI_act_{rid} }}
{extra_indent}						}}"""
        )
    return "\n".join(parts)


def gen_clr_act(rids):
    return "\n".join(f"			clr_country_flag = CHI_act_{rid}" for rid in rids)


def pay_chunks(amount):
    """Split money so no single effect exceeds 2 000 000."""
    left = amount
    chunks = []
    while left > 0:
        n = min(left, 2000000)
        chunks.append(n)
        left -= n
    return chunks


def money_effects(amount, indent="\t\t\t"):
    lines = []
    for n in pay_chunks(amount):
        lines.append(f"{indent}any_country = {{")
        lines.append(f"{indent}	limit = {{ tag = THIS }}")
        lines.append(f"{indent}	money = -{n}")
        lines.append(f"{indent}}}")
    return "\n".join(lines)


def _level_drop_block(rids, prefix, indent="\t\t\t"):
    orlim = gen_region_or(rids)
    steps = []
    for src, dst in ((4, 3), (3, 2), (2, 1), (1, None)):
        extra = ""
        if src != 4:
            extra = f"{indent}\t\tNOT = {{ has_province_modifier = CHI_lvl_dropped }}\n"
        add = ""
        if dst:
            add = f"{indent}\tadd_province_modifier = {{ name = {prefix}_{dst} duration = -1 }}\n"
        steps.append(
            f"""{indent}any_owned = {{
{indent}	limit = {{
{indent}		has_province_modifier = {prefix}_{src}
{extra}{indent}		OR = {{
{orlim}
{indent}		}}
{indent}	}}
{indent}	remove_province_modifier = {prefix}_{src}
{add}{indent}	add_province_modifier = {{ name = CHI_lvl_dropped duration = -1 }}
{indent}}}"""
        )
    steps.append(
        f"""{indent}any_owned = {{
{indent}	limit = {{
{indent}		OR = {{
{orlim}
{indent}		}}
{indent}	}}
{indent}	remove_province_modifier = CHI_lvl_dropped
{indent}}}"""
    )
    return "\n".join(steps)


def famine_drop_block(rids, indent="\t\t\t"):
    return _level_drop_block(rids, "CHI_famine", indent)


def water_drop_block(rids, indent="\t\t\t"):
    return _level_drop_block(rids, "CHI_water", indent)


def build_event_144408(rids):
    set_act = gen_set_act(rids)
    clr_act = gen_clr_act(rids)
    orlim = gen_region_or(rids)
    fam_drop = famine_drop_block(rids)
    wat_drop = water_drop_block(rids)
    fam_if_water = famine_drop_block(rids)
    pay_granary = money_effects(2000000, "\t\t\t\t")
    pay_granary_c = money_effects(2000000, "\t\t\t\t") + "\n" + money_effects(2000000, "\t\t\t\t")
    pay_w1 = money_effects(500, "\t\t\t\t")
    pay_w1c = money_effects(1000, "\t\t\t\t")
    pay_w2 = money_effects(80000, "\t\t\t\t")
    pay_w2c = money_effects(160000, "\t\t\t\t")
    pay_w3 = money_effects(400000, "\t\t\t\t")
    pay_w3c = money_effects(800000, "\t\t\t\t")
    pay_w4 = money_effects(1000000, "\t\t\t\t")
    pay_w4c = money_effects(2000000, "\t\t\t\t")
    pay_uniq = money_effects(1000000, "\t\t\t\t") + "\n" + money_effects(1000000, "\t\t\t\t")
    pay_uniqc = money_effects(2000000, "\t\t\t\t") + "\n" + money_effects(2000000, "\t\t\t\t")

    def water_pay_option(level, pay, pay_c, money_need, money_need_c):
        return f"""	option = {{
		name = "CHI_sel_water_{level}"
		trigger = {{
			has_province_modifier = CHI_water_{level}
			owner = {{
				OR = {{
					AND = {{
						NOT = {{ has_country_modifier = CHI_corruption_high }}
						money = {money_need}
					}}
					AND = {{
						has_country_modifier = CHI_corruption_high
						money = {money_need_c if money_need_c <= 2000000 else 2000000}
					}}
				}}
			}}
		}}
		add_province_modifier = {{ name = CHI_click_mark duration = -1 }}
		owner = {{
{set_act}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ NOT = {{ has_country_modifier = CHI_corruption_high }} }}
				}}
				owner = {{
{pay}
				}}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_modifier = CHI_corruption_high }}
				}}
				owner = {{
{pay_c}
				}}
			}}
{wat_drop}
			any_owned = {{
				limit = {{
					has_province_modifier = CHI_famine_tied_to_water
					OR = {{
{orlim}
					}}
				}}
				owner = {{ set_country_flag = CHI_do_waterfam }}
			}}
		}}
		owner = {{
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_flag = CHI_do_waterfam }}
				}}
				owner = {{
{fam_if_water}
				}}
			}}
			clr_country_flag = CHI_do_waterfam
{clr_act}
		}}
		remove_province_modifier = CHI_click_mark
		province_selector = -1
	}}"""

    uniq_option = f"""	option = {{
		name = "CHI_sel_unique_water"
		trigger = {{
			OR = {{
				has_province_modifier = CHI_water_canal_silt
				has_province_modifier = CHI_water_yangtze_nav
				has_province_modifier = CHI_water_yellow_dikes
			}}
			owner = {{ money = 2000000 }}
		}}
		add_province_modifier = {{ name = CHI_click_mark duration = -1 }}
		owner = {{
{set_act}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ NOT = {{ has_country_modifier = CHI_corruption_high }} }}
				}}
				owner = {{
{pay_uniq}
				}}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_modifier = CHI_corruption_high }}
				}}
				owner = {{
{pay_uniqc}
				}}
			}}
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				remove_province_modifier = CHI_water_canal_silt
				remove_province_modifier = CHI_water_yangtze_nav
				remove_province_modifier = CHI_water_yellow_dikes
			}}
{clr_act}
		}}
		remove_province_modifier = CHI_click_mark
		province_selector = -1
	}}"""

    granary = f"""	option = {{
		name = "CHI_sel_granary"
		trigger = {{
			OR = {{
				has_province_modifier = CHI_famine_1
				has_province_modifier = CHI_famine_2
				has_province_modifier = CHI_famine_3
				has_province_modifier = CHI_famine_4
			}}
			NOT = {{ has_province_modifier = CHI_great_granary }}
			owner = {{ money = 2000000 }}
		}}
		add_province_modifier = {{ name = CHI_click_mark duration = -1 }}
		owner = {{
{set_act}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ NOT = {{ has_country_modifier = CHI_corruption_high }} }}
				}}
				owner = {{
{pay_granary}
				}}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_modifier = CHI_corruption_high }}
				}}
				owner = {{
{pay_granary_c}
				}}
			}}
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_great_granary duration = -1 }}
			}}
{fam_drop}
{clr_act}
		}}
		remove_province_modifier = CHI_click_mark
		province_selector = -1
	}}"""

    infra = f"""	option = {{
		name = "CHI_sel_infra"
		trigger = {{
			OR = {{
				has_province_modifier = CHI_famine_1
				has_province_modifier = CHI_famine_2
				has_province_modifier = CHI_famine_3
				has_province_modifier = CHI_famine_4
			}}
			NOT = {{ has_province_modifier = CHI_famine_infra_relief }}
		}}
		add_province_modifier = {{ name = CHI_click_mark duration = -1 }}
		owner = {{
{set_act}
			any_owned = {{
				limit = {{
					has_building = railroad
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_famine_infra_relief duration = -1 }}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{
						NOT = {{
							any_owned = {{
								AND = {{
									NOT = {{ has_building = railroad }}
									OR = {{
{orlim}
									}}
								}}
							}}
						}}
					}}
				}}
				owner = {{
{fam_drop}
				}}
			}}
{clr_act}
		}}
		remove_province_modifier = CHI_click_mark
		province_selector = -1
	}}"""

    port = """	option = {
		name = "CHI_sel_port_piracy"
		trigger = {
			is_coastal = yes
			has_building = naval_base
			OR = {
				has_province_modifier = CHI_piracy_2
				has_province_modifier = CHI_piracy_3
				has_province_modifier = CHI_piracy_4
			}
		}
		remove_province_modifier = CHI_piracy_4
		remove_province_modifier = CHI_piracy_3
		remove_province_modifier = CHI_piracy_2
		add_province_modifier = { name = CHI_piracy_1 duration = -1 }
		add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
		province_selector = -1
	}"""

    fleet = """	option = {
		name = "CHI_sel_fleet_piracy"
		trigger = {
			is_coastal = yes
			OR = {
				has_province_modifier = CHI_piracy_1
				has_province_modifier = CHI_piracy_2
				has_province_modifier = CHI_piracy_3
				has_province_modifier = CHI_piracy_4
			}
			owner = { total_amount_of_ships = 200 }
		}
		owner = {
			any_owned = {
				remove_province_modifier = CHI_piracy_1
				remove_province_modifier = CHI_piracy_2
				remove_province_modifier = CHI_piracy_3
				remove_province_modifier = CHI_piracy_4
			}
		}
		province_selector = -1
	}"""

    return f"""province_event = {{
	title = "CHI_Selector_EvtName"
	desc = "CHI_Selector_EvtDesc"
	id = 144408
	picture = "Administration"
	is_triggered_only = yes

	option = {{
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}}
	option = {{
		name = "Selector_EvtOptSupplyDepot"
		owner = {{
			money = -500000
			any_owned = {{
				remove_province_modifier = provincial_supply_depot_pmodifier
			}}
		}}
		add_province_modifier = {{
			name = provincial_supply_depot_pmodifier
			duration = -1
		}}
		province_selector = -1
	}}
{granary}
{water_pay_option(1, pay_w1, pay_w1c, 500, 1000)}
{water_pay_option(2, pay_w2, pay_w2c, 80000, 160000)}
{water_pay_option(3, pay_w3, pay_w3c, 400000, 800000)}
{water_pay_option(4, pay_w4, pay_w4c, 1000000, 2000000)}
{uniq_option}
{infra}
{port}
{fleet}
	option = {{
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}}
}}
"""


POP_INSERT = """
		modifier = {
			factor = 0
			country = { has_country_modifier = CHI_patchwork_empire }
			soldiers = 0.03
		}
		modifier = {
			factor = 0
			location = { has_province_modifier = CHI_separatism_1 }
			soldiers = 0.015
		}
		modifier = {
			factor = 0
			location = { has_province_modifier = CHI_separatism_2 }
			soldiers = 0.01
		}
		modifier = {
			factor = 0
			location = { has_province_modifier = CHI_separatism_3 }
			soldiers = 0.005
		}
		modifier = {
			factor = 0
			location = { has_province_modifier = CHI_separatism_4 }
			soldiers = 0.005
		}
"""

POP_ANCHOR = """		modifier = {
			factor = 1.05
			country = { military_politics = regular_army }
		}
		group = {
			modifier = {
				factor = -4
				recruited_percentage = 0.0
			}"""

POP_ANCHOR_OFF = """		modifier = {
			factor = 1.1
			AND = {
				has_building = town_infrastructure
				country = { colonial_politics = non_colonial }

				NOT = { soldiers = 0.10 }
			}
		}"""


def patch_poptypes():
    repl = (
        POP_ANCHOR[: POP_ANCHOR.index("		group = {")]
        + POP_INSERT
        + "		group = {\n			modifier = {\n				factor = -4\n				recruited_percentage = 0.0\n			}"
    )
    for name in ("farmers.txt", "labourers.txt", "craftsmen.txt"):
        path = ROOT / "poptypes" / name
        text = path.read_text(encoding="utf-8")
        if "CHI_patchwork_empire" in text:
            print(name, "already patched")
            continue
        if POP_ANCHOR not in text:
            raise SystemExit(f"anchor missing in {name}")
        path.write_text(text.replace(POP_ANCHOR, repl, 1), encoding="utf-8", newline="\n")
        print("patched", name)
    op = ROOT / "poptypes" / "officers.txt"
    ot = op.read_text(encoding="utf-8")
    if "CHI_patchwork_empire" not in ot:
        if POP_ANCHOR_OFF not in ot:
            raise SystemExit("officers anchor missing")
        ot = ot.replace(POP_ANCHOR_OFF, POP_INSERT + "\n" + POP_ANCHOR_OFF, 1)
        op.write_text(ot, encoding="utf-8", newline="\n")
        print("patched officers.txt")
    else:
        print("officers already patched")


def build_loc():
    lines = []
    add = lines.append
    add(loc_line("CHI_Selector_EvtName", "Управление провинцией"))
    add(
        loc_line(
            "CHI_Selector_EvtDesc",
            "Селектор этой провинции. Действие применяется ко всему региону "
            "(голод, вода, амбар) либо только к этой провинции (порт). "
            "При коррупции цена решений x2.",
        )
    )
    add(loc_line("CHI_sel_granary", "Великий амбар"))
    add(loc_line("CHI_sel_water_1", "Ремонт ирригации I"))
    add(loc_line("CHI_sel_water_2", "Ремонт ирригации II"))
    add(loc_line("CHI_sel_water_3", "Ремонт ирригации III"))
    add(loc_line("CHI_sel_water_4", "Ремонт ирригации IV"))
    add(loc_line("CHI_sel_unique_water", "Особые речные работы"))
    add(loc_line("CHI_sel_infra", "Инфраструктура 2-го уровня частично снимает голод"))
    add(loc_line("CHI_sel_port_piracy", "Порт ослабляет пиратство в этой провинции"))
    add(loc_line("CHI_sel_fleet_piracy", "Флот в 200 кораблей подавляет пиратство по всей стране"))
    add(loc_line("Selector_EvtName", "Селектор провинции"))
    add(loc_line("Selector_EvtDesc", "Выберите действие для отмеченной провинции."))
    add(loc_line("Selector_EvtOptCancel", "Отмена"))
    add(loc_line("Selector_EvtOptSupplyDepot", "Снабженческий склад (500 000)"))
    add(loc_line("Selector_EvtOptRemAllSelectors", "Убрать все селекторы"))
    add(loc_line("select_prov_CHI", "Китай: селектор провинции"))
    add(loc_line("select_prov_CHI_desc", "Открыть действия для провинции с селектором (голод, вода, пиратство, амбар)."))
    add(loc_line("select_prov", "Селектор провинции"))
    add(loc_line("select_prov_desc", "Открыть действия для провинции с селектором."))

    add(loc_line("CHI_patchwork_empire", "Лоскутная феодальная империя"))
    add(
        loc_line(
            "CHI_patchwork_empire_desc",
            "Неснимаемый порядок Цин: слабый центр, быстрый набор ополчения.\\n"
            "Лимит солдат (~3% населения) задаётся типами POP, не этим модификатором. "
            "В карточке модификатора видны только организация, набор и мобилизация.",
        )
    )
    add(loc_line("CHI_inefficient_bureaucracy", "Неэффективная бюрократия"))
    add(
        loc_line(
            "CHI_inefficient_bureaucracy_desc",
            "Старая карточка без штрафа. Живой эффект — уровни I–IV в списке модификаторов страны.",
        )
    )
    bureau_txt = {
        4: "Худший разлад канцелярии: война или бунт. Налог -11, управление -13.",
        3: "Старт Цин. Канцелярия слабая, но не развалена. Налог -8, управление -10.",
        2: "Первые сдвиги: грамотность, реформа школ, мысль или спад коррупции. Налог -5, управление -6.",
        1: "Почти собрана: грамотность и современная мысль. Налог -2, управление -3.",
    }
    roman_b = {1: "I", 2: "II", 3: "III", 4: "IV"}
    for i in range(1, 5):
        add(loc_line(f"CHI_inefficient_bureaucracy_{i}", f"Неэффективная бюрократия {roman_b[i]}"))
        add(
            loc_mod_line(
                f"CHI_inefficient_bureaucracy_{i}_desc",
                f"{bureau_txt[i]}\n"
                "Снимается сама: растёт грамотность, появляются школы, осваивается современная мысль, падает коррупция.\n"
                f"Прогресс: {recog_bar(20 * (4 - i) / 4)}",
            )
        )
    add(loc_line("CHI_separatism_peripheral", "Сепаратизм: периферийный"))
    add(
        loc_line(
            "CHI_separatism_peripheral_desc",
            "Национальный сепаратизм на окраинах.\\n"
            f"Масштаб: {bar(1, 3)}\\n-5 к налогу, организации и пополнению.",
        )
    )
    add(loc_line("CHI_separatism_medium", "Сепаратизм: средний"))
    add(
        loc_line(
            "CHI_separatism_medium_desc",
            "Национальный сепаратизм среднего масштаба.\\n"
            f"Масштаб: {bar(2, 3)}\\n-10 к налогу, организации и пополнению.",
        )
    )
    add(loc_line("CHI_separatism_large", "Сепаратизм: масштабный"))
    add(
        loc_line(
            "CHI_separatism_large_desc",
            "Национальный сепаратизм охватил империю.\\n"
            f"Масштаб: {bar(3, 3)}\\n-15 к налогу, организации и пополнению.",
        )
    )
    add(loc_line("CHI_corruption_high", "Коррупция"))
    add(
        loc_line(
            "CHI_corruption_high_desc",
            "Эффективность управления -25. Все решения по борьбе с бедствиями стоят x2.",
        )
    )
    add(loc_line("CHI_corruption_medium", "Коррупция (средняя)"))
    add(loc_line("CHI_corruption_medium_desc", "Эффективность управления -15."))
    add(loc_line("CHI_corruption_low", "Коррупция (низкая)"))
    add(loc_line("CHI_corruption_low_desc", "Эффективность управления -5."))

    roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
    sep_txt = {
        1: "Фермеры почти не идут в солдаты выше ~1.5% населения провинции (порог в poptypes, не в этом модификаторе).",
        2: "Порог солдат ещё ниже (~1.0%). Плюс штраф RGO.",
        3: "Порог солдат ~0.5%. Сильная милитантность.",
        4: "Порог солдат ~0.5%, максимальная милитантность и исход.",
    }
    for i in range(1, 5):
        add(loc_line(f"CHI_separatism_{i}", f"Сепаратизм {roman[i]}"))
        add(
            loc_line(
                f"CHI_separatism_{i}_desc",
                f"Региональный сепаратизм.\\nУровень: {bar(i, 4)}\\n{sep_txt[i]}",
            )
        )
    fam_txt = {
        1: "Прирост -0.1%/мес, начинается исход.",
        2: "Прирост -0.13%/мес, сильный исход.",
        3: "Прирост -0.17%/мес, тяжёлый голод.",
        4: "Прирост -0.2%/мес, исход из региона.",
    }
    for i in range(1, 5):
        add(loc_line(f"CHI_famine_{i}", f"Голод {roman[i]}"))
        add(
            loc_line(
                f"CHI_famine_{i}_desc",
                f"Проблема с едой.\\nУровень: {bar(i, 4)}\\n{fam_txt[i]}\\n"
                "Частично снимается амбаром. Уровень голода падает сам, если инфраструктура 2-го уровня построена во всех провинциях региона. Если голод связан с водой - ремонт воды тоже снижает его.",
            )
        )
    wat_txt = {
        1: "Сельское хозяйство ослаблено.",
        2: "Плюс штраф промышленности.",
        3: "Тяжёлая гидротехническая разруха.",
        4: "Река не управляется, поля и фабрики страдают.",
    }
    for i in range(1, 5):
        add(loc_line(f"CHI_water_{i}", f"Вода {roman[i]}"))
        add(
            loc_line(
                f"CHI_water_{i}_desc",
                f"Проблемы водоснабжения.\\nУровень: {bar(i, 4)}\\n{wat_txt[i]}\\n"
                "Бьёт по RGO и миграции. Снимается через селектор.",
            )
        )
    for i in range(1, 6):
        add(loc_line(f"CHI_weak_rule_{i}", f"Слабая власть {roman[i]}"))
        add(
            loc_line(
                f"CHI_weak_rule_{i}_desc",
                f"Слабая власть над регионом.\\nУровень: {bar(i, 5)}\\n"
                "2 уровня от неэффективной бюрократии, до 3 — от бедствий провинции. Вне ядра империи.",
            )
        )
    for i in range(1, 5):
        add(loc_line(f"CHI_piracy_{i}", f"Пиратство {roman[i]}"))
        add(
            loc_line(
                f"CHI_piracy_{i}_desc",
                f"Приморская угроза.\\nУровень: {bar(i, 4)}\\n"
                "Порт ослабляет на 1 уровень. Флот в 200 кораблей снимает полностью.",
            )
        )
    add(loc_line("CHI_water_canal_silt", "Заиление канала"))
    add(
        loc_line(
            "CHI_water_canal_silt_desc",
            "Судоходство Великого канала подорвано. Тяжёлый штраф промышленности региона.\\n"
            "Снимается селектором (особая речная проблема).",
        )
    )
    add(loc_line("CHI_water_yangtze_nav", "Срыв судоходства Янцзы"))
    add(
        loc_line(
            "CHI_water_yangtze_nav_desc",
            "Речная торговля Янцзы парализована. Штраф промышленности.\\nСнимается селектором.",
        )
    )
    add(loc_line("CHI_water_yellow_dikes", "Дамбы Хуанхэ"))
    add(
        loc_line(
            "CHI_water_yellow_dikes_desc",
            "Угроза прорыва Хуанхэ: поля и еда под ударом.\\nСнимается селектором.",
        )
    )
    add(loc_line("CHI_famine_tied_to_water", "Голод связан с водой"))
    add(
        loc_line(
            "CHI_famine_tied_to_water_desc",
            "Ремонт гидротехники через селектор также снизит голод на 1 уровень.",
        )
    )
    add(loc_line("CHI_great_granary", "Великий амбар"))
    add(
        loc_line(
            "CHI_great_granary_desc",
            "Казённый амбар региона. Частично компенсирует голод, держит зерно и людей.",
        )
    )
    add(loc_line("CHI_famine_infra_relief", "Инфраструктура против голода"))
    add(
        loc_line(
            "CHI_famine_infra_relief_desc",
            "Если инфраструктура 2-го уровня построена во всех провинциях региона, уровень голода снижается сам. Это не решение селектора.",
        )
    )
    add(loc_line("CHI_port_anti_piracy", "Портовый надзор"))
    add(loc_line("CHI_port_anti_piracy_desc", "Порт ослабляет приморский разбой в этой провинции."))
    add(loc_line("CHI_click_mark", "Обработка приказа"))
    add(loc_line("CHI_click_mark_desc", "Временный маркер выбранной провинции."))
    add(loc_line("CHI_lvl_dropped", "Снижение уровня"))
    add(loc_line("CHI_lvl_dropped_desc", "Служебный маркер: уровень бедствия уже снижен в этом проходе."))
    add(loc_line("CHI_sep_revolt_pending", "Исход восстания"))
    add(loc_line("CHI_sep_revolt_pending_desc", "После спада восстания, если провинция под контролем Китая, сепаратизм региона будет снижен."))
    add(loc_line("CHI_sep_revolt_won", "Восстание подавлено"))
    add(loc_line("CHI_sep_revolt_won_desc", "Провинция снова под контролем."))
    add(loc_line("CHI_corruption_no", "Без коррупции"))
    add(loc_line("CHI_corruption_no_desc", "Коррупция снята."))
    add(loc_line("CHI_fleet_anti_piracy_ready", "Флот против пиратства"))
    add(loc_line("CHI_fleet_anti_piracy_ready_desc", "В строю не меньше 200 кораблей: флот может подавить пиратство по всей стране."))
    return "".join(lines)


LOC_KEYS = {
    "CHI_Selector_EvtName",
    "CHI_Selector_EvtDesc",
    "CHI_sel_granary",
    "CHI_sel_water_1",
    "CHI_sel_water_2",
    "CHI_sel_water_3",
    "CHI_sel_water_4",
    "CHI_sel_unique_water",
    "CHI_sel_infra",
    "CHI_sel_port_piracy",
    "CHI_sel_fleet_piracy",
    "CHI_patchwork_empire",
    "CHI_patchwork_empire_desc",
    "CHI_inefficient_bureaucracy",
    "CHI_inefficient_bureaucracy_desc",
    "CHI_inefficient_bureaucracy_1",
    "CHI_inefficient_bureaucracy_1_desc",
    "CHI_inefficient_bureaucracy_2",
    "CHI_inefficient_bureaucracy_2_desc",
    "CHI_inefficient_bureaucracy_3",
    "CHI_inefficient_bureaucracy_3_desc",
    "CHI_inefficient_bureaucracy_4",
    "CHI_inefficient_bureaucracy_4_desc",
    "CHI_separatism_peripheral",
    "CHI_separatism_peripheral_desc",
    "CHI_separatism_medium",
    "CHI_separatism_medium_desc",
    "CHI_separatism_large",
    "CHI_separatism_large_desc",
    "CHI_corruption_high",
    "CHI_corruption_high_desc",
    "CHI_corruption_medium",
    "CHI_corruption_medium_desc",
    "CHI_corruption_low",
    "CHI_corruption_low_desc",
    "CHI_water_canal_silt",
    "CHI_water_canal_silt_desc",
    "CHI_water_yangtze_nav",
    "CHI_water_yangtze_nav_desc",
    "CHI_water_yellow_dikes",
    "CHI_water_yellow_dikes_desc",
    "CHI_famine_tied_to_water",
    "CHI_famine_tied_to_water_desc",
    "CHI_great_granary",
    "CHI_great_granary_desc",
    "CHI_famine_infra_relief",
    "CHI_famine_infra_relief_desc",
    "CHI_port_anti_piracy",
    "CHI_port_anti_piracy_desc",
    "CHI_click_mark",
    "CHI_click_mark_desc",
    "CHI_lvl_dropped",
    "CHI_lvl_dropped_desc",
    "CHI_sep_revolt_pending",
    "CHI_sep_revolt_pending_desc",
    "CHI_sep_revolt_won",
    "CHI_sep_revolt_won_desc",
    "CHI_corruption_no",
    "CHI_corruption_no_desc",
    "CHI_fleet_anti_piracy_ready",
    "CHI_fleet_anti_piracy_ready_desc",
    "Selector_EvtName",
    "Selector_EvtDesc",
    "Selector_EvtOptCancel",
    "Selector_EvtOptSupplyDepot",
    "Selector_EvtOptRemAllSelectors",
    "select_prov_CHI",
    "select_prov_CHI_desc",
    "select_prov",
    "select_prov_desc",
}
for i in range(1, 5):
    LOC_KEYS.update(
        {
            f"CHI_separatism_{i}",
            f"CHI_separatism_{i}_desc",
            f"CHI_famine_{i}",
            f"CHI_famine_{i}_desc",
            f"CHI_water_{i}",
            f"CHI_water_{i}_desc",
            f"CHI_piracy_{i}",
            f"CHI_piracy_{i}_desc",
        }
    )
for i in range(1, 6):
    LOC_KEYS.update({f"CHI_weak_rule_{i}", f"CHI_weak_rule_{i}_desc"})


def patch_event_modifiers():
    path = ROOT / "common" / "event_modifiers.txt"
    text = path.read_bytes().decode("utf-8")
    text = fill_corruption(text)
    start = f"# {MARK}_START"
    end = f"# {MARK}_END"
    block = start + "\n" + MODIFIERS.strip() + "\n" + end + "\n"
    if start in text:
        text = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            block.strip(),
            text,
            count=1,
            flags=re.S,
        )
    else:
        needle = "CHI_MCK_separatism = {\r\n\tprestige = -0.025\r\n\tland_organisation = -0.05\r\n}\r\n"
        if needle not in text:
            needle = "CHI_MCK_separatism = {\n\tprestige = -0.025\n\tland_organisation = -0.05\n}\n"
        if needle not in text:
            raise SystemExit("CHI_MCK_separatism block not found")
        text = text.replace(needle, needle + block, 1)
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("event_modifiers.txt ok")


def patch_setup(regions):
    path = ROOT / "decisions" / "SETUP.txt"
    text = path.read_bytes().decode("utf-8")
    new_chi = build_setup(regions)
    start_mark = "\t\t\t# " + MARK + "_START"
    end_mark = "\t\t\t# " + MARK + "_END"
    wrapped = start_mark + "\n" + new_chi + "\n" + end_mark
    if start_mark in text:
        s = text.index(start_mark)
        e = text.index(end_mark) + len(end_mark)
        text = text[:s] + wrapped + text[e:]
    else:
        start = text.find("\t\t\tCHI = {")
        if start < 0:
            start = text.find("CHI = {")
            start = text.rfind("\n", 0, start) + 1
        brace = text.find("{", start)
        depth = 0
        end = None
        for k, ch in enumerate(text[brace:], brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = k + 1
                    break
        if end is None:
            raise SystemExit("SETUP CHI brace match failed")
        text = text[:start] + wrapped + text[end:]
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("SETUP.txt ok")


def extract_event(text, event_id):
    key = f"id = {event_id}"
    i = text.find(key)
    if i < 0:
        raise SystemExit(f"event {event_id} not found")
    start = text.rfind("province_event", 0, i)
    if start < 0:
        raise SystemExit("province_event start not found")
    j = text.find("{", start)
    depth = 0
    for k, ch in enumerate(text[j:], j):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, k + 1
    raise SystemExit("unbalanced event")


def patch_jan(rids):
    # Hub 144408 lives in events/CHI_crisis_01_hub.txt. Do not inject a duplicate into JAN.
    print("JAN 144408 skipped (hub file owns it)")


def patch_chi_decisions():
    path = ROOT / "decisions" / "CHI.txt"
    text = path.read_bytes().decode("utf-8")
    text = text.replace(
        """			set_country_flag = CHI_high_corruption_lost
			CHI_corruption_high = {}""",
        """			set_country_flag = CHI_high_corruption_lost
			remove_country_modifier = CHI_corruption_high
			add_country_modifier = { name = CHI_corruption_medium duration = -1 }""",
    )
    text = text.replace(
        """			set_country_flag = CHI_medium_corruption_lost
			CHI_corruption_medium = {}""",
        """			set_country_flag = CHI_medium_corruption_lost
			remove_country_modifier = CHI_corruption_medium
			add_country_modifier = { name = CHI_corruption_low duration = -1 }""",
    )
    text = text.replace(
        """			set_country_flag = CHI_corruption_lost
			CHI_corruption_low = {}""",
        """			set_country_flag = CHI_corruption_lost
			remove_country_modifier = CHI_corruption_low""",
    )
    path.write_bytes(text.encode("utf-8"))
    print("CHI.txt corruption wired")


def patch_loc():
    path = ROOT / "localisation" / "a.csv"
    data = path.read_bytes()
    text = data.decode("cp1251")
    kept = []
    removed = 0
    for line in text.splitlines(True):
        key = line.split(";", 1)[0] if line.strip() else ""
        if key in LOC_KEYS:
            removed += 1
            continue
        kept.append(line)
    body = "".join(kept)
    if not body.endswith("\n"):
        body += "\r\n"
    body += build_loc()
    out = body.encode("cp1251", errors="strict")
    if b"\xef\xbf\xbd" in out:
        raise SystemExit("FFFD in loc")
    path.write_bytes(out.replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n"))
    print("a.csv ok, replaced keys", removed)


def patch_triggered():
    path = ROOT / "common" / "triggered_modifiers.txt"
    text = path.read_bytes().decode("utf-8")
    start = f"# {MARK}_START"
    end = f"# {MARK}_END"
    block = f"""{start}
CHI_fleet_anti_piracy_ready = {{
	trigger = {{
		tag = CHI
		total_amount_of_ships = 200
	}}
	prestige = 0.01
}}
CHI_inefficient_bureaucracy_4 = {{
	trigger = {{
		tag = CHI
		OR = {{
			war_exhaustion = 20
			average_militancy = 6
		}}
		NOT = {{ literacy = 0.20 }}
		NOT = {{ ideological_thought = 1 }}
		NOT = {{ state_n_government = 1 }}
		NOT = {{ has_country_flag = CHI_high_corruption_lost }}
		school_reforms = no_schools
	}}
	tax_efficiency = -0.11
	administrative_efficiency_modifier = -0.13
	icon = 52
}}
CHI_inefficient_bureaucracy_3 = {{
	trigger = {{
		tag = CHI
		NOT = {{ war_exhaustion = 20 }}
		NOT = {{ average_militancy = 6 }}
		NOT = {{ literacy = 0.20 }}
		NOT = {{ ideological_thought = 1 }}
		NOT = {{ state_n_government = 1 }}
		NOT = {{ has_country_flag = CHI_high_corruption_lost }}
		school_reforms = no_schools
	}}
	tax_efficiency = -0.08
	administrative_efficiency_modifier = -0.10
	icon = 52
}}
CHI_inefficient_bureaucracy_2 = {{
	trigger = {{
		tag = CHI
		OR = {{
			literacy = 0.20
			ideological_thought = 1
			state_n_government = 1
			has_country_flag = CHI_high_corruption_lost
			NOT = {{ school_reforms = no_schools }}
		}}
		NOT = {{
			AND = {{
				literacy = 0.30
				OR = {{
					ideological_thought = 1
					state_n_government = 1
					empiricism = 1
				}}
			}}
		}}
		NOT = {{
			AND = {{
				literacy = 0.45
				has_country_flag = CHI_corruption_lost
				OR = {{
					state_n_government = 1
					empiricism = 1
					functionalism = 1
				}}
				NOT = {{ school_reforms = no_schools }}
			}}
		}}
	}}
	tax_efficiency = -0.05
	administrative_efficiency_modifier = -0.06
	icon = 52
}}
CHI_inefficient_bureaucracy_1 = {{
	trigger = {{
		tag = CHI
		literacy = 0.30
		OR = {{
			ideological_thought = 1
			state_n_government = 1
			empiricism = 1
		}}
		NOT = {{
			AND = {{
				literacy = 0.45
				has_country_flag = CHI_corruption_lost
				OR = {{
					state_n_government = 1
					empiricism = 1
					functionalism = 1
				}}
				NOT = {{ school_reforms = no_schools }}
			}}
		}}
	}}
	tax_efficiency = -0.02
	administrative_efficiency_modifier = -0.03
	icon = 52
}}
{end}
"""
    if start in text:
        s = text.index(start)
        e = text.index(end) + len(end)
        text = text[:s] + block + text[e:]
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + block
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("triggered_modifiers.txt ok")


def main():
    regions = parse_chi_regions()
    used = {k: v for k, v in regions.items() if k in LEVELS and k not in SKIP}
    missing = [k for k in LEVELS if k not in SKIP and k not in regions]
    if missing:
        print("WARN missing regions", missing)
    rids = [k.split("_")[1] for k in used]
    print("regions", len(used), "rids", rids)
    patch_event_modifiers()
    patch_setup(used)
    patch_jan(rids)
    patch_chi_decisions()
    patch_poptypes()
    patch_loc()
    patch_triggered()
    print("done")


if __name__ == "__main__":
    main()

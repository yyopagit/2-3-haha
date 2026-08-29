# -*- coding: utf-8 -*-
"""Clean selector tooltips, one water repair + CD, 10x lower pop-growth penalties."""
from pathlib import Path
import re

ROOT = Path(r"c:\Games\Vic2LV2\Victoria 2\mod\5")
WRAP = ROOT / "assets" / "_chi_crisis_wrapper1.py"

src = WRAP.read_text(encoding="utf-8")
src = src.replace('if __name__ == "__main__":', "if False:")
ns = {}
exec(compile(src, str(WRAP), "exec"), ns)

gen_set_act = ns["gen_set_act"]
gen_clr_act = ns["gen_clr_act"]
gen_region_or = ns["gen_region_or"]
famine_drop_block = ns["famine_drop_block"]
water_drop_block = ns["water_drop_block"]
parse_chi_regions = ns["parse_chi_regions"]
regions_used = ns["regions_used"]
ids_trigger = ns["ids_trigger"]
LEVELS = ns["LEVELS"]
SKIP = ns["SKIP"]
extract_event = ns["extract_event"]
loc_line = ns["loc_line"]
loc_mod_line = ns["loc_mod_line"]
LOC_KEYS = ns["LOC_KEYS"]
bar = ns["bar"]
level_bar = ns["level_bar"]
build_loc = ns["build_loc"]
bureaucracy_refresh_effect = ns["bureaucracy_refresh_effect"]
yellow_progress_effect = ns["yellow_progress_effect"]
yellow_migrate_effect = ns["yellow_migrate_effect"]
patch_triggered = ns["patch_triggered"]


def rids_used():
    return ns["rids_used"]()


def patch_pop_growth():
    print("skip pop growth (values already set in event_modifiers)")


def pay_flag(flag, amount, corrupt_amount, level_mod=None, indent="\t\t"):
    """Pay from owner. Vic2 cannot read or write more than 2 000 000 in one money line,
    so 4 000 000 is two lines of 2 000 000, never money = 4000000."""
    mod_line = f"{indent}\t\thas_province_modifier = {level_mod}\n" if level_mod else ""

    def chunks_of(amt):
        left = amt
        out = []
        while left > 0:
            n = min(left, 2000000)
            out.append(n)
            left -= n
        return out

    def one_pay(amt, corrupt):
        cor = "has_country_modifier = CHI_corruption_high" if corrupt else "NOT = { has_country_modifier = CHI_corruption_high }"
        chunks = chunks_of(amt)
        blocks = []
        for i, n in enumerate(chunks):
            is_last = i == len(chunks) - 1
            if i == 0:
                extra = (
                    f"{mod_line}{indent}\t\towner = {{ {cor} }}\n"
                    f"{indent}\t\towner = {{ money = {n} }}\n"
                )
                if is_last:
                    body = (
                        f"{indent}\t\tmoney = -{n}\n"
                        f"{indent}\t\tset_country_flag = CHI_crisis_paid"
                    )
                else:
                    body = (
                        f"{indent}\t\tmoney = -{n}\n"
                        f"{indent}\t\tset_country_flag = CHI_pay_part"
                    )
            else:
                extra = (
                    f"{indent}\t\towner = {{ has_country_flag = CHI_pay_part }}\n"
                    f"{indent}\t\towner = {{ money = {n} }}\n"
                )
                if is_last:
                    body = (
                        f"{indent}\t\tmoney = -{n}\n"
                        f"{indent}\t\tset_country_flag = CHI_crisis_paid\n"
                        f"{indent}\t\tclr_country_flag = CHI_pay_part"
                    )
                else:
                    body = f"{indent}\t\tmoney = -{n}"
            blocks.append(
                f"""{indent}random_owned = {{
{indent}	limit = {{
{indent}		has_building = province_selector
{extra}{indent}	}}
{indent}	owner = {{
{body}
{indent}	}}
{indent}}}"""
            )
        if len(chunks) > 1:
            blocks.append(
                f"""{indent}random_owned = {{
{indent}	limit = {{
{indent}		has_building = province_selector
{indent}		owner = {{ has_country_flag = CHI_pay_part }}
{indent}		owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
{indent}	}}
{indent}	owner = {{
{indent}		money = {chunks[0]}
{indent}		clr_country_flag = CHI_pay_part
{indent}	}}
{indent}}}"""
            )
        return "\n".join(blocks)

    return one_pay(amount, False) + "\n" + one_pay(corrupt_amount, True)


def pay_by_selected(level_mod, amount, corrupt_amount, indent="\t\t"):
    return pay_flag("CHI_crisis_selected", amount, corrupt_amount, level_mod, indent)


def region_clear_mods(rids, mods, indent="\t\t\t"):
    orlim = gen_region_or(rids)
    rms = "\n".join(f"{indent}\tremove_province_modifier = {m}" for m in mods)
    return f"""{indent}any_owned = {{
{indent}	limit = {{
{indent}		OR = {{
{orlim}
{indent}		}}
{indent}	}}
{rms}
{indent}}}"""


def if_paid(inner):
    return f"""			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_flag = CHI_crisis_paid }}
				}}
				owner = {{
{inner}
				}}
			}}"""


SEP_CRISIS = (
    "CHI_separatism_1",
    "CHI_separatism_2",
    "CHI_separatism_3",
    "CHI_separatism_4",
)
FOOD_CRISIS = (
    "CHI_water_1",
    "CHI_water_2",
    "CHI_water_3",
    "CHI_water_4",
    "CHI_water_canal_silt",
    "CHI_water_yangtze_nav",
    "CHI_water_yellow_dikes",
    "CHI_famine_1",
    "CHI_famine_2",
    "CHI_famine_3",
    "CHI_famine_4",
)
WATER_MENU_CRISIS = (
    "CHI_hydro_cd",
    "CHI_water_1",
    "CHI_water_2",
    "CHI_water_3",
    "CHI_water_4",
)
RIVER_CRISIS = (
    "CHI_water_canal_silt",
    "CHI_water_yangtze_nav",
    "CHI_water_yellow_dikes",
)
GRANARY_MENU_CRISIS = (
    "CHI_famine_1",
    "CHI_famine_2",
    "CHI_famine_3",
    "CHI_famine_4",
    "CHI_food_cd",
    "CHI_great_granary",
)
PIRACY_ALL = ("CHI_piracy_1", "CHI_piracy_2", "CHI_piracy_3", "CHI_piracy_4")
PIRACY_PORT = ("CHI_piracy_2", "CHI_piracy_3", "CHI_piracy_4")
UNIQUE_WATER = (
    "CHI_water_canal_silt",
    "CHI_water_yangtze_nav",
    "CHI_water_yellow_dikes",
)
WATER_LEVELS = ("CHI_water_1", "CHI_water_2", "CHI_water_3", "CHI_water_4")

# Option triggers on province_event are ignored here, so each combo is its own event.
HUB_COMBOS = (
    (144408, True, True, True),
    (144409, True, True, False),
    (144410, True, False, True),
    (144411, False, True, True),
    (144412, True, False, False),
    (144413, False, True, False),
    (144414, False, False, True),
    (144415, False, False, False),
)
FOOD_COMBOS = (
    (144441, True, True, True),
    (144416, True, True, False),
    (144417, True, False, True),
    (144423, False, True, True),
    (144424, True, False, False),
    (144425, False, True, False),
    (144500, False, False, True),
    (144501, False, False, False),
)
RIVER_COMBOS = (
    (144418, True, True, True),
    (144419, True, True, False),
    (144420, True, False, True),
    (144421, False, True, True),
    (144422, True, False, False),
    (144428, False, True, False),
    (144429, False, False, True),
)
# base, piracy_2_4, ships200
COAST_COMBOS = (
    (144442, True, True, True),
    (144444, True, True, False),
    (144445, False, True, True),
    (144446, False, True, False),
    (144447, True, False, True),
    (144448, True, False, False),
    (144426, False, False, True),
    (144427, False, False, False),
)


def _or_mods(mods, pad):
    inner = "\n".join(f"{pad}\thas_province_modifier = {m}" for m in mods)
    return f"{pad}OR = {{\n{inner}\n{pad}}}"


def _not_or_mods(mods, pad):
    return f"{pad}NOT = {{\n{_or_mods(mods, pad + chr(9))}\n{pad}}}"


def _coast_yes(pad):
    return f"{pad}is_coastal = yes\n{_or_mods(PIRACY_ALL, pad)}"


def _coast_no(pad):
    return (
        f"{pad}NOT = {{\n"
        f"{pad}\tis_coastal = yes\n"
        f"{_or_mods(PIRACY_ALL, pad + chr(9))}\n"
        f"{pad}}}"
    )


def _rand_pe(eid, limit_lines, rand_pad):
    lp = rand_pad + "\t"
    body = "\n".join(limit_lines)
    return (
        f"{rand_pad}random_owned = {{\n"
        f"{lp}limit = {{\n"
        f"{body}\n"
        f"{lp}}}\n"
        f"{lp}province_event = {{ id = {eid} days = 0 }}\n"
        f"{rand_pad}}}"
    )


def matching_hub_randoms(rand_pad):
    """Exclusive limits: exactly one hub event fires for the selector province."""
    lp = rand_pad + "\t\t"
    chunks = []
    for eid, sep, food, coast in HUB_COMBOS:
        bits = [f"{lp}has_building = province_selector"]
        bits.append(_or_mods(SEP_CRISIS, lp) if sep else _not_or_mods(SEP_CRISIS, lp))
        bits.append(_or_mods(FOOD_CRISIS, lp) if food else _not_or_mods(FOOD_CRISIS, lp))
        bits.append(_coast_yes(lp) if coast else _coast_no(lp))
        chunks.append(_rand_pe(eid, bits, rand_pad))
    return "\n".join(chunks)


def fire_matching_hub():
    """From a province_event option: pick the hub that matches THIS selector province."""
    inner = matching_hub_randoms("\t\t\t")
    return f"		owner = {{\n{inner}\n		}}"


def fire_matching_food():
    rp = "\t\t\t"
    lp = rp + "\t\t"
    chunks = []
    for eid, water, granary, river in FOOD_COMBOS:
        bits = [f"{lp}has_building = province_selector"]
        bits.append(_or_mods(WATER_MENU_CRISIS, lp) if water else _not_or_mods(WATER_MENU_CRISIS, lp))
        bits.append(
            _or_mods(GRANARY_MENU_CRISIS, lp) if granary else _not_or_mods(GRANARY_MENU_CRISIS, lp)
        )
        bits.append(_or_mods(RIVER_CRISIS, lp) if river else _not_or_mods(RIVER_CRISIS, lp))
        chunks.append(_rand_pe(eid, bits, rp))
    inner = "\n".join(chunks)
    return f"		owner = {{\n{inner}\n		}}"


def fire_matching_coast():
    rp = "\t\t\t"
    lp = rp + "\t\t"
    chunks = []
    for eid, base, port_lv, ships in COAST_COMBOS:
        bits = [
            f"{lp}has_building = province_selector",
            f"{lp}is_coastal = yes",
            _or_mods(PIRACY_ALL, lp),
        ]
        if base:
            bits.append(f"{lp}has_building = naval_base")
        else:
            bits.append(f"{lp}NOT = {{ has_building = naval_base }}")
        if port_lv:
            bits.append(_or_mods(PIRACY_PORT, lp))
        else:
            bits.append(_not_or_mods(PIRACY_PORT, lp))
        if ships:
            bits.append(f"{lp}owner = {{ total_amount_of_ships = 200 }}")
        else:
            bits.append(f"{lp}NOT = {{ owner = {{ total_amount_of_ships = 200 }} }}")
        chunks.append(_rand_pe(eid, bits, rp))
    inner = "\n".join(chunks)
    return f"		owner = {{\n{inner}\n		}}"


def fire_matching_water():
    rp = "\t\t\t"
    lp = rp + "\t\t"
    chunks = [
        _rand_pe(
            144458,
            [
                f"{lp}has_building = province_selector",
                f"{lp}has_province_modifier = CHI_hydro_cd",
            ],
            rp,
        )
    ]
    water_ids = {1: 144470, 2: 144471, 3: 144472, 4: 144473}
    for lvl in range(1, 5):
        others = [
            f"{lp}NOT = {{ has_province_modifier = CHI_water_{o} }}" for o in range(1, 5) if o != lvl
        ]
        common = [
            f"{lp}has_building = province_selector",
            f"{lp}NOT = {{ has_province_modifier = CHI_hydro_cd }}",
            f"{lp}has_province_modifier = CHI_water_{lvl}",
        ] + others
        chunks.append(_rand_pe(water_ids[lvl], common, rp))
    inner = "\n".join(chunks)
    return f"		owner = {{\n{inner}\n		}}"


def fire_matching_river():
    rp = "\t\t\t"
    lp = rp + "\t\t"
    chunks = []
    for eid, canal, yangtze, yellow in RIVER_COMBOS:
        bits = [f"{lp}has_building = province_selector"]
        bits.append(
            f"{lp}has_province_modifier = CHI_water_canal_silt"
            if canal
            else f"{lp}NOT = {{ has_province_modifier = CHI_water_canal_silt }}"
        )
        bits.append(
            f"{lp}has_province_modifier = CHI_water_yangtze_nav"
            if yangtze
            else f"{lp}NOT = {{ has_province_modifier = CHI_water_yangtze_nav }}"
        )
        bits.append(
            f"{lp}has_province_modifier = CHI_water_yellow_dikes"
            if yellow
            else f"{lp}NOT = {{ has_province_modifier = CHI_water_yellow_dikes }}"
        )
        chunks.append(_rand_pe(eid, bits, rp))
    inner = "\n".join(chunks)
    return f"		owner = {{\n{inner}\n		}}"


def worker_immediate(rids, extra_after_act):
    """CHI body for the silent JAN worker (no player tooltip dump)."""
    set_act = gen_set_act(rids)
    clr_act = gen_clr_act(rids)
    return f"""{set_act}
{extra_after_act}
{clr_act}
			clr_country_flag = CHI_crisis_paid"""


def build_workers(rids):
    orlim = gen_region_or(rids)
    wat_drop = water_drop_block(rids)
    fam_drop = famine_drop_block(rids)
    # Region-only CD: only provinces in the marked CHI_reg_* + CHI_act_* region.
    cd_add = f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_hydro_cd duration = 900 }}
			}}"""
    water_fam = f"""			any_owned = {{
				limit = {{
					has_province_modifier = CHI_famine_tied_to_water
					OR = {{
{orlim}
					}}
				}}
				owner = {{ set_country_flag = CHI_do_waterfam }}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_flag = CHI_do_waterfam }}
				}}
				owner = {{
{famine_drop_block(rids, indent="\t\t\t\t")}
					clr_country_flag = CHI_do_waterfam
				}}
			}}"""

    # Always apply — menu option already charged money/goods.
    water_extra = wat_drop + "\n" + water_fam + "\n" + cd_add

    granary_add = f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_great_granary duration = -1 }}
				add_province_modifier = {{ name = CHI_food_cd duration = 730 }}
			}}
{fam_drop}"""
    granary_extra = if_paid(granary_add)

    def river_add(mod_name, cd_name):
        bump = ""
        if mod_name == "CHI_water_yellow_dikes":
            bump = "\n" + ns["yellow_progress_effect"]()
        return f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				remove_province_modifier = {mod_name}
				add_province_modifier = {{ name = {cd_name} duration = 900 }}
			}}{bump}"""

    infra_extra = f"""			any_owned = {{
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
{famine_drop_block(rids, indent="\t\t\t\t")}
				}}
			}}"""

    sep_drop = water_drop_block(rids).replace("CHI_water_", "CHI_separatism_")
    sep_add = f"""{sep_drop}
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_sep_cd duration = 365 }}
			}}"""
    sep_extra = if_paid(sep_add)

    sep_full_add = (
        region_clear_mods(
            rids,
            [
                "CHI_separatism_1",
                "CHI_separatism_2",
                "CHI_separatism_3",
                "CHI_separatism_4",
            ],
        )
        + f"""
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_sep_cd duration = 730 }}
			}}"""
    )
    sep_full_extra = if_paid(sep_full_add)

    water_full_clear = region_clear_mods(
        rids,
        [
            "CHI_water_1",
            "CHI_water_2",
            "CHI_water_3",
            "CHI_water_4",
            "CHI_water_canal_silt",
            "CHI_water_yangtze_nav",
            "CHI_water_yellow_dikes",
        ],
    )
    famine_full_clear = region_clear_mods(
        rids,
        ["CHI_famine_1", "CHI_famine_2", "CHI_famine_3", "CHI_famine_4"],
    )
    famine_full_inner = region_clear_mods(
        rids,
        ["CHI_famine_1", "CHI_famine_2", "CHI_famine_3", "CHI_famine_4"],
        indent="\t\t\t\t",
    )
    water_full_add = f"""{water_full_clear}
			any_owned = {{
				limit = {{
					has_province_modifier = CHI_famine_tied_to_water
					OR = {{
{orlim}
					}}
				}}
				owner = {{ set_country_flag = CHI_do_waterfam }}
			}}
			random_owned = {{
				limit = {{
					is_capital = yes
					owner = {{ has_country_flag = CHI_do_waterfam }}
				}}
				owner = {{
{famine_full_inner}
					clr_country_flag = CHI_do_waterfam
				}}
			}}
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_hydro_cd duration = 730 }}
			}}"""
    water_full_extra = if_paid(water_full_add)

    famine_full_add = (
        famine_full_clear
        + f"""
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_great_granary duration = -1 }}
				add_province_modifier = {{ name = CHI_food_cd duration = 730 }}
			}}"""
    )
    famine_full_extra = if_paid(famine_full_add)

    def ev(eid, work_id, title, desc, extra):
        # JAN country_event does the work (AI auto-clicks, player never sees the dump).
        # Player gets a clean province notice with no effects.
        body = worker_immediate(rids, extra)
        return f"""country_event = {{
	id = {work_id}
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {{
		name = "noloc"
		CHI = {{
{body}
			random_owned = {{
				limit = {{ has_building = province_selector }}
				province_event = {{ id = {eid} days = 0 }}
				province_selector = -1
			}}
		}}
	}}
}}

province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_ok"
		province_selector = -1
	}}
}}
"""

    return {
        "water": ev(144431, 144551, "CHI_sel_water_done", "CHI_sel_water_done_desc", water_extra),
        "granary": ev(144432, 144552, "CHI_sel_granary_done", "CHI_sel_granary_done_desc", granary_extra),
        "unique": ev(144433, 144553, "CHI_sel_canal_done", "CHI_sel_canal_done_desc", river_add("CHI_water_canal_silt", "CHI_canal_cd")),
        "yangtze": ev(144534, 144554, "CHI_sel_yangtze_done", "CHI_sel_yangtze_done_desc", river_add("CHI_water_yangtze_nav", "CHI_yangtze_cd")),
        "yellow": ev(144535, 144555, "CHI_sel_yellow_done", "CHI_sel_yellow_done_desc", river_add("CHI_water_yellow_dikes", "CHI_yellow_cd")),
        "sep": ev(144437, 144556, "CHI_sel_sep_done", "CHI_sel_sep_done_desc", sep_extra),
        "sep_full": ev(144505, 144557, "CHI_sel_sep_full_done", "CHI_sel_sep_full_done_desc", sep_full_extra),
        "water_full": ev(144508, 144558, "CHI_sel_water_full_done", "CHI_sel_water_full_done_desc", water_full_extra),
        "famine_full": ev(144511, 144559, "CHI_sel_famine_full_done", "CHI_sel_famine_full_done_desc", famine_full_extra),
    }


def build_slim_144408():
    return """province_event = {
	title = "CHI_Selector_EvtName"
	desc = "CHI_Selector_EvtDesc"
	id = 144408
	picture = "Administration"
	is_triggered_only = yes

	option = {
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}
	option = {
		name = "Selector_EvtOptSupplyDepot"
		owner = {
			money = -500000
			any_owned = {
				remove_province_modifier = provincial_supply_depot_pmodifier
			}
		}
		add_province_modifier = {
			name = provincial_supply_depot_pmodifier
			duration = -1
		}
		province_selector = -1
	}
	option = {
		name = "CHI_sel_granary"
		trigger = {
			OR = {
				has_province_modifier = CHI_famine_1
				has_province_modifier = CHI_famine_2
				has_province_modifier = CHI_famine_3
				has_province_modifier = CHI_famine_4
			}
			NOT = { has_province_modifier = CHI_great_granary }
			owner = { money = 2000000 }
		}
		province_event = { id = 144432 days = 0 }
		province_selector = -1
	}
	option = {
		name = "CHI_sel_water"
		trigger = {
			NOT = { has_province_modifier = CHI_hydro_cd }
			OR = {
				AND = {
					has_province_modifier = CHI_water_1
					owner = { money = 200000 }
				}
				AND = {
					has_province_modifier = CHI_water_2
					owner = { money = 500000 }
				}
				AND = {
					has_province_modifier = CHI_water_3
					owner = { money = 1000000 }
				}
				AND = {
					has_province_modifier = CHI_water_4
					owner = { money = 2000000 }
				}
			}
		}
		province_event = { id = 144431 days = 0 }
		province_selector = -1
	}
	option = {
		name = "CHI_sel_unique_water"
		trigger = {
			NOT = { has_province_modifier = CHI_hydro_cd }
			OR = {
				has_province_modifier = CHI_water_canal_silt
				has_province_modifier = CHI_water_yangtze_nav
				has_province_modifier = CHI_water_yellow_dikes
			}
			owner = { money = 2000000 }
		}
		province_event = { id = 144433 days = 0 }
		province_selector = -1
	}
	option = {
		name = "CHI_sel_infra"
		trigger = {
			OR = {
				has_province_modifier = CHI_famine_1
				has_province_modifier = CHI_famine_2
				has_province_modifier = CHI_famine_3
				has_province_modifier = CHI_famine_4
			}
			NOT = { has_province_modifier = CHI_famine_infra_relief }
		}
		province_event = { id = 144434 days = 0 }
		province_selector = -1
	}
	option = {
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
	}
	option = {
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
	}
}
"""


def patch_jan():
    print("skip JAN hub (menus live in _chi_crisis_menus.py)")


def write_workers(rids):
    print("skip CHI_crises.txt (split files live in _chi_crisis_menus.py)")


def patch_loc():
    extra_keys = {
        "CHI_sel_water",
        "CHI_sel_ok",
        "CHI_sel_water_done",
        "CHI_sel_water_done_desc",
        "CHI_sel_granary_done",
        "CHI_sel_granary_done_desc",
        "CHI_sel_unique_done",
        "CHI_sel_unique_done_desc",
        "CHI_sel_infra_done",
        "CHI_sel_infra_done_desc",
        "CHI_hydro_cd",
        "CHI_hydro_cd_desc",
        "CHI_sel_water_1",
        "CHI_sel_water_2",
        "CHI_sel_water_3",
        "CHI_sel_water_4",
        "CHI_sel_granary",
    }
    path = ROOT / "localisation" / "a.csv"
    t = path.read_bytes().decode("cp1251")
    kept = []
    for line in t.splitlines(True):
        key = line.split(";", 1)[0] if line.strip() else ""
        if key in extra_keys:
            continue
        kept.append(line)
    add = []
    add.append(loc_line("CHI_sel_water", "Ремонт ирригации региона (деньги + дерево/цемент/железо/пиломатериалы; КД региона ~2.5 года)"))
    add.append(loc_line("CHI_sel_ok", "Принято"))
    add.append(loc_line("CHI_sel_water_done", "Ирригация"))
    add.append(loc_line("CHI_sel_water_done_desc", "Работы в регионе закончены. Уровень проблемы с водой снижен на 1. В этом регионе следующий ремонт примерно через 2.5 года."))
    add.append(loc_line("CHI_sel_granary_done", "Великий амбар"))
    add.append(loc_line("CHI_sel_granary_done_desc", "Амбар заложен по всему региону. Голод снижен на 1 уровень. Сельское хозяйство +5%. Прирост населения амбар не даёт."))
    add.append(loc_line("CHI_sel_unique_done", "Речные работы"))
    add.append(loc_line("CHI_sel_unique_done_desc", "Особая речная проблема региона снята. В этом регионе повтор примерно через 2.5 года."))
    add.append(loc_line("CHI_sel_infra_done", "Инфраструктура"))
    add.append(loc_line("CHI_sel_infra_done_desc", "Провинции с инфраструктурой 2 получили облегчение голода. Если она везде в регионе - голод снижен на 1."))
    add.append(loc_line("CHI_hydro_cd", "Ремонт ирригации региона"))
    add.append(loc_line("CHI_hydro_cd_desc", "В этом регионе уже идут работы по ирригации и дамбам. Следующий заказ здесь примерно через 2.5 года."))
    add.append(loc_line("CHI_sel_granary", "Великий амбар"))
    body = "".join(kept)
    if not body.endswith("\n"):
        body += "\r\n"
    out = (body + "".join(add)).encode("cp1251")
    path.write_bytes(out.replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n"))
    print("a.csv loc updated, fffd", out.count(b"\xef\xbf\xbd"))


def main():
    rids = rids_used()
    print("rids", len(rids))
    patch_pop_growth()
    patch_jan()
    write_workers(rids)
    patch_loc()
    print("done")


if __name__ == "__main__":
    main()

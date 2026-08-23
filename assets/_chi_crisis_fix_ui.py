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
LEVELS = ns["LEVELS"]
SKIP = ns["SKIP"]
extract_event = ns["extract_event"]
loc_line = ns["loc_line"]
LOC_KEYS = ns["LOC_KEYS"]
bar = ns["bar"]
build_loc = ns["build_loc"]


def rids_used():
    regions = parse_chi_regions()
    used = {k: v for k, v in regions.items() if k in LEVELS and k not in SKIP}
    return [k.split("_")[1] for k in used]


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
{indent}		has_province_flag = {flag}
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
{indent}		has_province_flag = {flag}
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
			}}
			clr_country_flag = CHI_crisis_paid"""


def worker_immediate(rids, extra_after_act):
    """Region worker: mark act from clicked province, apply effects, clear act.
    Payment is already done on the menu option — do not gate on CHI_crisis_paid."""
    set_act = gen_set_act(rids)
    clr_act = gen_clr_act(rids)
    return f"""	option = {{
		name = "CHI_sel_ok"
		set_province_flag = CHI_crisis_selected
		owner = {{
{set_act}
{extra_after_act}
{clr_act}
			clr_country_flag = CHI_crisis_paid
		}}
		clr_province_flag = CHI_crisis_selected
		owner = {{
			clr_country_flag = CHI_mode_food
			clr_country_flag = CHI_mode_sep
			clr_country_flag = CHI_mode_water
			clr_country_flag = CHI_mode_granary
			clr_country_flag = CHI_mode_port
			clr_country_flag = CHI_mode_fleet
			clr_country_flag = CHI_mode_depot
			clr_country_flag = CHI_mode_hub
			set_country_flag = CHI_mode_hub
			any_owned = {{ clr_province_flag = CHI_click }}
		}}
		set_province_flag = CHI_click
		owner = {{ country_event = {{ id = 144440 days = 0 }} }}
	}}"""


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
				set_province_flag = CHI_do_waterfam
			}}
			random_owned = {{
				limit = {{ has_province_flag = CHI_do_waterfam }}
				owner = {{
{famine_drop_block(rids, indent="\t\t\t\t")}
				}}
			}}
			any_owned = {{ clr_province_flag = CHI_do_waterfam }}"""

    # Always apply — menu option already charged money/goods.
    water_extra = wat_drop + "\n" + water_fam + "\n" + cd_add

    granary_add = f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_great_granary duration = -1 }}
			}}
{fam_drop}"""
    granary_extra = if_paid(granary_add)

    uniq_add = f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				remove_province_modifier = CHI_water_canal_silt
				remove_province_modifier = CHI_water_yangtze_nav
				remove_province_modifier = CHI_water_yellow_dikes
				add_province_modifier = {{ name = CHI_hydro_cd duration = 900 }}
			}}"""
    uniq_extra = uniq_add

    infra_extra = f"""			any_owned = {{
				limit = {{
					railroad = 2
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
									NOT = {{ railroad = 2 }}
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
				set_province_flag = CHI_do_waterfam
			}}
			random_owned = {{
				limit = {{ has_province_flag = CHI_do_waterfam }}
				owner = {{
{famine_full_inner}
				}}
			}}
			any_owned = {{ clr_province_flag = CHI_do_waterfam }}
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

    def ev(eid, title, desc, extra):
        return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
{worker_immediate(rids, extra)}
}}
"""

    return {
        "water": ev(144431, "CHI_sel_water_done", "CHI_sel_water_done_desc", water_extra),
        "granary": ev(144432, "CHI_sel_granary_done", "CHI_sel_granary_done_desc", granary_extra),
        "unique": ev(144433, "CHI_sel_unique_done", "CHI_sel_unique_done_desc", uniq_extra),
        "sep": ev(144437, "CHI_sel_sep_done", "CHI_sel_sep_done_desc", sep_extra),
        "sep_full": ev(144505, "CHI_sel_sep_full_done", "CHI_sel_sep_full_done_desc", sep_full_extra),
        "water_full": ev(144508, "CHI_sel_water_full_done", "CHI_sel_water_full_done_desc", water_full_extra),
        "famine_full": ev(144511, "CHI_sel_famine_full_done", "CHI_sel_famine_full_done_desc", famine_full_extra),
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
			naval_base = 1
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
    add.append(loc_line("CHI_sel_granary_done_desc", "Амбар заложен по всему региону. Голод снижен на 1 уровень."))
    add.append(loc_line("CHI_sel_unique_done", "Речные работы"))
    add.append(loc_line("CHI_sel_unique_done_desc", "Особая речная проблема региона снята. В этом регионе повтор примерно через 2.5 года."))
    add.append(loc_line("CHI_sel_infra_done", "Инфраструктура"))
    add.append(loc_line("CHI_sel_infra_done_desc", "Провинции с инфраструктурой 2 получили облегчение голода. Если она везде в регионе - голод снижен на 1."))
    add.append(loc_line("CHI_hydro_cd", "Ремонт ирригации региона"))
    add.append(loc_line("CHI_hydro_cd_desc", "В этом регионе уже идут работы по ирригации и дамбам. Следующий заказ здесь примерно через 2.5 года."))
    add.append(loc_line("CHI_sel_granary", "Построить великий амбар в регионе (дерево 250, цемент 150, железо 100, пиломатериалы 80)"))
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

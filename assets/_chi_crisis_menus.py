# -*- coding: utf-8 -*-
"""China crisis selector — direct province_event chain (no country router on CHI).

Vic2 shows country_event windows to the receiving tag. Firing a "silent" router on CHI
dumps every any_owned effect into a visible popup (the spam you saw). Navigation is
therefore only province_event → province_event on the clicked province.
"""
from pathlib import Path
import importlib.util
import re

ROOT = Path(r"c:\Games\Vic2LV2\Victoria 2\mod\5")
FIX = ROOT / "assets" / "_chi_crisis_fix_ui.py"

spec = importlib.util.spec_from_file_location("chi_fix", FIX)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

loc_line = mod.loc_line
extract_event = mod.extract_event
pay_flag = mod.pay_flag


TAX_STACKS = 20
TAX_DAYS = 730
FULL_DAYS = 730
STEP_DAYS = 365
HYDRO_DAYS = 900

# Event IDs (province menus)
HUB_ID = 144408
SEP_MENU_ID = 144480
FOOD_MENU_ID = 144441
COAST_MENU_ID = 144442
MISC_MENU_ID = 144443
WATER_MENU_ID = 144470
GRANARY_MENU_ID = 144475
PORT_MENU_ID = 144463
FLEET_MENU_ID = 144466


def open_pe(eid):
    return f"		province_event = {{ id = {eid} days = 0 }}"


def reopen_hub():
    """Return to the hub that matches this province. Option triggers are ignored
    by this engine, so we fire one of 144408-144415 via exclusive random_owned."""
    return mod.fire_matching_hub()


def reopen_food():
    """One level up from irrigation / granary / river projects: food submenu."""
    return mod.fire_matching_food()


def reopen_coast():
    """One level up from port/fleet info screens: coast submenu."""
    return mod.fire_matching_coast()


def reopen_sep():
    """One level up from tax/revolt notices: separatism submenu."""
    return open_pe(SEP_MENU_ID)


HAS_SEP = """				OR = {
					has_province_modifier = CHI_separatism_1
					has_province_modifier = CHI_separatism_2
					has_province_modifier = CHI_separatism_3
					has_province_modifier = CHI_separatism_4
				}"""

HAS_WATER = """				OR = {
					has_province_modifier = CHI_hydro_cd
					has_province_modifier = CHI_water_1
					has_province_modifier = CHI_water_2
					has_province_modifier = CHI_water_3
					has_province_modifier = CHI_water_4
					has_province_modifier = CHI_water_canal_silt
					has_province_modifier = CHI_water_yangtze_nav
					has_province_modifier = CHI_water_yellow_dikes
				}"""

HAS_FAMINE = """				OR = {
					has_province_modifier = CHI_famine_1
					has_province_modifier = CHI_famine_2
					has_province_modifier = CHI_famine_3
					has_province_modifier = CHI_famine_4
				}"""

HAS_GRANARY_MENU = """				OR = {
					has_province_modifier = CHI_famine_1
					has_province_modifier = CHI_famine_2
					has_province_modifier = CHI_famine_3
					has_province_modifier = CHI_famine_4
					has_province_modifier = CHI_food_cd
					has_province_modifier = CHI_great_granary
				}"""

HAS_FOOD = """				OR = {
					has_province_modifier = CHI_water_1
					has_province_modifier = CHI_water_2
					has_province_modifier = CHI_water_3
					has_province_modifier = CHI_water_4
					has_province_modifier = CHI_water_canal_silt
					has_province_modifier = CHI_water_yangtze_nav
					has_province_modifier = CHI_water_yellow_dikes
					has_province_modifier = CHI_famine_1
					has_province_modifier = CHI_famine_2
					has_province_modifier = CHI_famine_3
					has_province_modifier = CHI_famine_4
				}"""

HAS_COAST = """				is_coastal = yes
				OR = {
					has_province_modifier = CHI_piracy_1
					has_province_modifier = CHI_piracy_2
					has_province_modifier = CHI_piracy_3
					has_province_modifier = CHI_piracy_4
				}"""


def hub_event(eid, sep, food, coast):
    """Hub without option triggers: only the buttons that belong to this combo."""
    opts = []
    if sep:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_sep"
{open_pe(SEP_MENU_ID)}
	}}"""
        )
    if food:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_food"
{mod.fire_matching_food()}
	}}"""
        )
    if coast:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_coast"
{mod.fire_matching_coast()}
	}}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_menu_misc"
{open_pe(MISC_MENU_ID)}
	}}"""
    )
    opts.append(
        """	option = {
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}"""
    )
    desc = "CHI_Selector_EvtDesc_none" if not (sep or food or coast) else "CHI_Selector_EvtDesc"
    joined = "\n".join(opts)
    return f"""province_event = {{
	title = "CHI_Selector_EvtName"
	desc = "{desc}"
	id = {eid}
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def alias_event(eid, target, title="CHI_Selector_EvtName", desc="CHI_Selector_EvtDesc"):
    """Old ids: fire the real menu from option, never from immediate (Vic2 CTD)."""
    return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_ok"
		province_event = {{ id = {target} days = 0 }}
	}}
}}
"""


def build_hubs():
    return "\n".join(hub_event(eid, sep, food, coast) for eid, sep, food, coast in mod.HUB_COMBOS)


def build_hub():
    return build_hubs()


def _food_menu(eid, water, granary, river):
    back = reopen_hub()
    opts = []
    if water:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_hydro"
{mod.fire_matching_water()}
	}}"""
        )
    if granary:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_granary"
{open_pe(GRANARY_MENU_ID)}
	}}"""
        )
    if river:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_river"
{mod.fire_matching_river()}
	}}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_back"
{back}
	}}"""
    )
    joined = "\n".join(opts)
    return f"""province_event = {{
	title = "CHI_menu_food_title"
	desc = "CHI_menu_food_desc"
	id = {eid}
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def build_food_submenu():
    return "\n".join(
        _food_menu(eid, water, granary, river) for eid, water, granary, river in mod.FOOD_COMBOS
    )


def _coast_menu(eid, base, port_lv, ships):
    back = reopen_hub()
    opts = []
    if port_lv and base:
        opts.append(
            """	option = {
		name = "CHI_sel_port_piracy"
		province_event = { id = 144465 days = 0 }
	}"""
        )
    if port_lv and not base:
        opts.append(
            """	option = {
		name = "CHI_need_port"
		province_event = { id = 144463 days = 0 }
	}"""
        )
    if ships:
        opts.append(
            """	option = {
		name = "CHI_sel_fleet_piracy"
		province_event = { id = 144466 days = 0 }
	}"""
        )
    else:
        opts.append(
            """	option = {
		name = "CHI_need_fleet"
		province_event = { id = 144464 days = 0 }
	}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_ok"
{back}
	}}"""
    )
    joined = "\n".join(opts)
    return f"""province_event = {{
	title = "CHI_menu_coast_title"
	desc = "CHI_menu_coast_desc"
	id = {eid}
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def build_coast_submenu():
    return "\n".join(
        _coast_menu(eid, base, port_lv, ships) for eid, base, port_lv, ships in mod.COAST_COMBOS
    )


def build_misc_submenu():
    back = reopen_hub()
    return f"""
province_event = {{
	title = "CHI_menu_misc_title"
	desc = "CHI_menu_misc_desc"
	id = {MISC_MENU_ID}
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_depot"
		trigger = {{
			owner = {{ money = 500000 }}
		}}
		province_event = {{ id = 144467 days = 0 }}
	}}
	option = {{
		name = "CHI_sel_back"
{back}
	}}
}}
"""


def build_submenus():
    return "# CHI_MENUS_START\n" + build_food_submenu() + build_coast_submenu() + build_misc_submenu()


def build_dispatcher():
    """No country router. Kept as empty stub so old callers do not break."""
    return """
# Router removed: country_event on CHI was visible and dumped any_owned tooltips.
# Navigation is province_event → province_event only.
"""


def fire_need(flag, pmod, eid):
    return f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
					has_province_modifier = {pmod}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {eid} days = 1 }}
			}}"""


def fire_paid(flag, eid):
    return f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ has_country_flag = CHI_crisis_paid }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {eid} days = 1 }}
			}}"""


def wait_cd(flag, cd_mod):
    """Immediate only: block pay if CD is up. Do not fire events from immediate (Vic2 CTD)."""
    return f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					has_province_modifier = {cd_mod}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{
					set_country_flag = CHI_pay_fired
					set_country_flag = CHI_pay_wait
				}}
			}}"""


def fire_wait(wait_id):
    return f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ has_country_flag = CHI_pay_wait }}
				}}
				owner = {{ clr_country_flag = CHI_pay_wait }}
				province_event = {{ id = {wait_id} days = 1 }}
			}}"""


def granary_goods_pay():
    """Deduct stockpile goods if enough; set CHI_crisis_paid on success."""
    return """			random_owned = {
				limit = {
					has_building = province_selector
					owner = {
						timber = 250
						cement = 150
						iron = 100
						lumber = 80
					}
					owner = { NOT = { has_country_flag = CHI_crisis_paid } }
				}
				owner = {
					timber = -250
					cement = -150
					iron = -100
					lumber = -80
					set_country_flag = CHI_crisis_paid
				}
			}"""


def fire_goods_fallback(flag):
    return f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144524 days = 1 }}
			}}"""


def build_pay_dispatcher():
    bribe_pay = pay_flag("CHI_do_bribe", 500000, 1000000)
    water_need = {
        1: fire_need("CHI_do_water_pay", "CHI_water_1", 144450),
        2: fire_need("CHI_do_water_pay", "CHI_water_2", 144451),
        3: fire_need("CHI_do_water_pay", "CHI_water_3", 144452),
        4: fire_need("CHI_do_water_pay", "CHI_water_4", 144454),
    }
    def stage(eid, imm_body, opt_body, title, desc):
        # Immediate: money/goods only. Option: follow-up events.
        # Vic2 CTDs if province_event is fired from immediate.
        return f"""
province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		owner = {{
			clr_country_flag = CHI_crisis_paid
			clr_country_flag = CHI_pay_fired
			clr_country_flag = CHI_pay_part
			clr_country_flag = CHI_pay_wait
{imm_body}
		}}
	}}
	option = {{
		name = "CHI_sel_ok"
		owner = {{
{opt_body}
			clr_country_flag = CHI_pay_fired
			clr_country_flag = CHI_pay_part
			clr_country_flag = CHI_pay_wait
		}}
	}}
}}
"""

    bribe_fail = f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
					owner = {{ has_country_modifier = CHI_corruption_high }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144452 days = 1 }}
			}}
			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144451 days = 1 }}
			}}"""

    return {
        "sep": stage(
            144493,
            f"""{wait_cd("CHI_do_bribe", "CHI_sep_cd")}
{bribe_pay}""",
            f"""{fire_wait(144456)}
{fire_paid("CHI_do_bribe", 144437)}
{bribe_fail}""",
            "CHI_pay_bribe",
            "CHI_pay_bribe_desc",
        ),
        "water_1": stage(
            144494,
            f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd")}
{water_level_pay(1, WATER_REPAIR[1])}""",
            f"""{fire_wait(144458)}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need[1]}
{fire_goods_fallback("CHI_do_water_pay")}""",
            "CHI_pay_water_1",
            "CHI_pay_water_1_desc",
        ),
        "water_2": stage(
            144497,
            f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd")}
{water_level_pay(2, WATER_REPAIR[2])}""",
            f"""{fire_wait(144458)}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need[2]}
{fire_goods_fallback("CHI_do_water_pay")}""",
            "CHI_pay_water_2",
            "CHI_pay_water_2_desc",
        ),
        "water_3": stage(
            144498,
            f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd")}
{water_level_pay(3, WATER_REPAIR[3])}""",
            f"""{fire_wait(144458)}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need[3]}
{fire_goods_fallback("CHI_do_water_pay")}""",
            "CHI_pay_water_3",
            "CHI_pay_water_3_desc",
        ),
        "water_4": stage(
            144499,
            f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd")}
{water_level_pay(4, WATER_REPAIR[4])}""",
            f"""{fire_wait(144458)}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need[4]}
{fire_goods_fallback("CHI_do_water_pay")}""",
            "CHI_pay_water_4",
            "CHI_pay_water_4_desc",
        ),
        "canal": stage(
            144495,
            f"""{wait_cd("CHI_do_canal_pay", "CHI_canal_cd")}
{canal_goods_pay()}""",
            f"""{fire_wait(144536)}
{fire_paid("CHI_do_canal_pay", 144433)}
{fire_need("CHI_do_canal_pay", "CHI_water_canal_silt", 144452)}
{fire_goods_fallback("CHI_do_canal_pay")}""",
            "CHI_pay_canal",
            "CHI_pay_canal_desc",
        ),
        "yangtze": stage(
            144531,
            f"""{wait_cd("CHI_do_yangtze_pay", "CHI_yangtze_cd")}
{yangtze_goods_pay()}""",
            f"""{fire_wait(144536)}
{fire_paid("CHI_do_yangtze_pay", 144534)}
{fire_need("CHI_do_yangtze_pay", "CHI_water_yangtze_nav", 144452)}
{fire_goods_fallback("CHI_do_yangtze_pay")}""",
            "CHI_pay_yangtze",
            "CHI_pay_yangtze_desc",
        ),
        "yellow": stage(
            144532,
            f"""{wait_cd("CHI_do_yellow_pay", "CHI_yellow_cd")}
{yellow_goods_pay()}""",
            f"""{fire_wait(144536)}
{fire_paid("CHI_do_yellow_pay", 144535)}
{fire_need("CHI_do_yellow_pay", "CHI_water_yellow_dikes", 144453)}
{fire_goods_fallback("CHI_do_yellow_pay")}""",
            "CHI_pay_yellow",
            "CHI_pay_yellow_desc",
        ),
        "granary": stage(
            144496,
            granary_goods_pay(),
            f"""{fire_paid("CHI_do_granary_pay", 144432)}
			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144524 days = 1 }}
			}}""",
            "CHI_pay_granary",
            "CHI_pay_granary_desc",
        ),
    }


def back_effect(back_id):
    if back_id == "hub":
        return reopen_hub()
    if back_id == "food":
        return reopen_food()
    if back_id == "coast":
        return reopen_coast()
    if back_id == "misc":
        return open_pe(MISC_MENU_ID)
    if back_id == "sep":
        return reopen_sep()
    if back_id == "ok":
        return ""
    return f"		province_event = {{ id = {back_id} days = 0 }}"


def notice(eid, title, desc, back_id):
    return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_ok"
{back_effect(back_id)}
	}}
}}
"""


def confirm(eid, title, desc, opt_name, opt_effect, back_id):
    return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "{opt_name}"
{opt_effect}
	}}
	option = {{
		name = "CHI_sel_back"
{back_effect(back_id)}
	}}
}}
"""


def pay_click(flag, pay_id):
    return f"		province_event = {{ id = {pay_id} days = 0 }}"


def bribe_sep_effect():
    """Flat 500k bribe via pay stage 144493. Tooltip stays on CHI."""
    return pay_click("CHI_do_bribe", 144493)


def granary_build_effect():
    """Regional granary: goods from stockpile via pay stage 144496."""
    return pay_click("CHI_do_granary_pay", 144496)


def revolt_confirm_effect():
    """Effects live on the confirm option, not on the menu button or in immediate."""
    return f"""		any_pop = {{
			limit = {{
				OR = {{
					type = farmers
					type = labourers
					type = craftsmen
					type = soldiers
					type = artisans
				}}
			}}
			militancy = 10
			consciousness = 5
		}}
		add_province_modifier = {{ name = CHI_sep_revolt_cd duration = {TAX_DAYS} }}
		add_province_modifier = {{ name = CHI_sep_uprising duration = 180 }}
		add_province_modifier = {{ name = CHI_sep_revolt_pending duration = -1 }}
		remove_province_modifier = CHI_sep_revolt_won
		owner = {{ set_country_flag = CHI_sep_revolt_active }}
{reopen_hub()}"""


def sep_methods(eid=SEP_MENU_ID, lvl=1):
    tax_prov = "		province_event = { id = 144512 days = 0 }"
    return f"""province_event = {{
	id = {SEP_MENU_ID}
	title = "CHI_sep_menu_title"
	desc = "CHI_menu_sep_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_bribe"
		trigger = {{
			NOT = {{ has_province_modifier = CHI_sep_cd }}
		}}
{bribe_sep_effect()}
	}}
	option = {{
		name = "CHI_sel_tax_cut"
		trigger = {{
			NOT = {{ has_province_modifier = CHI_sep_tax_cut }}
		}}
{tax_prov}
	}}
	option = {{
		name = "CHI_sel_revolt"
		trigger = {{
			NOT = {{ has_province_modifier = CHI_sep_revolt_cd }}
		}}
		province_event = {{ id = 144525 days = 0 }}
	}}
	option = {{
		name = "CHI_sel_back"
{reopen_hub()}
	}}
}}
"""


def build_money_notices():
    return "\n".join(
        [
            notice(144450, "CHI_need_200k", "CHI_need_money_desc", "food"),
            notice(144451, "CHI_need_500k", "CHI_need_money_desc", "hub"),
            notice(144452, "CHI_need_1m", "CHI_need_money_desc", "hub"),
            notice(144453, "CHI_need_15m", "CHI_need_money_desc", "food"),
            notice(144454, "CHI_need_2m", "CHI_need_money_desc", "food"),
            notice(144524, "CHI_need_goods", "CHI_need_goods_desc", "food"),
        ]
    )


def build_sep_leaves():
    revolt_ok = f"""province_event = {{
	id = 144525
	title = "CHI_sel_revolt"
	desc = "CHI_sel_revolt_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_ok"
{revolt_confirm_effect()}
	}}
}}
"""
    parts = [
        notice(144455, "CHI_sel_sep_none", "CHI_sel_sep_none_desc", "hub"),
        notice(144456, "CHI_sel_sep_wait", "CHI_sel_sep_wait_desc", "hub"),
        notice(144491, "CHI_sel_revolt_won", "CHI_sel_revolt_won_desc", "sep"),
        notice(144513, "CHI_sel_tax_done", "CHI_sel_tax_done_desc", "sep"),
        sep_methods(),
        revolt_ok,
    ]
    for eid in range(144481, 144490):
        parts.append(alias_event(eid, SEP_MENU_ID, "CHI_sep_menu_title", "CHI_menu_sep_desc"))
    return "\n".join(parts)



# Money + goods for irrigation. Costs on the option effect (tooltip shows deductions only).
WATER_REPAIR = {
    1: {"money": 200000, "corrupt": 400000, "timber": 2400, "cement": 1200, "iron": 600, "lumber": 600},
    2: {"money": 500000, "corrupt": 1000000, "timber": 3600, "cement": 1800, "iron": 1200, "lumber": 900},
    3: {"money": 1000000, "corrupt": 2000000, "timber": 5400, "cement": 3000, "iron": 1800, "lumber": 1500},
    4: {"money": 2000000, "corrupt": 4000000, "timber": 7500, "cement": 4500, "iron": 3000, "lumber": 2400},
}
UNIQUE_REPAIR = {
    "money": 2000000,
    "corrupt": 4000000,
    "timber": 6000,
    "cement": 3600,
    "iron": 2400,
    "lumber": 1800,
}
CANAL_REPAIR = {
    "money": 1000000,
    "corrupt": 2000000,
    "timber": 3000,
    "cement": 1500,
    "iron": 1000,
    "lumber": 800,
}
YANGTZE_REPAIR = {
    "money": 1000000,
    "corrupt": 2000000,
    "timber": 2500,
    "cement": 1200,
    "iron": 1500,
    "lumber": 700,
}
YELLOW_REPAIR = {
    "money": 1500000,
    "corrupt": 3000000,
    "timber": 4000,
    "cement": 2500,
    "iron": 1500,
    "lumber": 1200,
}


def _money_pay_lines(amount, indent="\t\t\t"):
    """Vic2 rejects |money| > 2 000 000 in one command."""
    left = abs(int(amount))
    lines = []
    while left > 0:
        n = min(left, 2000000)
        lines.append(f"{indent}money = -{n}")
        left -= n
    return "\n".join(lines)


def _goods_trigger(c, indent="\t\t\t\t"):
    return (
        f"{indent}timber = {c['timber']}\n"
        f"{indent}cement = {c['cement']}\n"
        f"{indent}iron = {c['iron']}\n"
        f"{indent}lumber = {c['lumber']}"
    )


def _goods_pay(c, indent="\t\t\t"):
    return (
        f"{indent}timber = -{c['timber']}\n"
        f"{indent}cement = -{c['cement']}\n"
        f"{indent}iron = -{c['iron']}\n"
        f"{indent}lumber = -{c['lumber']}"
    )



def pay_goods_flag(flag, amount, corrupt_amount, costs, level_mod=None, indent="\t\t"):
    """Money + goods pay blocks (Vic2 max 2M per money line)."""
    mod_line = f"{indent}\t\thas_province_modifier = {level_mod}\n" if level_mod else ""
    # Goods checks belong in owner = { } (national stockpile). Province-scope
    # timber = N is not the country stockpile and fails or is ignored.
    gt = _goods_trigger(costs, indent + "\t\t\t")
    gp = _goods_pay(costs, indent + "\t\t")

    def chunks_of(amt):
        left = amt
        out = []
        while left > 0:
            n = min(left, 2000000)
            out.append(n)
            left -= n
        return out

    def one_pay(amt, corrupt):
        cor = (
            "has_country_modifier = CHI_corruption_high"
            if corrupt
            else "NOT = { has_country_modifier = CHI_corruption_high }"
        )
        chunks = chunks_of(amt)
        blocks = []
        for i, n in enumerate(chunks):
            is_last = i == len(chunks) - 1
            is_multi = len(chunks) > 1
            goods_lim = gt if is_last else ""
            goods_body = gp if is_last else ""

            if is_multi and i == 0:
                extra = (
                    f"{mod_line}{indent}\t\towner = {{\n"
                    f"{indent}\t\t\t{cor}\n"
                    f"{indent}\t\t\tmoney = {n}\n"
                    f"{gt}\n"
                    f"{indent}\t\t}}\n"
                    f"{indent}\t\towner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}\n"
                    f"{indent}\t\towner = {{ NOT = {{ has_country_flag = CHI_pay_part }} }}\n"
                )
                body = f"{indent}\t\tmoney = -{n}\n{indent}\t\tset_country_flag = CHI_pay_part"
            elif is_multi and is_last:
                if corrupt:
                    extra = (
                        f"{mod_line}{indent}\t\towner = {{\n"
                        f"{indent}\t\t\t{cor}\n"
                        f"{indent}\t\t\tmoney = {n}\n"
                        f"{indent}\t\t\thas_country_flag = CHI_pay_part\n"
                        f"{goods_lim}\n"
                        f"{indent}\t\t}}\n"
                    )
                else:
                    extra = (
                        f"{mod_line}{indent}\t\towner = {{ has_country_flag = CHI_pay_part }}\n"
                        f"{indent}\t\towner = {{\n"
                        f"{indent}\t\t\t{cor}\n"
                        f"{indent}\t\t\tmoney = {n}\n"
                        f"{goods_lim}\n"
                        f"{indent}\t\t}}\n"
                    )
                body = (
                    f"{indent}\t\tmoney = -{n}\n"
                    f"{goods_body}\n"
                    f"{indent}\t\tset_country_flag = CHI_crisis_paid\n"
                    f"{indent}\t\tclr_country_flag = CHI_pay_part"
                )
            else:
                extra = (
                    f"{mod_line}{indent}\t\towner = {{\n"
                    f"{indent}\t\t\t{cor}\n"
                    f"{indent}\t\t\tmoney = {n}\n"
                    f"{goods_lim}\n"
                    f"{indent}\t\t}}\n"
                    f"{indent}\t\towner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}\n"
                )
                body = (
                    f"{indent}\t\tmoney = -{n}\n"
                    f"{goods_body}\n"
                    f"{indent}\t\tset_country_flag = CHI_crisis_paid"
                )

            blocks.append(
                f"""{indent}random_owned = {{
{indent}\tlimit = {{
{indent}		has_building = province_selector
{extra}{indent}\t}}
{indent}\towner = {{
{body}
{indent}\t}}
{indent}}}"""
            )
        if len(chunks) > 1:
            blocks.append(
                f"""{indent}random_owned = {{
{indent}\tlimit = {{
{indent}		has_building = province_selector
{indent}\t\towner = {{ has_country_flag = CHI_pay_part }}
{indent}\t\towner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
{indent}\t}}
{indent}\towner = {{
{indent}\t\tmoney = {chunks[0]}
{indent}\t\tclr_country_flag = CHI_pay_part
{indent}\t}}
{indent}}}"""
            )
        return "\n".join(blocks)

    return one_pay(amount, False) + "\n" + one_pay(corrupt_amount, True)


def water_level_pay(level, costs):
    return pay_goods_flag(
        "CHI_do_water_pay",
        costs["money"],
        costs["corrupt"],
        costs,
        f"CHI_water_{level}",
        indent="\t\t\t",
    )


def unique_goods_pay():
    return pay_goods_flag(
        "CHI_do_uniq_pay",
        UNIQUE_REPAIR["money"],
        UNIQUE_REPAIR["corrupt"],
        UNIQUE_REPAIR,
        indent="\t\t\t",
    )


def canal_goods_pay():
    return pay_goods_flag(
        "CHI_do_canal_pay",
        CANAL_REPAIR["money"],
        CANAL_REPAIR["corrupt"],
        CANAL_REPAIR,
        indent="\t\t\t",
    )


def yangtze_goods_pay():
    return pay_goods_flag(
        "CHI_do_yangtze_pay",
        YANGTZE_REPAIR["money"],
        YANGTZE_REPAIR["corrupt"],
        YANGTZE_REPAIR,
        indent="\t\t\t",
    )


def yellow_goods_pay():
    return pay_goods_flag(
        "CHI_do_yellow_pay",
        YELLOW_REPAIR["money"],
        YELLOW_REPAIR["corrupt"],
        YELLOW_REPAIR,
        indent="\t\t\t",
    )

def water_choice(eid, desc_key, step_name, flag, pay_id):
    return f"""province_event = {{
\tid = {eid}
\ttitle = "CHI_water_choice_title"
\tdesc = "{desc_key}"
\tpicture = "Administration"
\tis_triggered_only = yes
\toption = {{
\t\tname = "{step_name}"
\t\ttrigger = {{
\t\t\tNOT = {{ has_province_modifier = CHI_hydro_cd }}
\t\t}}
{pay_click(flag, pay_id)}
\t}}
\toption = {{
\t\tname = "CHI_sel_back"
{reopen_food()}
\t}}
}}
"""

WATER_PAY_ID = {1: 144494, 2: 144497, 3: 144498, 4: 144499}


def _water_choice_menu(eid, level):
    opts = []
    if level:
        opts.append(
            f"""	option = {{
		name = "CHI_sel_water_{level}"
{pay_click("CHI_do_water_pay", WATER_PAY_ID[level])}
	}}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_back"
{reopen_food()}
	}}"""
        )
    joined = "\n".join(opts)
    return f"""province_event = {{
	id = {eid}
	title = "CHI_water_choice_title"
	desc = "CHI_water_choice_desc"
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def build_water_leaves():
    menus = [
        _water_choice_menu(144470, 1),
        _water_choice_menu(144471, 2),
        _water_choice_menu(144472, 3),
        _water_choice_menu(144473, 4),
    ]
    return "\n".join(
        [
            notice(144457, "CHI_sel_no_water", "CHI_sel_no_water_desc", "food"),
            notice(144458, "CHI_sel_hydro_wait", "CHI_sel_hydro_wait_desc", "food"),
        ]
        + menus
    )


def _river_menu(eid, canal, yangtze, yellow):
    back = reopen_food()
    opts = []
    if canal:
        opts.append(
            """	option = {
		name = "CHI_sel_canal_silt"
		province_event = { id = 144495 days = 0 }
	}"""
        )
    if yangtze:
        opts.append(
            """	option = {
		name = "CHI_sel_yangtze_nav"
		province_event = { id = 144531 days = 0 }
	}"""
        )
    if yellow:
        opts.append(
            """	option = {
		name = "CHI_sel_yellow_dikes"
		province_event = { id = 144532 days = 0 }
	}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_back"
{back}
	}}"""
    )
    joined = "\n".join(opts)
    return f"""province_event = {{
	id = {eid}
	title = "CHI_menu_river_title"
	desc = "CHI_menu_river_desc"
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def build_river_leaves():
    menus = [_river_menu(eid, c, y, ye) for eid, c, y, ye in mod.RIVER_COMBOS]
    return "\n".join(
        [notice(144536, "CHI_sel_river_wait", "CHI_sel_river_wait_desc", "food")] + menus
    )


def build_famine_leaves():
    food = reopen_food()
    granary_menu = f"""province_event = {{
	id = 144475
	title = "CHI_famine_choice_title"
	desc = "CHI_famine_choice_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_granary"
		trigger = {{
			OR = {{
				has_province_modifier = CHI_famine_1
				has_province_modifier = CHI_famine_2
				has_province_modifier = CHI_famine_3
				has_province_modifier = CHI_famine_4
			}}
			NOT = {{ has_province_modifier = CHI_food_cd }}
		}}
{granary_build_effect()}
	}}
	option = {{
		name = "CHI_sel_back"
{food}
	}}
}}
"""
    return "\n".join(
        [
            notice(144459, "CHI_sel_no_famine", "CHI_sel_no_famine_desc", "food"),
            notice(144460, "CHI_sel_has_granary", "CHI_sel_has_granary_desc", "food"),
            notice(144523, "CHI_sel_food_wait", "CHI_sel_food_wait_desc", "food"),
            granary_menu,
        ]
    )


def build_piracy_leaves():
    coast = reopen_coast()
    port_imm = """		owner = {
			clr_country_flag = CHI_port_step
			random_owned = {
				limit = {
					has_building = province_selector
					has_province_modifier = CHI_piracy_4
				}
				remove_province_modifier = CHI_piracy_4
				add_province_modifier = { name = CHI_piracy_3 duration = -1 }
				owner = { set_country_flag = CHI_port_step }
			}
			random_owned = {
				limit = {
					has_building = province_selector
					has_province_modifier = CHI_piracy_3
					owner = { NOT = { has_country_flag = CHI_port_step } }
				}
				remove_province_modifier = CHI_piracy_3
				add_province_modifier = { name = CHI_piracy_2 duration = -1 }
				owner = { set_country_flag = CHI_port_step }
			}
			random_owned = {
				limit = {
					has_building = province_selector
					has_province_modifier = CHI_piracy_2
					owner = { NOT = { has_country_flag = CHI_port_step } }
				}
				remove_province_modifier = CHI_piracy_2
				add_province_modifier = { name = CHI_piracy_1 duration = -1 }
			}
			any_owned = {
				limit = { has_building = province_selector }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}
			clr_country_flag = CHI_port_step
		}"""
    fleet_imm = """		owner = {
			any_owned = {
				limit = {
					OR = {
						has_province_modifier = CHI_piracy_1
						has_province_modifier = CHI_piracy_2
						has_province_modifier = CHI_piracy_3
						has_province_modifier = CHI_piracy_4
					}
				}
				remove_province_modifier = CHI_piracy_1
				remove_province_modifier = CHI_piracy_2
				remove_province_modifier = CHI_piracy_3
				remove_province_modifier = CHI_piracy_4
			}
		}"""
    def info_then_ok(eid, title, desc, effect="", back=None):
        # Effects on the option, never in immediate: Vic2 dumps add/remove
        # onto the parchment as white/yellow text if they sit in immediate.
        # Fleet wipe removes piracy, so coast matching would find nothing — hub.
        opt_fx = f"{effect}\n" if effect else ""
        back_fx = back if back is not None else coast
        return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "{desc}"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_ok"
{opt_fx}{back_fx}
	}}
}}
"""
    return "\n".join(
        [
            notice(144461, "CHI_sel_not_coast", "CHI_sel_not_coast_desc", "hub"),
            notice(144462, "CHI_sel_no_piracy", "CHI_sel_no_piracy_desc", "hub"),
            info_then_ok(144463, "CHI_need_port", "CHI_need_port_desc"),
            info_then_ok(144464, "CHI_need_fleet", "CHI_need_fleet_desc"),
            info_then_ok(144465, "CHI_sel_port_piracy", "CHI_sel_port_piracy_desc", port_imm),
            info_then_ok(
                144466, "CHI_sel_fleet_piracy", "CHI_sel_fleet_piracy_desc", fleet_imm, reopen_hub()
            ),
        ]
    )


def build_depot_leaf():
    misc = open_pe(MISC_MENU_ID)
    return f"""province_event = {{
	id = 144467
	title = "CHI_depot_title"
	desc = "CHI_depot_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "Selector_EvtOptSupplyDepot"
		trigger = {{
			owner = {{ money = 500000 }}
		}}
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
	option = {{
		name = "CHI_sel_back"
{misc}
	}}
}}
"""


def build_leaves():
    return "\n".join(
        [
            build_money_notices(),
            build_sep_leaves(),
            build_water_leaves(),
            build_famine_leaves(),
            build_piracy_leaves(),
            build_depot_leaf(),
        ]
    )


def build_menus():
    pays = build_pay_dispatcher()
    return (
        build_hubs()
        + "\n"
        + build_dispatcher()
        + "".join(pays[k] for k in ("sep", "granary"))
        + build_submenus()
        + "\n"
        + build_leaves()
        + "\n# CHI_MENUS_END\n"
    )


def build_infra_pulse(rids):
    """No nested any_owned inside a province limit — Vic2 CTDs on that."""
    fam_or = """					OR = {
						has_province_modifier = CHI_famine_1
						has_province_modifier = CHI_famine_2
						has_province_modifier = CHI_famine_3
						has_province_modifier = CHI_famine_4
					}"""
    no_rr = []
    marks = []
    regs = mod.regions_used()
    for rid in rids:
        idb = mod.ids_trigger(regs[rid], pad="\t\t\t\t\t")
        no_rr.append(
            f"""			any_owned = {{
				limit = {{
{idb}
					NOT = {{ has_building = railroad }}
				}}
				owner = {{ set_country_flag = CHI_no_rr_{rid} }}
			}}"""
        )
        marks.append(
            f"""			any_owned = {{
				limit = {{
{idb}
{fam_or}
					owner = {{
						NOT = {{ has_country_flag = CHI_infra_drop_{rid} }}
						NOT = {{ has_country_flag = CHI_no_rr_{rid} }}
					}}
				}}
				owner = {{
					set_country_flag = CHI_act_{rid}
					set_country_flag = CHI_infra_drop_{rid}
				}}
			}}"""
        )
    drop = mod.famine_drop_block(rids, indent="\t\t\t")
    orlim = mod.gen_region_or(rids)
    relief = f"""			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_famine_infra_relief duration = -1 }}
			}}"""
    clr = mod.gen_clr_act(rids)
    clr_no = "\n".join(f"			clr_country_flag = CHI_no_rr_{rid}" for rid in rids)
    joined_no = "\n".join(no_rr)
    joined = "\n".join(marks)
    return f"""
# CHI_INFRA_PULSE_START
country_event = {{
	id = 144436
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {{
		name = "noloc"
		CHI = {{
{joined_no}
{joined}
{drop}
{relief}
{clr}
{clr_no}
		}}
	}}
}}
# CHI_INFRA_PULSE_END
"""


def build_revolt_pulse(rids):
    """After CHI_sep_uprising expires, if CHI still controls the provoked province,
    drop separatism one level for that region. Fired from JAN 140400, not MTTH.
    Follow-up notice is fired from option, never from immediate."""
    marks = []
    regs = mod.regions_used()
    for rid in rids:
        idb = mod.ids_trigger(regs[rid], pad="\t\t\t\t\t")
        marks.append(
            f"""			any_owned = {{
				limit = {{
					has_province_modifier = CHI_sep_revolt_pending
{idb}
					NOT = {{ has_province_modifier = CHI_sep_uprising }}
					controlled_by = THIS
					owner = {{ has_country_flag = CHI_sep_revolt_active }}
				}}
				owner = {{ set_country_flag = CHI_act_{rid} }}
				remove_province_modifier = CHI_sep_revolt_pending
				add_province_modifier = {{ name = CHI_sep_revolt_won duration = 30 }}
			}}"""
        )
    sep_drop = mod.water_drop_block(rids, indent="\t\t\t").replace("CHI_water_", "CHI_separatism_")
    clr = mod.gen_clr_act(rids)
    joined = "\n".join(marks)
    notice = """			any_owned = {
				limit = { has_province_modifier = CHI_sep_revolt_won }
				province_event = { id = 144491 days = 1 }
				remove_province_modifier = CHI_sep_revolt_won
			}"""
    return f"""
# CHI_REVOLT_PULSE_START
country_event = {{
	id = 144492
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {{
		name = "noloc"
		CHI = {{
{joined}
{sep_drop}
{notice}
{clr}
		}}
	}}
}}
# CHI_REVOLT_PULSE_END
"""




def build_region_flag_event():
    """Startup pulse: pirate port downgrade once, and clear leftover revolt
    markers from old saves. Regions are identified by province_id, not flags."""
    pirate_drop = """			any_owned = {
				limit = {
					has_building = naval_base
					has_province_modifier = CHI_piracy_4
					owner = { NOT = { has_country_flag = CHI_crisis_setup_done } }
				}
				remove_province_modifier = CHI_piracy_4
				add_province_modifier = { name = CHI_piracy_3 duration = -1 }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}
			any_owned = {
				limit = {
					has_building = naval_base
					has_province_modifier = CHI_piracy_3
					NOT = { has_province_modifier = CHI_port_anti_piracy }
					owner = { NOT = { has_country_flag = CHI_crisis_setup_done } }
				}
				remove_province_modifier = CHI_piracy_3
				add_province_modifier = { name = CHI_piracy_2 duration = -1 }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}
			any_owned = {
				limit = {
					has_building = naval_base
					has_province_modifier = CHI_piracy_2
					NOT = { has_province_modifier = CHI_port_anti_piracy }
					owner = { NOT = { has_country_flag = CHI_crisis_setup_done } }
				}
				remove_province_modifier = CHI_piracy_2
				add_province_modifier = { name = CHI_piracy_1 duration = -1 }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}"""
    revolt_clr = """			random_owned = {
				limit = {
					is_capital = yes
					owner = { NOT = { has_country_flag = CHI_crisis_setup_done } }
				}
				owner = {
					any_owned = {
						remove_province_modifier = CHI_sep_revolt_pending
						remove_province_modifier = CHI_sep_revolt_won
					}
					set_country_flag = CHI_crisis_setup_done
				}
			}"""
    return f"""
# CHI_REGION_FLAGS_START
country_event = {{
	id = 144405
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {{
		name = "noloc"
		CHI = {{
			remove_country_modifier = CHI_inefficient_bureaucracy
{pirate_drop}
{revolt_clr}
		}}
	}}
}}
# CHI_REGION_FLAGS_END
"""


def _tab_shift(block, n):
    pad = "\t" * n
    return "\n".join((pad + line if line else line) for line in block.split("\n"))


def dec_hub_route(extra, eid):
    extra_txt = ("\n" + _tab_shift(extra, 3)) if extra.strip() else ""
    return f"""					random_owned = {{
						limit = {{
							has_building = province_selector
							owner = {{ NOT = {{ has_country_flag = CHI_routed }} }}{extra_txt}
						}}
						owner = {{ set_country_flag = CHI_routed }}
						province_event = {{
							id = {eid}
							days = 0
						}}
					}}"""


def build_selector_decision():
    """Pick 144408-144415 from the selector province modifiers (no option triggers)."""
    text = """political_decisions = {
	select_prov = {
		picture = build_kiel_canal
			potential = {
				tag = JAN
				META_1 = {
					owner = {
						ai = no
						NOT = { tag = CHI }
						any_owned_province = { has_building = province_selector }
					}
				}
			}
			allow = {
				tag = JAN
			}
			effect = {
				any_country = {
					limit = {
						ai = no
						any_owned_province = { has_building = province_selector }
					}
					random_owned = {
						limit = {
							has_building = province_selector
						}
						province_event = {
							id = 144407
							days = 0
						}
					}
				}
			}
			
			ai_will_do = { factor = 1 }
		}
		
	select_prov_CHI = {
		picture = build_kiel_canal
			potential = {
				tag = JAN
				META_1 = {
					owner = {
						ai = no
						any_owned_province = { has_building = province_selector }
					}
				}
			}
			allow = {
				tag = JAN
			}
			effect = {
				any_country = {
					limit = {
						ai = no
						tag = CHI
						any_owned_province = { has_building = province_selector }
					}
					clr_country_flag = CHI_mode_hub
					clr_country_flag = CHI_mode_food
					clr_country_flag = CHI_mode_sep
					clr_country_flag = CHI_mode_water
					clr_country_flag = CHI_mode_granary
					clr_country_flag = CHI_mode_port
					clr_country_flag = CHI_mode_fleet
					clr_country_flag = CHI_mode_depot
					clr_country_flag = CHI_routed
					clr_country_flag = CHI_pay_fired
					clr_country_flag = CHI_crisis_paid
					set_country_flag = CHI_mode_hub
HUB_FIRE_PLACEHOLDER
				}
			}
			
			ai_will_do = { factor = 1 }
		}
}
"""
    return text.replace("HUB_FIRE_PLACEHOLDER", mod.matching_hub_randoms("\t\t\t\t\t"))


def write_selector():
    path = ROOT / "decisions" / "Selector.txt"
    text = build_selector_decision()
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("Selector.txt", path.stat().st_size)


def build_click_event():
    """Old saves may still fire 144406. Keep it silent so it is not the Shmel window."""
    return """
# CHI_CLICK_EVENT_START
country_event = {
	id = 144406
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {
		name = "noloc"
	}
}
# CHI_CLICK_EVENT_END
"""


def patch_jan():
    path = ROOT / "events" / "JAN.txt"
    raw = path.read_bytes().decode("utf-8").replace("\r\n", "\n")
    changed = False
    if "id = 144408" in raw:
        a, b = extract_event(raw, 144408)
        raw = raw[:a] + raw[b:]
        changed = True
        print("removed hub 144408 from JAN", b - a)
    pulse_line = "		country_event = { id = 144436 days = 1 }"
    old_pulse = (
        "		country_event = { id = 144436 days = 1 }\n"
        "		country_event = { id = 144492 days = 1 }\n"
        "		country_event = { id = 144405 days = 1 }"
    )
    new_pulse = (
        "		country_event = { id = 144405 days = 1 }\n"
        "		country_event = { id = 144436 days = 1 }\n"
        "		country_event = { id = 144492 days = 3 }"
    )
    if old_pulse in raw:
        raw = raw.replace(old_pulse, new_pulse, 1)
        changed = True
        print("JAN pulse order: flags first, revolt later")
    elif new_pulse not in raw:
        needle = "		country_event = { id = 140413 days = 1 }"
        if needle not in raw:
            raise SystemExit("JAN 140413 call not found")
        raw = raw.replace(needle, needle + "\n" + new_pulse, 1)
        changed = True
        print("JAN 140400 now pulses CHI infra/revolt/flags")
    depot = """province_event = {
	title = "Selector_EvtName"
	desc = "Selector_EvtDesc"
	id = 144407
	picture = "Administration"
	is_triggered_only = yes
	option = {
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}
	option = {
		name = "Selector_EvtOptSupplyDepot"
		trigger = {
			owner = { money = 500000 }
		}
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
		name = "CHI_need_500k"
		trigger = {
			owner = { NOT = { money = 500000 } }
		}
		province_selector = -1
	}
}"""
    if "id = 144407" in raw:
        a, b = extract_event(raw, 144407)
        if "owner = { money = 500000 }" not in raw[a:b]:
            raw = raw[:a] + depot + raw[b:]
            changed = True
            print("JAN 144407 depot now checks treasury")
    old_99851 = """country_event = {
	id = 99851
	is_triggered_only = yes
	
	option = {
		any_country = {
			social_reform = no_subsidies
			social_reform = no_pensions
			social_reform = no_medical_reforms
		}
	}
}"""
    new_99851 = """country_event = {
	id = 99851
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	option = {
		name = "noloc"
		any_country = {
			social_reform = no_subsidies
			social_reform = no_pensions
			social_reform = no_medical_reforms
		}
	}
}"""
    if old_99851 in raw:
        raw = raw.replace(old_99851, new_99851, 1)
        changed = True
        print("JAN 99851 got title/desc/name")
    if changed:
        path.write_bytes(raw.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    else:
        print("JAN.txt already patched")


def mark_region(rids, flag):
    return mod.gen_set_act(rids)


def build_tax_event(rids):
    mark = mark_region(rids, "CHI_do_tax_cut")
    orlim = mod.gen_region_or(rids)
    stacks = "\n".join(
        f"""			random_owned = {{
				limit = {{
					has_building = province_selector
					owner = {{ NOT = {{ has_country_flag = CHI_tax_stacked }} }}
					owner = {{ NOT = {{ has_country_modifier = CHI_sep_tax_stack_{i} }} }}
				}}
				owner = {{
					add_country_modifier = {{ name = CHI_sep_tax_stack_{i} duration = {TAX_DAYS} }}
					set_country_flag = CHI_tax_stacked
				}}
			}}"""
        for i in range(1, TAX_STACKS + 1)
    )
    clr = mod.gen_clr_act(rids)
    return f"""
province_event = {{
	id = 144512
	title = "CHI_sel_tax_done"
	desc = "CHI_sel_tax_done_desc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		owner = {{
			clr_country_flag = CHI_tax_stacked
{mark}
			any_owned = {{
				limit = {{
					OR = {{
{orlim}
					}}
				}}
				add_province_modifier = {{ name = CHI_sep_tax_cut duration = {TAX_DAYS} }}
			}}
{stacks}
{clr}
		}}
	}}
	option = {{
		name = "CHI_sel_ok"
		owner = {{
			random_owned = {{
				limit = {{ has_building = province_selector }}
				province_event = {{ id = 144513 days = 1 }}
			}}
			clr_country_flag = CHI_tax_stacked
		}}
	}}
}}
"""


def dump_event_file(path, header, chunks):
    body = header + "\n" + "\n".join(c for c in chunks if c)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print(path.name, path.stat().st_size)
    return path


LEGACY_EVENT_FILES = [
    "CHI_selector.txt",
    "CHI_separatism.txt",
    "CHI_water.txt",
    "CHI_famine.txt",
    "CHI_piracy.txt",
    "CHI_crises.txt",
]


def write_crises():
    """Vic2 loads ONLY files directly in events/ — subfolders are ignored."""
    rids = mod.rids_used()
    workers = mod.build_workers(rids)
    pays = build_pay_dispatcher()
    out_dir = ROOT / "events"
    # Remove old monolithic + wrongly nested copies
    for name in LEGACY_EVENT_FILES:
        legacy = out_dir / name
        if legacy.is_file():
            legacy.unlink()
            print("removed legacy", name)
    nested = out_dir / "chi_crisis"
    if nested.is_dir():
        for p in nested.glob("*.txt"):
            p.unlink()
            print("removed nested", p.name)
        try:
            nested.rmdir()
            print("removed empty events/chi_crisis/")
        except OSError:
            pass
    # Flat small files in events/ root (Vic2-readable, still browsable)
    files = {
        "CHI_crisis_01_hub.txt": (
            "# Selector hub events (144408-144415)\n",
            [build_hubs()],
        ),
        "CHI_crisis_03_submenus.txt": (
            "# Food / coast / misc submenus\n",
            [build_food_submenu(), build_coast_submenu(), build_misc_submenu()],
        ),
        "CHI_crisis_04_notices.txt": (
            "# Money / goods notices + depot\n",
            [build_money_notices(), build_depot_leaf()],
        ),
        "CHI_crisis_05_setup.txt": (
            "# Region flags + click marker\n",
            [build_region_flag_event(), build_click_event()],
        ),
        "CHI_crisis_10_sep_pay.txt": (
            "# Separatism bribe pay stage\n",
            [pays["sep"]],
        ),
        "CHI_crisis_11_sep_worker.txt": (
            "# Separatism worker + tax stacks\n",
            [workers["sep"], build_tax_event(rids)],
        ),
        "CHI_crisis_12_sep_menus.txt": (
            "# Separatism menus (4 levels, option triggers)\n",
            [build_sep_leaves()],
        ),
        "CHI_crisis_13_sep_pulse.txt": (
            "# Revolt win pulse\n",
            [build_revolt_pulse(rids)],
        ),
        "CHI_crisis_20_water_pay.txt": (
            "# Water + river project pay stages\n",
            [
                pays["water_1"],
                pays["water_2"],
                pays["water_3"],
                pays["water_4"],
                pays["canal"],
                pays["yangtze"],
                pays["yellow"],
            ],
        ),
        "CHI_crisis_21_water_worker.txt": (
            "# Water + river workers\n",
            [workers["water"], workers["unique"], workers["yangtze"], workers["yellow"]],
        ),
        "CHI_crisis_22_water_menus.txt": (
            "# Water choice menus\n",
            [build_water_leaves()],
        ),
        "CHI_crisis_23_river_menus.txt": (
            "# Canal / Yangtze / Yellow dike projects\n",
            [build_river_leaves()],
        ),
        "CHI_crisis_30_famine_pay.txt": (
            "# Granary pay stage\n",
            [pays["granary"]],
        ),
        "CHI_crisis_31_famine_worker.txt": (
            "# Granary worker\n",
            [workers["granary"]],
        ),
        "CHI_crisis_32_famine_menus.txt": (
            "# Famine / granary menus\n",
            [build_famine_leaves()],
        ),
        "CHI_crisis_33_famine_pulse.txt": (
            "# Infra famine relief pulse\n",
            [build_infra_pulse(rids)],
        ),
        "CHI_crisis_40_piracy_menus.txt": (
            "# Coast piracy menus\n",
            [build_piracy_leaves()],
        ),
    }
    written = []
    for name, (header, chunks) in files.items():
        written.append(dump_event_file(out_dir / name, header, chunks))
    return written


NEW_MODS = """
CHI_sep_tax_cut = {
	icon = 9
}
CHI_sep_revolt_cd = {
	icon = 16
}
CHI_sep_uprising = {
	pop_militancy_modifier = 0.20
	icon = 16
}
CHI_food_cd = {
	icon = 7
}
"""


def patch_modifiers():
    path = ROOT / "common" / "event_modifiers.txt"
    text = path.read_bytes().decode("utf-8")
    changed = False
    m = re.search(r"CHI_sep_tax_cut = \{[^}]*\}", text)
    if m and "tax_efficiency" in m.group(0):
        text = text[: m.start()] + "CHI_sep_tax_cut = {\n\ticon = 9\n}" + text[m.end() :]
        changed = True
        print("CHI_sep_tax_cut is province marker only")
    extra_bits = []
    if "CHI_canal_cd =" not in text:
        extra_bits.append(
            "CHI_canal_cd = {\n\ticon = 8\n}\n"
            "CHI_yangtze_cd = {\n\ticon = 8\n}\n"
            "CHI_yellow_cd = {\n\ticon = 8\n}\n"
            "CHI_yellow_new_course = {\n\tfarm_RGO_eff = 0.03\n\timmigrant_attract = 0.05\n\ticon = 11\n}"
        )
    if "CHI_sep_revolt_cd =" not in text:
        extra_bits.append(NEW_MODS.strip())
    if "CHI_sep_tax_stack_1 =" not in text:
        extra_bits.append(
            "\n".join(
                f"CHI_sep_tax_stack_{i} = {{\n\ttax_efficiency = -0.04\n\ticon = 9\n}}"
                for i in range(1, TAX_STACKS + 1)
            )
        )
    if "CHI_click_mark =" not in text:
        extra_bits.append(
            "CHI_click_mark = {\n\ticon = 9\n}\n"
            "CHI_lvl_dropped = {\n\ticon = 9\n}\n"
            "CHI_sep_revolt_pending = {\n\ticon = 16\n}\n"
            "CHI_sep_revolt_won = {\n\ticon = 16\n}"
        )
    if extra_bits:
        end = "# CHI_CRISIS_WRAPPER1_END"
        if end not in text:
            raise SystemExit("wrapper end not found")
        text = text.replace(end, "\n".join(extra_bits) + "\n" + end, 1)
        changed = True
        print("crisis extra modifiers added")
    if changed:
        path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    else:
        print("event_modifiers ok")


def patch_triggered():
    mod.patch_triggered()


def patch_loc():
    keys = {
        "CHI_Selector_EvtDesc",
        "CHI_Selector_EvtDesc_none",
        "CHI_Selector_EvtName",
        "Selector_EvtName",
        "Selector_EvtDesc",
        "CHI_menu_sep",
        "CHI_menu_food",
        "CHI_menu_coast",
        "CHI_menu_misc",
        "CHI_menu_misc_title",
        "CHI_menu_misc_desc",
        "CHI_sel_depot",
        "CHI_menu_hydro",
        "CHI_menu_sep_title",
        "CHI_menu_sep_desc",
        "CHI_menu_food_title",
        "CHI_menu_food_desc",
        "CHI_menu_coast_title",
        "CHI_menu_coast_desc",
        "CHI_sel_back",
        "CHI_sel_sep_1",
        "CHI_sel_sep_2",
        "CHI_sel_sep_3",
        "CHI_sel_sep_4",
        "CHI_sel_sep_done",
        "CHI_sel_sep_done_desc",
        "CHI_need_200k",
        "CHI_need_500k",
        "CHI_need_1m",
        "CHI_need_15m",
        "CHI_need_2m",
        "CHI_need_2m_water",
        "CHI_need_2m_granary",
        "CHI_need_money_desc",
        "CHI_need_goods",
        "CHI_need_goods_desc",
        "CHI_sel_not_coast_desc",
        "CHI_sel_no_piracy_desc",
        "CHI_need_port",
        "CHI_need_fleet",
        "CHI_need_port_desc",
        "CHI_need_fleet_desc",
        "CHI_sel_port_piracy_desc",
        "CHI_sel_fleet_piracy_desc",
        "CHI_depot_title",
        "CHI_depot_desc",
        "CHI_sel_sep",
        "CHI_sel_sep_none",
        "CHI_sel_sep_wait",
        "CHI_sel_not_coast",
        "CHI_sel_no_water",
        "CHI_sel_no_famine",
        "CHI_sel_no_piracy",
        "CHI_sel_has_granary",
        "CHI_sel_hydro_wait",
        "CHI_sel_water",
        "CHI_sel_water_1",
        "CHI_sel_water_2",
        "CHI_sel_water_3",
        "CHI_sel_water_4",
        "CHI_sel_granary",
        "CHI_menu_granary",
        "CHI_sel_unique_water",
        "CHI_sel_infra",
        "CHI_sel_infra_done",
        "CHI_sel_infra_done_desc",
        "CHI_sel_port_piracy",
        "CHI_sel_fleet_piracy",
        "CHI_sel_water_done",
        "CHI_sel_water_done_desc",
        "CHI_sel_granary_done",
        "CHI_sel_granary_done_desc",
        "CHI_sel_unique_done",
        "CHI_sel_unique_done_desc",
        "CHI_sep_cd",
        "CHI_sep_cd_desc",
        "CHI_sel_ok",
        "noloc",
        "CHI_famine_1_desc",
        "CHI_famine_2_desc",
        "CHI_famine_3_desc",
        "CHI_famine_4_desc",
        "CHI_famine_infra_relief_desc",
        "CHI_sel_tax_cut",
        "CHI_sel_tax_cut_desc",
        "CHI_sel_revolt",
        "CHI_sel_revolt_desc",
            "CHI_sel_revolt_wait",
            "CHI_sel_revolt_wait_desc",
            "CHI_sel_revolt_won",
            "CHI_sel_revolt_won_desc",
        "CHI_sep_tax_cut",
        "CHI_sep_tax_cut_desc",
        "CHI_sep_revolt_cd",
        "CHI_sep_revolt_cd_desc",
        "CHI_sep_uprising",
        "CHI_sep_uprising_desc",
        "CHI_provoked_rebels",
        "CHI_sep_tax_cut_nation",
        "CHI_sep_tax_cut_nation_desc",
    }
    keys.update(
        {
            "CHI_sep_menu_title",
            "CHI_sel_bribe",
            "CHI_sel_bribe_desc",
            "CHI_pay_processing",
            "CHI_pay_processing_desc",
            "CHI_pay_granary",
            "CHI_pay_granary_desc",
            "CHI_pay_bribe",
            "CHI_pay_bribe_desc",
            "CHI_pay_unique",
            "CHI_pay_unique_desc",
            "CHI_pay_canal",
            "CHI_pay_canal_desc",
            "CHI_pay_yangtze",
            "CHI_pay_yangtze_desc",
            "CHI_pay_yellow",
            "CHI_pay_yellow_desc",
            "CHI_menu_river",
            "CHI_menu_river_title",
            "CHI_menu_river_desc",
            "CHI_sel_canal_silt",
            "CHI_sel_yangtze_nav",
            "CHI_sel_yellow_dikes",
            "CHI_sel_canal_done",
            "CHI_sel_canal_done_desc",
            "CHI_sel_yangtze_done",
            "CHI_sel_yangtze_done_desc",
            "CHI_sel_yellow_done",
            "CHI_sel_yellow_done_desc",
            "CHI_sel_river_wait",
            "CHI_sel_river_wait_desc",
            "CHI_canal_cd",
            "CHI_canal_cd_desc",
            "CHI_yangtze_cd",
            "CHI_yangtze_cd_desc",
            "CHI_yellow_cd",
            "CHI_yellow_cd_desc",
            "CHI_yellow_new_course",
            "CHI_yellow_new_course_desc",
            "CHI_yellow_river_works",
            "CHI_yellow_river_works_desc",
            "CHI_yellow_course_title",
            "CHI_yellow_course_desc",
            "CHI_yellow_course_north",
            "CHI_yellow_course_dikes",
            "CHI_pay_water_1",
            "CHI_pay_water_1_desc",
            "CHI_pay_water_2",
            "CHI_pay_water_2_desc",
            "CHI_pay_water_3",
            "CHI_pay_water_3_desc",
            "CHI_pay_water_4",
            "CHI_pay_water_4_desc",
            "CHI_menu_sep_desc",
            "CHI_sel_sep_none_desc",
            "CHI_sel_sep_wait_desc",
            "CHI_sel_tax_done",
            "CHI_sel_tax_done_desc",
            "CHI_water_choice_title",
            "CHI_water_choice_desc",
            "CHI_water_choice_1_desc",
            "CHI_water_choice_2_desc",
            "CHI_water_choice_3_desc",
            "CHI_water_choice_4_desc",
            "CHI_water_choice_unique_desc",
            "CHI_sel_water_full",
            "CHI_water_full_title",
            "CHI_water_full_desc",
            "CHI_sel_water_full_go",
            "CHI_sel_water_full_done",
            "CHI_sel_water_full_done_desc",
            "CHI_sel_no_water_desc",
            "CHI_sel_hydro_wait_desc",
            "CHI_famine_choice_title",
            "CHI_famine_choice_desc",
            "CHI_sel_has_granary_desc",
            "CHI_sel_food_wait",
            "CHI_sel_food_wait_desc",
            "CHI_sel_no_famine_desc",
            "CHI_food_cd",
            "CHI_food_cd_desc",
            "CHI_hydro_cd",
            "CHI_hydro_cd_desc",
            "CHI_great_granary",
            "CHI_great_granary_desc",
            "CHI_famine_tied_to_water",
            "CHI_famine_tied_to_water_desc",
            "CHI_water_canal_silt",
            "CHI_water_canal_silt_desc",
            "CHI_water_yangtze_nav",
            "CHI_water_yangtze_nav_desc",
            "CHI_water_yellow_dikes",
            "CHI_water_yellow_dikes_desc",
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
            "CHI_port_anti_piracy",
            "CHI_port_anti_piracy_desc",
            "CHI_famine_infra_relief",
            "CHI_famine_infra_relief_desc",
            "CHI_sel_sep_full",
            "CHI_sep_full_title",
            "CHI_sep_full_desc",
            "CHI_sel_sep_full_go",
            "CHI_sel_sep_full_done",
            "CHI_sel_sep_full_done_desc",
            "CHI_sel_famine_full",
            "CHI_famine_full_title",
            "CHI_famine_full_desc",
            "CHI_sel_famine_full_go",
            "CHI_sel_famine_full_done",
            "CHI_sel_famine_full_done_desc",
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
            "CHI_provoked_rebels_title",
            "CHI_provoked_rebels_name",
            "CHI_provoked_rebels_desc",
            "CHI_provoked_rebels_army",
        }
    )
    keys.update(mod.LOC_KEYS)
    for i in range(1, TAX_STACKS + 1):
        keys.update({f"CHI_sep_tax_stack_{i}", f"CHI_sep_tax_stack_{i}_desc"})
    for i in range(1, 5):
        keys.update(
            {
                f"CHI_separatism_{i}",
                f"CHI_separatism_{i}_desc",
                f"CHI_water_{i}",
                f"CHI_water_{i}_desc",
                f"CHI_piracy_{i}",
                f"CHI_piracy_{i}_desc",
                f"CHI_famine_{i}",
            }
        )
    path = ROOT / "localisation" / "a.csv"
    t = path.read_bytes().decode("cp1251")
    kept = []
    for line in t.splitlines(True):
        key = line.split(";", 1)[0] if line.strip() else ""
        if key in keys:
            continue
        kept.append(line)
    add = [
        loc_line("CHI_Selector_EvtName", "Управление провинцией"),
        loc_line(
            "CHI_Selector_EvtDesc",
            "Только бедствия этой провинции. Сепаратизм, вода и голод — на весь регион. Порт — только сюда. При высокой коррупции деньги вдвое.",
        ),
        loc_line(
            "CHI_Selector_EvtDesc_none",
            "В этой провинции нет сепаратизма, проблем с водой, голода и пиратства. Можно поставить склад или закрыть окно.",
        ),
        loc_line("Selector_EvtName", "Селектор провинции"),
        loc_line(
            "Selector_EvtDesc",
            "Склад снабжения стоит 500 000 и ставится только в этой провинции. Старый склад в других провинциях этой страны снимается. Без 500 000 в казне сложить склад нельзя: игра уйдёт в минус, если списать вслепую.",
        ),
        loc_line("CHI_menu_sep", "Борьба с сепаратизмом"),
        loc_line("CHI_menu_food", "Голод и вода"),
        loc_line("CHI_menu_coast", "Побережье и пиратство"),
        loc_line("CHI_menu_misc", "Прочее"),
        loc_line("CHI_menu_misc_title", "Прочее"),
        loc_line(
            "CHI_menu_misc_desc",
            "Склад снабжения стоит 500 000 и ставится только в этой провинции. Старый склад в других провинциях снимается. Если в казне меньше 500 000, кнопки склада не будет.",
        ),
        loc_line("CHI_sel_depot", "Провинциальный склад"),
        loc_line("CHI_menu_hydro", "Ирригация"),
        loc_line("CHI_menu_river", "Речные проекты"),
        loc_line("CHI_menu_river_title", "Речные проекты региона"),
        loc_line(
            "CHI_menu_river_desc",
            "Кнопки только для проблем этой провинции. Очистка канала от ила, расчистка фарватера Янцзы и ремонт дамб Хуанхэ снимают свой модификатор во всём регионе. Перекопать русло Хуанхэ по всей империи нельзя отсюда — это решение двора.",
        ),
        loc_line("CHI_menu_sep_title", "Борьба с сепаратизмом"),
        loc_line(
            "CHI_menu_sep_desc",
            "Подкуп: 500 000 (при коррупции 1 000 000), сепаратизм региона -1, повтор год. Налог: маркер на регион на 2 года, казна -4% за каждый такой регион. Провокация: только эта провинция, через полгода при контроле Китая сепаратизм региона -1.",
        ),
        loc_line("CHI_menu_food_title", "Голод и вода"),
        loc_line(
            "CHI_menu_food_desc",
            "Ирригация: -1 уровень воды в регионе, повтор около 2.5 лет. Амбар: дерево 250, цемент 150, железо 100, пиломатериалы 80. Речные проекты отдельно: очистка канала от ила, фарватер Янцзы, ремонт дамб Хуанхэ. Перенос русла Хуанхэ — решение во вкладке политики.",
        ),
        loc_line("CHI_menu_coast_title", "Побережье и пиратство"),
        loc_line(
            "CHI_menu_coast_desc",
            "Кнопки ниже только по факту этой провинции. Порт: нужна уже построенная военно-морская база именно здесь (окно не умеет показать число баз — есть или нет). Флот: не меньше 200 кораблей у страны (текущее число кораблей окно тоже не показывает). Пиратство 1 портом не снимается.",
        ),
        loc_line("CHI_sel_back", "Назад"),
        loc_line("CHI_sel_sep_1", "Подавить сепаратизм I"),
        loc_line("CHI_sel_sep_2", "Подавить сепаратизм II"),
        loc_line("CHI_sel_sep_3", "Подавить сепаратизм III"),
        loc_line("CHI_sel_sep_4", "Подавить сепаратизм IV"),
        loc_line("CHI_sel_sep_done", "Сепаратизм"),
        loc_line("CHI_sel_sep_done_desc", "Подкуп прошёл. Сепаратизм региона снижен на 1 уровень. Повтор в этом регионе через год."),
        loc_line("CHI_need_200k", "200000"),
        loc_line("CHI_need_500k", "500000"),
        loc_line("CHI_need_1m", "1000000"),
        loc_line("CHI_need_15m", "1500000"),
        loc_line("CHI_need_2m", "2000000"),
        loc_line("CHI_need_money_desc", "В казне нет нужной суммы. При высокой коррупции денежная цена удваивается. Суммы больше 2 000 000 игра принимает только кусками по 2 000 000."),
        loc_line("CHI_need_goods", "Не хватает ресурсов"),
        loc_line(
            "CHI_need_goods_desc",
            "На складе не хватает дерева, цемента, железа или пиломатериалов. Для амбара: 250 / 150 / 100 / 80. Для ирригации объёмы больше и зависят от уровня — они указаны в описании заказа.",
        ),
        loc_line("CHI_need_port", "Нет военно-морской базы в этой провинции"),
        loc_line(
            "CHI_need_port_desc",
            "В этой провинции нет военно-морской базы. Постройте базу здесь, затем снова откройте селектор: порт снижает пиратство 2-4 на 1 уровень только в провинции с базой. Число баз окно показать не может.",
        ),
        loc_line("CHI_need_fleet", "Флота меньше 200 кораблей"),
        loc_line(
            "CHI_need_fleet_desc",
            "Нужно не меньше 200 кораблей у страны. Тогда флот снимет пиратство со всех провинций. Текущее число кораблей это окно показать не может — смотрите флот в интерфейсе страны.",
        ),
        loc_line(
            "CHI_sel_port_piracy_desc",
            "В этой провинции уже есть военно-морская база. Нажмите Понятно: пиратство здесь снизится на 1 уровень, появится портовый надзор. Другие провинции не затронет.",
        ),
        loc_line(
            "CHI_sel_fleet_piracy_desc",
            "В строю не меньше 200 кораблей. Нажмите Понятно: пиратство снимется со всех провинций страны. Откатить нельзя. Точное число кораблей окно показать не может.",
        ),
        loc_line("CHI_sel_not_coast_desc", "Эта провинция не стоит на море, пиратство здесь не лечится портом."),
        loc_line("CHI_sel_no_piracy_desc", "В этой провинции нет пиратства."),
        loc_line("CHI_depot_title", "Обработка приказа: склад 500 000"),
        loc_line("CHI_depot_desc", "Склад снабжения стоит 500 000 и ставится только в этой провинции. Старый склад в других провинциях снимается."),
        loc_line("CHI_sel_sep_none", "В этой провинции нет сепаратизма"),
        loc_line("CHI_sel_sep_wait", "Подавление уже идёт (повтор через год)"),
        loc_line("CHI_sel_not_coast", "Эта провинция не приморская"),
        loc_line("CHI_sel_no_water", "В этой провинции нет проблем с водой"),
        loc_line("CHI_sel_no_famine", "В этой провинции нет голода"),
        loc_line("CHI_sel_no_piracy", "В этой провинции нет пиратства"),
        loc_line("CHI_sel_has_granary", "Великий амбар уже построен"),
        loc_line("CHI_sel_hydro_wait", "Ремонт ирригации уже идёт (повтор ~2.5 года)"),
        loc_line("CHI_sel_granary", "Великий амбар"),
        loc_line("CHI_menu_granary", "Великий амбар"),
        loc_line("CHI_sel_port_piracy", "База есть: снизить пиратство на 1"),
        loc_line("CHI_sel_fleet_piracy", "Флот 200+: снять пиратство в стране"),
        loc_line("CHI_sel_water_1", "Ремонт ирригации I"),
        loc_line("CHI_sel_water_2", "Ремонт ирригации II"),
        loc_line("CHI_sel_water_3", "Ремонт ирригации III"),
        loc_line("CHI_sel_water_4", "Ремонт ирригации IV"),
        loc_line("CHI_sel_unique_water", "Речные проекты"),
        loc_line("CHI_sel_canal_silt", "Очистка канала от ила"),
        loc_line("CHI_sel_yangtze_nav", "Расчистка фарватера Янцзы"),
        loc_line("CHI_sel_yellow_dikes", "Ремонт дамб Хуанхэ"),
        loc_line("CHI_sel_water_done", "Ирригация"),
        loc_line(
            "CHI_sel_water_done_desc",
            "Работы в регионе закончены. Уровень проблемы с водой снижен на 1. В этом регионе следующий ремонт примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_granary_done", "Великий амбар"),
        loc_line(
            "CHI_sel_granary_done_desc",
            "Амбар заложен по всему региону из казённых запасов. Голод снижен на 1 уровень. Повтор продовольственной программы в этом регионе через 2 года.",
        ),
        loc_line("CHI_sel_unique_done", "Речные работы"),
        loc_line("CHI_sel_unique_done_desc", "Речной проект региона выполнен."),
        loc_line("CHI_sel_canal_done", "Канал расчищен"),
        loc_line(
            "CHI_sel_canal_done_desc",
            "Ил снят с Великого канала в этом регионе. Повтор очистки здесь примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_yangtze_done", "Фарватер Янцзы"),
        loc_line(
            "CHI_sel_yangtze_done_desc",
            "Судоходство Янцзы в этом регионе восстановлено. Повтор расчистки здесь примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_yellow_done", "Дамбы Хуанхэ"),
        loc_line(
            "CHI_sel_yellow_done_desc",
            "Дамбы Хуанхэ в этом регионе укреплены. Повтор ремонта здесь примерно через 2.5 года. Перенос русла по всей стране — решение двора.",
        ),
        loc_line("CHI_sel_river_wait", "Речной проект уже идёт"),
        loc_line(
            "CHI_sel_river_wait_desc",
            "Этот речной проект в регионе уже заказан. Повтор примерно через 2.5 года.",
        ),
        loc_line("CHI_sep_cd", "Подавление сепаратизма"),
        loc_line("CHI_sep_cd_desc", "В регионе уже идёт кампания. Следующий заказ через год."),
        loc_line("CHI_sel_ok", "Понятно"),
        loc_line("noloc", " "),
        loc_line("CHI_pay_processing", "Обработка приказа"),
        loc_line(
            "CHI_pay_processing_desc",
            "Казна и склады проверяют приказ. Если денег или товаров не хватает, списывать не будут.",
        ),
        loc_line("CHI_pay_granary", "Обработка приказа: дерево 250, цемент 150, железо 100, пиломатериалы 80"),
        loc_line(
            "CHI_pay_granary_desc",
            "Стоимость великого амбара: дерево 250, цемент 150, железо 100, пиломатериалы 80. Если товаров не хватает, списывать не будут.",
        ),
        loc_line("CHI_pay_bribe", "Обработка приказа: 500 000, при коррупции 1 000 000"),
        loc_line(
            "CHI_pay_bribe_desc",
            "Подкуп: 500 000. При высокой коррупции 1 000 000. Если денег не хватает, списывать не будут.",
        ),
        loc_line(
            "CHI_pay_canal",
            "Обработка приказа: 1 000 000 + дерево 3000, цемент 1500, железо 1000, пиломатериалы 800",
        ),
        loc_line(
            "CHI_pay_canal_desc",
            "Очистка Великого канала от ила в этом регионе: 1 000 000, дерево 3000, цемент 1500, железо 1000, пиломатериалы 800. При коррупции 2 000 000.",
        ),
        loc_line(
            "CHI_pay_yangtze",
            "Обработка приказа: 1 000 000 + дерево 2500, цемент 1200, железо 1500, пиломатериалы 700",
        ),
        loc_line(
            "CHI_pay_yangtze_desc",
            "Расчистка фарватера Янцзы в этом регионе: 1 000 000, дерево 2500, цемент 1200, железо 1500, пиломатериалы 700. При коррупции 2 000 000.",
        ),
        loc_line(
            "CHI_pay_yellow",
            "Обработка приказа: 1 500 000 + дерево 4000, цемент 2500, железо 1500, пиломатериалы 1200",
        ),
        loc_line(
            "CHI_pay_yellow_desc",
            "Ремонт дамб Хуанхэ в этом регионе: 1 500 000, дерево 4000, цемент 2500, железо 1500, пиломатериалы 1200. При коррупции 3 000 000. Перенос русла — решение двора.",
        ),
        loc_line(
            "CHI_pay_water_1",
            "Обработка приказа: 200 000 + дерево 2400, цемент 1200, железо 600, пиломатериалы 600",
        ),
        loc_line(
            "CHI_pay_water_1_desc",
            "Ирригация I: 200 000, дерево 2400, цемент 1200, железо 600, пиломатериалы 600. При коррупции 400 000. Если не хватает, списывать не будут.",
        ),
        loc_line(
            "CHI_pay_water_2",
            "Обработка приказа: 500 000 + дерево 3600, цемент 1800, железо 1200, пиломатериалы 900",
        ),
        loc_line(
            "CHI_pay_water_2_desc",
            "Ирригация II: 500 000, дерево 3600, цемент 1800, железо 1200, пиломатериалы 900. При коррупции 1 000 000. Если не хватает, списывать не будут.",
        ),
        loc_line(
            "CHI_pay_water_3",
            "Обработка приказа: 1 000 000 + дерево 5400, цемент 3000, железо 1800, пиломатериалы 1500",
        ),
        loc_line(
            "CHI_pay_water_3_desc",
            "Ирригация III: 1 000 000, дерево 5400, цемент 3000, железо 1800, пиломатериалы 1500. При коррупции 2 000 000. Если не хватает, списывать не будут.",
        ),
        loc_line(
            "CHI_pay_water_4",
            "Обработка приказа: 2 000 000 + дерево 7500, цемент 4500, железо 3000, пиломатериалы 2400",
        ),
        loc_line(
            "CHI_pay_water_4_desc",
            "Ирригация IV: 2 000 000, дерево 7500, цемент 4500, железо 3000, пиломатериалы 2400. При коррупции 4 000 000. Если не хватает, списывать не будут.",
        ),
        loc_line("CHI_sel_bribe", "Подкупить лидеров сепаратистов"),
        loc_line("CHI_sel_bribe_desc", "Взятки местным вожакам. Сепаратизм региона падает на 1 уровень. Стоимость 500 000. Повтор через год."),
        loc_line("CHI_sel_tax_cut", "Снизить налоги в этом регионе на 2 года"),
        loc_line(
            "CHI_sel_tax_cut_desc",
            "Маркер на регион на 2 года. Казна отдельно теряет 4% эффективности налогов за каждый такой регион (до 20). В самом маркере провинции налога нет — штраф только в страновом стеке.",
        ),
        loc_line("CHI_sel_revolt", "Спровоцировать восстание"),
        loc_line(
            "CHI_sel_revolt_desc",
            "Милитантность в этой провинции на 180 дней. Когда модификатор спадёт, если провинция под контролем Китая, пульс Ян-Майена снизит сепаратизм региона на 1. Повтор 2 года.",
        ),
        loc_line("CHI_sel_revolt_wait", "Восстание уже спровоцировано (2 года)"),
        loc_line("CHI_sel_revolt_wait_desc", "В этой провинции уже идёт провокация. Повтор через 2 года."),
        loc_line("CHI_sel_revolt_won", "Восстание подавлено"),
        loc_line("CHI_sel_revolt_won_desc", "Провинция снова под контролем. Сепаратизм региона снижен на 1 уровень."),
        loc_line("CHI_sep_tax_cut", "Налоговая льгота региона"),
        loc_line(
            "CHI_sep_tax_cut_desc",
            "Маркер региона на 2 года. В этой карточке нет штрафа налога: казна теряет 4% эффективности за стек CHI_sep_tax_stack, по одному на регион.",
        ),
        loc_line("CHI_sep_revolt_cd", "Провокация восстания"),
        loc_line("CHI_sep_revolt_cd_desc", "В этой провинции уже спровоцировано восстание. Повтор через 2 года."),
        loc_line("CHI_sep_uprising", "Спровоцированное восстание"),
        loc_line("CHI_sep_uprising_desc", "Население поднято на 180 дней. Когда модификатор спадёт, если провинция под контролем Китая, пульс Ян-Майена снизит сепаратизм региона на 1."),
        loc_line("CHI_provoked_rebels", "Спровоцированные повстанцы"),
        loc_line("CHI_provoked_rebels_title", "Спровоцированное восстание"),
        loc_line("CHI_provoked_rebels_name", "Спровоцированные повстанцы"),
        loc_line(
            "CHI_provoked_rebels_desc",
            "Население провинции поднято приказом двора. Они сложатся, когда провинция снова будет под контролем Китая.",
        ),
        loc_line("CHI_provoked_rebels_army", "Повстанческая армия"),
        loc_line("CHI_click_mark", "Обработка приказа"),
        loc_line("CHI_click_mark_desc", "Временный маркер выбранной провинции."),
        loc_line("CHI_lvl_dropped", "Снижение уровня"),
        loc_line("CHI_lvl_dropped_desc", "Служебный маркер: уровень бедствия уже снижен в этом проходе."),
        loc_line("CHI_sep_revolt_pending", "Исход восстания"),
        loc_line(
            "CHI_sep_revolt_pending_desc",
            "После спада восстания, если провинция под контролем Китая, сепаратизм региона будет снижен.",
        ),
        loc_line("CHI_sep_revolt_won", "Восстание подавлено"),
        loc_line("CHI_sep_revolt_won_desc", "Провинция снова под контролем."),
        loc_line("CHI_corruption_no", "Без коррупции"),
        loc_line("CHI_corruption_no_desc", "Коррупция снята."),
        loc_line("CHI_fleet_anti_piracy_ready", "Флот против пиратства"),
        loc_line(
            "CHI_fleet_anti_piracy_ready_desc",
            "В строю не меньше 200 кораблей: флот может подавить пиратство по всей стране.",
        ),
        loc_line("CHI_sep_menu_title", "Сепаратизм региона"),
        loc_line("CHI_sel_sep_none_desc", "В этой провинции нет сепаратизма, который можно снизить."),
        loc_line("CHI_sel_sep_wait_desc", "В регионе уже идёт подавление. Повтор через год."),
        loc_line("CHI_sel_tax_done", "Налоги снижены"),
        loc_line("CHI_sel_tax_done_desc", "Льгота действует 2 года в этом регионе. Казна теряет 4% эффективности налогов. Другие регионы можно освободить отдельно."),
        loc_line("CHI_water_choice_title", "Ирригация региона"),
        loc_line(
            "CHI_water_choice_desc",
            "Ремонт снижает воду на 1 уровень в этом регионе. Если ремонт уже идёт, кнопок нет. I: 200 000. II: 500 000. III: 1 000 000. IV: 2 000 000 плюс товары. При коррупции деньги вдвое.",
        ),
        loc_line(
            "CHI_water_choice_1_desc",
            "Уровень I. Снижает проблему воды на 1 ступень в этом регионе. Стоимость: 200 000, дерево 2400, цемент 1200, железо 600, пиломатериалы 600. При коррупции: 400 000. Повтор в этом регионе примерно через 2.5 года.",
        ),
        loc_line(
            "CHI_water_choice_2_desc",
            "Уровень II. Снижает проблему воды на 1 ступень в этом регионе. Стоимость: 500 000, дерево 3600, цемент 1800, железо 1200, пиломатериалы 900. При коррупции: 1 000 000. Повтор в этом регионе примерно через 2.5 года.",
        ),
        loc_line(
            "CHI_water_choice_3_desc",
            "Уровень III. Снижает проблему воды на 1 ступень в этом регионе. Стоимость: 1 000 000, дерево 5400, цемент 3000, железо 1800, пиломатериалы 1500. При коррупции: 2 000 000. Повтор в этом регионе примерно через 2.5 года.",
        ),
        loc_line(
            "CHI_water_choice_4_desc",
            "Уровень IV. Снижает проблему воды на 1 ступень в этом регионе. Стоимость: 2 000 000, дерево 7500, цемент 4500, железо 3000, пиломатериалы 2400. При коррупции: 4 000 000. Повтор в этом регионе примерно через 2.5 года.",
        ),
        loc_line(
            "CHI_water_choice_unique_desc",
            "Речные проекты: очистка канала, фарватер Янцзы, дамбы Хуанхэ. Каждая кнопка только если этот модификатор есть в провинции. Перенос русла Хуанхэ — решение двора.",
        ),
        loc_line("CHI_sel_no_water_desc", "В этой провинции нет проблем с водой."),
        loc_line(
            "CHI_sel_hydro_wait_desc",
            "В этом регионе уже идёт ремонт ирригации. Следующий заказ здесь примерно через 2.5 года. Другие регионы можно чинить отдельно.",
        ),
        loc_line("CHI_famine_choice_title", "Голод региона"),
        loc_line("CHI_famine_choice_desc", "Великий амбар снижает голод на 1 уровень. Стоимость из складов: дерево 250, цемент 150, железо 100, пиломатериалы 80. Если программа уже идёт, кнопки амбара нет — повтор 2 года. Если амбар уже стоит и голода нет, заказывать нечего."),
        loc_line("CHI_sel_no_famine_desc", "В этой провинции нет голода."),
        loc_line("CHI_sel_has_granary_desc", "Великий амбар в регионе уже стоит."),
        loc_line("CHI_sel_food_wait", "Продовольственная программа идёт"),
        loc_line("CHI_sel_food_wait_desc", "В регионе уже идёт продовольственная программа. Повтор через 2 года."),
        loc_line("CHI_food_cd", "Продовольственная программа"),
        loc_line("CHI_food_cd_desc", "В регионе уже идёт продовольственная программа. Повтор через 2 года."),
        loc_line("CHI_hydro_cd", "Ремонт ирригации региона"),
        loc_line(
            "CHI_hydro_cd_desc",
            "В этом регионе уже идут работы по ирригации и дамбам. Следующий заказ здесь примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_hydro_wait", "Ремонт ирригации в регионе уже идёт (~2.5 года)"),
        loc_line("CHI_great_granary", "Великий амбар"),
        loc_line("CHI_great_granary_desc", "Казённый амбар региона. Частично держит зерно и людей."),
        loc_line("CHI_famine_tied_to_water", "Голод связан с водой"),
        loc_line("CHI_famine_tied_to_water_desc", "Ремонт ирригации также снижает такой голод на 1 уровень."),
        loc_line("CHI_water_canal_silt", "Заиление Великого канала"),
        loc_line(
            "CHI_water_canal_silt_desc",
            "Ил душит судоходство канала. Снимается проектом «Очистка канала от ила» в селекторе этого региона.",
        ),
        loc_line("CHI_water_yangtze_nav", "Срыв судоходства Янцзы"),
        loc_line(
            "CHI_water_yangtze_nav_desc",
            "Фарватер занесён, речная торговля парализована. Снимается расчисткой фарватера Янцзы в селекторе этого региона.",
        ),
        loc_line("CHI_water_yellow_dikes", "Угроза дамб Хуанхэ"),
        loc_line(
            "CHI_water_yellow_dikes_desc",
            "Дамбы Хуанхэ в этом регионе могут прорваться. Локальный ремонт — селектор. Переложить русло по всей империи — решение «Работы на Хуанхэ».",
        ),
        loc_line("CHI_canal_cd", "Очистка канала"),
        loc_line("CHI_canal_cd_desc", "В регионе уже чистят канал от ила. Повтор примерно через 2.5 года."),
        loc_line("CHI_yangtze_cd", "Расчистка Янцзы"),
        loc_line("CHI_yangtze_cd_desc", "В регионе уже чистят фарватер Янцзы. Повтор примерно через 2.5 года."),
        loc_line("CHI_yellow_cd", "Ремонт дамб Хуанхэ"),
        loc_line("CHI_yellow_cd_desc", "В регионе уже чинят дамбы Хуанхэ. Повтор примерно через 2.5 года."),
        loc_line("CHI_yellow_new_course", "Новое русло Хуанхэ"),
        loc_line(
            "CHI_yellow_new_course_desc",
            "Двор переложил главное русло Хуанхэ. Старая угроза дамб по провинциям снята.",
        ),
        loc_line("CHI_yellow_river_works", "Работы на Хуанхэ"),
        loc_line(
            "CHI_yellow_river_works_desc",
            "Нужно: мир, 2 000 000 в казне, год 1846 или технология железных дорог. Варианты: переложить русло на север или укрепить дамбы по всей империи. Региональный ремонт дамб — селектор провинции.",
        ),
        loc_line("CHI_yellow_course_title", "Хуанхэ: русло или дамбы"),
        loc_line(
            "CHI_yellow_course_desc",
            "Локальный ремонт дамб делается селектором по регионам. Здесь — общеимперский выбор. Северное русло: 2 000 000, дерево 4000, цемент 2000, железо 1500, пиломатериалы 1000, снимает угрозу дамб везде. Укрепить дамбы по стране: 2 000 000, без переноса русла.",
        ),
        loc_line("CHI_yellow_course_north", "Переложить русло на север"),
        loc_line("CHI_yellow_course_dikes", "Укрепить дамбы по всей империи"),
        loc_line("CHI_patchwork_empire", "Лоскутная феодальная империя"),
        loc_line(
            "CHI_patchwork_empire_desc",
            "Неснимаемый порядок Цин: слабый центр, быстрый набор ополчения. "
            "Лимит солдат (~3% населения провинции) задаётся типами POP, не этим модификатором.",
        ),
        loc_line("CHI_inefficient_bureaucracy", "Неэффективная бюрократия"),
        loc_line("CHI_port_anti_piracy", "Портовый надзор"),
        loc_line("CHI_port_anti_piracy_desc", "Порт ослабляет приморский разбой в этой провинции. Штрафы пиратства смотрите в карточке пиратства, не здесь."),
        loc_line("CHI_famine_infra_relief", "Инфраструктура против голода"),
        loc_line(
            "CHI_famine_infra_relief_desc",
            "Один раз: когда во всех провинциях региона железная дорога 2-го уровня, пульс Ян-Майена снижает голод на 1 и вешает этот модификатор. Это не кнопка селектора. Повторно голод сам не падает.",
        ),
    ]
    bar = mod.bar
    fam_txt = {
        1: "Прирост -0.1%/мес, начинается исход.",
        2: "Прирост -0.13%/мес, сильный исход.",
        3: "Прирост -0.17%/мес, тяжёлый голод.",
        4: "Прирост -0.2%/мес, исход из региона.",
    }
    roman = {1: "I", 2: "II", 3: "III", 4: "IV"}
    for i in range(1, 5):
        add.append(loc_line(f"CHI_famine_{i}", f"Голод {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_famine_{i}_desc",
                f"Проблема с едой. {bar(i, 4)}. {fam_txt[i]} "
                "Снимается великим амбаром (дерево 250, цемент 150, железо 100, пиломатериалы 80).",
            )
        )
    for i in range(1, 5):
        add.append(loc_line(f"CHI_separatism_{i}", f"Сепаратизм {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_separatism_{i}_desc",
                f"Региональный сепаратизм. {bar(i, 4)}. "
                "Снимается подкупом (500 000, при коррупции 1 000 000) или после подавления восстания. Порог солдат задаётся типами POP, не этой карточкой.",
            )
        )
        add.append(loc_line(f"CHI_water_{i}", f"Ирригация {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_water_{i}_desc",
                f"Проблемы ирригации и дамб. {bar(i, 4)}. Снимается поэтапным ремонтом (деньги и товары по уровню).",
            )
        )
        add.append(loc_line(f"CHI_piracy_{i}", f"Пиратство {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_piracy_{i}_desc",
                f"Приморская угроза. {bar(i, 4)}. "
                "Порт снижает на 1 только в провинции с военно-морской базой. Флот в 200 кораблей снимает пиратство по всей стране.",
            )
        )
    for i in range(1, TAX_STACKS + 1):
        add.append(loc_line(f"CHI_sep_tax_stack_{i}", "Региональная налоговая льгота"))
        add.append(
            loc_line(
                f"CHI_sep_tax_stack_{i}_desc",
                "Казна теряет 4% эффективности налогов, пока в одном из регионов действует льгота. Несколько регионов складываются.",
            )
        )
    extra_keys = {ln.split(";", 1)[0] for ln in add}
    for line in mod.build_loc().splitlines(True):
        key = line.split(";", 1)[0] if line.strip() else ""
        if key and key not in extra_keys:
            add.append(line if line.endswith("\n") else line + "\r\n")
    deduped_add = {}
    for ln in add:
        k = ln.split(";", 1)[0]
        if k:
            deduped_add[k] = ln if ln.endswith("\r\n") else ln + "\r\n"
    # Managed keys from add overwrite kept; one line per key in final file.
    final = {}
    for ln in kept:
        k = ln.split(";", 1)[0] if ln.strip() else ""
        if k:
            final[k] = ln if ln.endswith("\r\n") else ln + "\r\n"
    for ln in deduped_add.values():
        k = ln.split(";", 1)[0]
        if k:
            final[k] = ln
    body = "".join(final.values())
    if not body.endswith("\r\n"):
        body += "\r\n"
    out = body.encode("cp1251")
    path.write_bytes(out.replace(b"\n", b"\r\n").replace(b"\r\r\n", b"\r\n"))
    print("loc ok, fffd", out.count(b"\xef\xbf\xbd"))


def write_river_policy():
    dec = ROOT / "decisions" / "CHI_rivers.txt"
    dec.write_bytes(
        """political_decisions = {
	CHI_yellow_river_works = {
		picture = build_kiel_canal
		potential = {
			tag = CHI
			NOT = { has_country_flag = CHI_yellow_course_done }
			NOT = { has_country_flag = CHI_yellow_dikes_nation_done }
			any_owned_province = { has_province_modifier = CHI_water_yellow_dikes }
		}
		allow = {
			war = no
			money = 2000000
			OR = {
				year = 1846
				iron_railroad = 1
			}
		}
		effect = {
			country_event = { id = 144540 days = 0 }
		}
		ai_will_do = { factor = 0 }
	}
}
""".replace(
            "\r\n", "\n"
        )
        .replace("\n", "\r\n")
        .encode("utf-8")
    )
    print("CHI_rivers.txt", dec.stat().st_size)
    ev = ROOT / "events" / "CHI_crisis_41_yellow_course.txt"
    ev.write_bytes(
        """# Nationwide Yellow River course / dikes (from decision CHI_yellow_river_works)

country_event = {
	id = 144540
	title = "CHI_yellow_course_title"
	desc = "CHI_yellow_course_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {
		name = "CHI_yellow_course_north"
		money = -2000000
		timber = -4000
		cement = -2000
		iron = -1500
		lumber = -1000
		set_country_flag = CHI_yellow_course_done
		JAN = { country_event = { id = 144541 days = 0 } }
	}
	option = {
		name = "CHI_yellow_course_dikes"
		money = -2000000
		set_country_flag = CHI_yellow_dikes_nation_done
		JAN = { country_event = { id = 144542 days = 0 } }
	}
	option = {
		name = "CHI_sel_back"
	}
}

country_event = {
	id = 144541
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	immediate = {
		CHI = {
			any_owned = {
				limit = { has_province_modifier = CHI_water_yellow_dikes }
				remove_province_modifier = CHI_water_yellow_dikes
			}
			add_country_modifier = { name = CHI_yellow_new_course duration = -1 }
			prestige = 10
		}
	}
	option = {
		name = "noloc"
	}
}

country_event = {
	id = 144542
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	immediate = {
		CHI = {
			any_owned = {
				limit = { has_province_modifier = CHI_water_yellow_dikes }
				remove_province_modifier = CHI_water_yellow_dikes
			}
			prestige = 5
		}
	}
	option = {
		name = "noloc"
	}
}
""".replace(
            "\r\n", "\n"
        )
        .replace("\n", "\r\n")
        .encode("utf-8")
    )
    print(ev.name, ev.stat().st_size)


def main():
    patch_jan()
    write_crises()
    write_selector()
    write_river_policy()
    patch_modifiers()
    patch_triggered()
    patch_loc()
    print("done")


if __name__ == "__main__":
    main()

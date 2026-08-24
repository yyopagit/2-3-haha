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


def mark_click():
    return """		owner = {
			any_owned = { clr_province_flag = CHI_click }
		}
		set_province_flag = CHI_click"""


def reopen_hub():
    """Return to the single hub on this province — no country router."""
    return f"""{mark_click()}
{open_pe(HUB_ID)}"""


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

HAS_FOOD = """				OR = {
					has_province_modifier = CHI_hydro_cd
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


def hub_event(eid):
    """Single hub: options appear only when the province has that crisis."""
    return f"""province_event = {{
	title = "CHI_Selector_EvtName"
	desc = "CHI_Selector_EvtDesc"
	id = {eid}
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		owner = {{
			any_owned = {{ clr_province_flag = CHI_click }}
		}}
		set_province_flag = CHI_click
		province_selector = -1
	}}
	option = {{
		name = "CHI_menu_sep"
		trigger = {{
{HAS_SEP}
		}}
{open_pe(SEP_MENU_ID)}
	}}
	option = {{
		name = "CHI_menu_food"
		trigger = {{
{HAS_FOOD}
		}}
{open_pe(FOOD_MENU_ID)}
	}}
	option = {{
		name = "CHI_menu_coast"
		trigger = {{
{HAS_COAST}
		}}
{open_pe(COAST_MENU_ID)}
	}}
	option = {{
		name = "CHI_menu_misc"
{open_pe(MISC_MENU_ID)}
	}}
	option = {{
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}}
}}
"""


def build_hubs():
    # Decision still references 144409-144415 — aliases that reopen the real hub.
    stubs = []
    for eid in range(144409, 144416):
        stubs.append(
            f"""province_event = {{
	id = {eid}
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		set_province_flag = CHI_click
		province_event = {{ id = {HUB_ID} days = 0 }}
	}}
	option = {{
		name = "CHI_sel_ok"
	}}
}}
"""
        )
    return hub_event(HUB_ID) + "\n" + "\n".join(stubs)


def build_hub():
    return build_hubs()


def build_food_submenu():
    back = reopen_hub()
    return f"""
province_event = {{
	title = "CHI_menu_food_title"
	desc = "CHI_menu_food_desc"
	id = {FOOD_MENU_ID}
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_menu_hydro"
		trigger = {{
{HAS_WATER}
		}}
{open_pe(WATER_MENU_ID)}
	}}
	option = {{
		name = "CHI_menu_granary"
		trigger = {{
{HAS_FAMINE}
		}}
{open_pe(GRANARY_MENU_ID)}
	}}
	option = {{
		name = "CHI_sel_back"
{back}
	}}
}}
"""


def build_coast_submenu():
    back = reopen_hub()
    return f"""
province_event = {{
	title = "CHI_menu_coast_title"
	desc = "CHI_menu_coast_desc"
	id = {COAST_MENU_ID}
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_port_piracy"
{open_pe(PORT_MENU_ID)}
	}}
	option = {{
		name = "CHI_sel_fleet_piracy"
{open_pe(FLEET_MENU_ID)}
	}}
	option = {{
		name = "CHI_sel_back"
{back}
	}}
}}
"""


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
		set_province_flag = CHI_do_depot
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
					has_province_flag = {flag}
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
					has_province_flag = {flag}
					owner = {{ has_country_flag = CHI_crisis_paid }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {eid} days = 1 }}
			}}"""


def wait_cd(flag, cd_mod, wait_id):
    return f"""			random_owned = {{
				limit = {{
					has_province_flag = {flag}
					has_province_modifier = {cd_mod}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {wait_id} days = 1 }}
				clr_province_flag = {flag}
			}}"""


def granary_goods_pay():
    """Deduct stockpile goods if enough; set CHI_crisis_paid on success."""
    return """			random_owned = {
				limit = {
					has_province_flag = CHI_do_granary_pay
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
					has_province_flag = {flag}
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144524 days = 1 }}
			}}"""


def build_pay_dispatcher():
    bribe_pay = pay_flag("CHI_do_bribe", 500000, 1000000)
    water_pay = "\n".join(
        [
            water_level_pay(1, WATER_REPAIR[1]),
            water_level_pay(2, WATER_REPAIR[2]),
            water_level_pay(3, WATER_REPAIR[3]),
            water_level_pay(4, WATER_REPAIR[4]),
        ]
    )
    uniq_pay = unique_goods_pay()
    water_need = "\n".join(
        [
            fire_need("CHI_do_water_pay", "CHI_water_1", 144450),
            fire_need("CHI_do_water_pay", "CHI_water_2", 144451),
            fire_need("CHI_do_water_pay", "CHI_water_3", 144452),
            fire_need("CHI_do_water_pay", "CHI_water_4", 144454),
        ]
    )
    uniq_need = "\n".join(
        [
            fire_need("CHI_do_uniq_pay", "CHI_water_canal_silt", 144454),
            fire_need("CHI_do_uniq_pay", "CHI_water_yangtze_nav", 144454),
            fire_need("CHI_do_uniq_pay", "CHI_water_yellow_dikes", 144454),
        ]
    )
    def stage(eid, body):
        # Province event (not JAN country): tooltips stay on CHI, no "Jan Mayen / ."
        return f"""
province_event = {{
	id = {eid}
	title = "CHI_pay_processing"
	desc = "CHI_pay_processing_desc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		owner = {{
			clr_country_flag = CHI_crisis_paid
			clr_country_flag = CHI_pay_fired
			clr_country_flag = CHI_pay_part
{body}
			clr_country_flag = CHI_pay_fired
		}}
	}}
	option = {{
		name = "CHI_sel_ok"
	}}
}}
"""

    stage_bribe = f"""{wait_cd("CHI_do_bribe", "CHI_sep_cd", 144456)}
{bribe_pay}
{fire_paid("CHI_do_bribe", 144437)}
			random_owned = {{
				limit = {{
					has_province_flag = CHI_do_bribe
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144451 days = 1 }}
			}}
			any_owned = {{ clr_province_flag = CHI_do_bribe }}"""

    stage_water = f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd", 144458)}
{water_pay}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need}
{fire_goods_fallback("CHI_do_water_pay")}
			any_owned = {{ clr_province_flag = CHI_do_water_pay }}"""

    stage_uniq = f"""{wait_cd("CHI_do_uniq_pay", "CHI_hydro_cd", 144458)}
{uniq_pay}
{fire_paid("CHI_do_uniq_pay", 144433)}
{uniq_need}
{fire_goods_fallback("CHI_do_uniq_pay")}
			any_owned = {{ clr_province_flag = CHI_do_uniq_pay }}"""

    stage_granary = f"""{granary_goods_pay()}
{fire_paid("CHI_do_granary_pay", 144432)}
			random_owned = {{
				limit = {{
					has_province_flag = CHI_do_granary_pay
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144524 days = 1 }}
			}}
			any_owned = {{ clr_province_flag = CHI_do_granary_pay }}"""

    return {
        "sep": stage(144493, stage_bribe),
        "water": stage(144494, stage_water),
        "unique": stage(144495, stage_uniq),
        "granary": stage(144496, stage_granary),
    }


def back_effect(back_id):
    if back_id == "hub":
        return reopen_hub()
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
    # Prefer province_event so tooltips do not show "Jan Mayen: Event '.'".
    return f"""		set_province_flag = {flag}
		province_event = {{ id = {pay_id} days = 0 }}"""


def bribe_sep_effect():
    """Flat 500k bribe via pay stage 144493. Tooltip stays on CHI."""
    return pay_click("CHI_do_bribe", 144493)


def granary_build_effect():
    """Regional granary: goods from stockpile via pay stage 144496."""
    return pay_click("CHI_do_granary_pay", 144496)


def sep_methods(eid=SEP_MENU_ID, lvl=1):
    tax_prov = """		set_province_flag = CHI_do_tax_cut
		province_event = { id = 144512 days = 0 }"""
    revolt_fx = f"""		any_pop = {{
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
		set_province_flag = CHI_sep_revolt_pending
		clr_province_flag = CHI_sep_revolt_armed
		clr_province_flag = CHI_sep_revolt_won
{reopen_hub()}"""
    return f"""province_event = {{
	id = {SEP_MENU_ID}
	title = "CHI_sep_menu_title"
	desc = "CHI_menu_sep_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_bribe"
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
{revolt_fx}
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
            notice(144450, "CHI_need_200k", "CHI_need_money_desc", "hub"),
            notice(144451, "CHI_need_500k", "CHI_need_money_desc", "hub"),
            notice(144452, "CHI_need_1m", "CHI_need_money_desc", "hub"),
            notice(144453, "CHI_need_15m", "CHI_need_money_desc", "hub"),
            notice(144454, "CHI_need_2m", "CHI_need_money_desc", "hub"),
            notice(144524, "CHI_need_goods", "CHI_need_goods_desc", "hub"),
        ]
    )


def build_sep_leaves():
    parts = [
        notice(144455, "CHI_sel_sep_none", "CHI_sel_sep_none_desc", "hub"),
        notice(144456, "CHI_sel_sep_wait", "CHI_sel_sep_wait_desc", "hub"),
        notice(144491, "CHI_sel_revolt_won", "CHI_sel_revolt_won_desc", "hub"),
        notice(144513, "CHI_sel_tax_done", "CHI_sel_tax_done_desc", "hub"),
        sep_methods(),
    ]
    for eid in range(144481, 144490):
        parts.append(
            f"""province_event = {{
	id = {eid}
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		province_event = {{ id = {SEP_MENU_ID} days = 0 }}
	}}
	option = {{
		name = "CHI_sel_ok"
	}}
}}
"""
        )
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
    gt = _goods_trigger(costs, indent + "\t\t")
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
{indent}\t\thas_province_flag = {flag}
{extra}{indent}\t}}
{indent}\towner = {{
{body}
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
{reopen_hub()}
\t}}
}}
"""

def build_water_leaves():
    opts = []
    for lvl in range(1, 5):
        opts.append(
            f"""	option = {{
		name = "CHI_sel_water_{lvl}"
		trigger = {{
			has_province_modifier = CHI_water_{lvl}
			NOT = {{ has_province_modifier = CHI_hydro_cd }}
		}}
{pay_click("CHI_do_water_pay", 144494)}
	}}"""
        )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_unique_water"
		trigger = {{
			OR = {{
				has_province_modifier = CHI_water_canal_silt
				has_province_modifier = CHI_water_yangtze_nav
				has_province_modifier = CHI_water_yellow_dikes
			}}
			NOT = {{ has_province_modifier = CHI_hydro_cd }}
		}}
{pay_click("CHI_do_uniq_pay", 144495)}
	}}"""
    )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_hydro_wait"
		trigger = {{
			has_province_modifier = CHI_hydro_cd
		}}
{reopen_hub()}
	}}"""
    )
    opts.append(
        f"""	option = {{
		name = "CHI_sel_back"
{reopen_hub()}
	}}"""
    )
    joined = "\n".join(opts)
    menu = f"""province_event = {{
	id = {WATER_MENU_ID}
	title = "CHI_water_choice_title"
	desc = "CHI_water_choice_desc"
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""
    aliases = []
    for eid in (144471, 144472, 144473, 144474):
        aliases.append(
            f"""province_event = {{
	id = {eid}
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		province_event = {{ id = {WATER_MENU_ID} days = 0 }}
	}}
	option = {{
		name = "CHI_sel_ok"
	}}
}}
"""
        )
    return "\n".join(
        [
            notice(144457, "CHI_sel_no_water", "CHI_sel_no_water_desc", "hub"),
            notice(144458, "CHI_sel_hydro_wait", "CHI_sel_hydro_wait_desc", "hub"),
            menu,
        ]
        + aliases
    )


def build_famine_leaves():
    hub = reopen_hub()
    granary_menu = f"""province_event = {{
	id = 144475
	title = "CHI_famine_choice_title"
	desc = "CHI_famine_choice_desc"
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_granary"
{granary_build_effect()}
	}}
	option = {{
		name = "CHI_sel_back"
{hub}
	}}
}}
"""
    return "\n".join(
        [
            notice(144459, "CHI_sel_no_famine", "CHI_sel_no_famine_desc", "hub"),
            notice(144460, "CHI_sel_has_granary", "CHI_sel_has_granary_desc", "hub"),
            notice(144523, "CHI_sel_food_wait", "CHI_sel_food_wait_desc", "hub"),
            granary_menu,
        ]
    )


def build_piracy_leaves():
    hub = reopen_hub()
    port_fx = f"""		remove_province_modifier = CHI_piracy_4
		remove_province_modifier = CHI_piracy_3
		remove_province_modifier = CHI_piracy_2
		add_province_modifier = {{ name = CHI_piracy_1 duration = -1 }}
		add_province_modifier = {{ name = CHI_port_anti_piracy duration = -1 }}
{hub}"""
    fleet_fx = f"""		owner = {{
			any_owned = {{
				remove_province_modifier = CHI_piracy_1
				remove_province_modifier = CHI_piracy_2
				remove_province_modifier = CHI_piracy_3
				remove_province_modifier = CHI_piracy_4
			}}
		}}
{hub}"""
    return "\n".join(
        [
            notice(144461, "CHI_sel_not_coast", "CHI_sel_not_coast", "hub"),
            notice(144462, "CHI_sel_no_piracy", "CHI_sel_no_piracy", "hub"),
            notice(144463, "CHI_need_port", "CHI_need_port", "hub"),
            notice(144464, "CHI_need_fleet", "CHI_need_fleet", "hub"),
            confirm(144465, "CHI_sel_port_piracy", "CHI_menu_coast_desc", "CHI_sel_port_piracy", port_fx, "hub"),
            confirm(144466, "CHI_sel_fleet_piracy", "CHI_menu_coast_desc", "CHI_sel_fleet_piracy", fleet_fx, "hub"),
        ]
    )


def build_depot_leaf():
    depot_fx = """		owner = {
			money = -500000
			any_owned = {
				remove_province_modifier = provincial_supply_depot_pmodifier
			}
		}
		add_province_modifier = {
			name = provincial_supply_depot_pmodifier
			duration = -1
		}
		province_selector = -1"""
    return confirm(144467, "Selector_EvtOptSupplyDepot", "Selector_EvtDesc", "Selector_EvtOptSupplyDepot", depot_fx, "hub")


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
    fam_or = """					OR = {
						has_province_modifier = CHI_famine_1
						has_province_modifier = CHI_famine_2
						has_province_modifier = CHI_famine_3
						has_province_modifier = CHI_famine_4
					}"""
    marks = []
    for rid in rids:
        marks.append(
            f"""			any_owned = {{
				limit = {{
					has_province_flag = CHI_reg_{rid}
{fam_or}
					owner = {{
						NOT = {{ has_country_flag = CHI_infra_drop_{rid} }}
						NOT = {{
							any_owned = {{
								has_province_flag = CHI_reg_{rid}
								NOT = {{ railroad = 2 }}
							}}
						}}
					}}
				}}
				owner = {{
					set_country_flag = CHI_act_{rid}
					set_country_flag = CHI_infra_drop_{rid}
				}}
			}}"""
        )
    drop = mod.famine_drop_block(rids, indent="\t\t\t")
    clr = mod.gen_clr_act(rids)
    joined = "\n".join(marks)
    return f"""
# CHI_INFRA_PULSE_START
country_event = {{
	id = 144436
	title = "noloc"
	desc = "noloc"
	trigger = {{ tag = JAN }}
	mean_time_to_happen = {{ days = 30 }}
	immediate = {{
		CHI = {{
{joined}
{drop}
{clr}
		}}
	}}
	option = {{
		name = "noloc"
	}}
}}
# CHI_INFRA_PULSE_END
"""


def build_revolt_pulse(rids):
    """Disabled — auto pulse false-fired at game start and stacked with visible router."""
    return """
# CHI_REVOLT_PULSE_START
# Auto revolt-won pulse DISABLED (startup spam / false rewards).
# CHI_REVOLT_PULSE_END
"""




def build_region_flag_event():
    """Decisions cannot set_province_flag inside any_owned/random_owned (restricted
    ProvinceCommand scope, silently dropped by the engine - confirmed by validator log).
    So CHI_reg_* flags and the naval_base piracy auto-downgrade are set here instead,
    in a plain event, fired once from SETUP.txt's marker_jan via country_event=144405."""
    regions = mod.parse_chi_regions()
    used = {k: v for k, v in regions.items() if k in mod.LEVELS and k not in mod.SKIP}
    blocks = []
    for key, ids in used.items():
        rid = key.split("_")[1]
        or_ids = "\n".join(
            "\t\t\t\t\t" + " ".join(f"province_id = {x}" for x in ids[i : i + 6])
            for i in range(0, len(ids), 6)
        )
        blocks.append(
            f"""			any_owned = {{
				limit = {{
					OR = {{
{or_ids}
					}}
				}}
				set_province_flag = CHI_reg_{rid}
			}}"""
        )
    pirate_drop = """			any_owned = {
				limit = {
					naval_base = 1
					has_province_modifier = CHI_piracy_3
				}
				remove_province_modifier = CHI_piracy_3
				add_province_modifier = { name = CHI_piracy_2 duration = -1 }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}
			any_owned = {
				limit = {
					naval_base = 1
					has_province_modifier = CHI_piracy_2
					NOT = { has_province_modifier = CHI_port_anti_piracy }
				}
				remove_province_modifier = CHI_piracy_2
				add_province_modifier = { name = CHI_piracy_1 duration = -1 }
				add_province_modifier = { name = CHI_port_anti_piracy duration = -1 }
			}"""
    # Clear provoke leftovers so a new game never inherits pending/won flags.
    revolt_clr = """			any_owned = {
				clr_province_flag = CHI_sep_revolt_pending
				clr_province_flag = CHI_sep_revolt_armed
				clr_province_flag = CHI_sep_revolt_won
			}"""
    joined = "\n".join(blocks)
    return f"""
# CHI_REGION_FLAGS_START
country_event = {{
	id = 144405
	title = "noloc"
	desc = "noloc"
	is_triggered_only = yes
	immediate = {{
		CHI = {{
{joined}
{pirate_drop}
{revolt_clr}
		}}
	}}
	option = {{
		name = "noloc"
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
    """Open the hub as a province_event from the decision (same pattern as 144407).
    THIS is the province that has the building. Hub immediate then removes the
    selector on THIS - country_event any_owned cannot do that, so leftovers
    (Gaozhou) stayed forever and random_owned always picked them first."""
    routes = "\n".join(dec_hub_route(extra, eid) for extra, eid in HUB_RULES)
    routes += "\n" + dec_hub_route("", 144415)
    return f"""political_decisions = {{
	select_prov = {{
		picture = build_kiel_canal
			potential = {{
				tag = JAN
				META_1 = {{
					owner = {{
						ai = no
						NOT = {{ tag = CHI }}
						any_owned_province = {{ has_building = province_selector }}
					}}
				}}
			}}
			allow = {{
				tag = JAN
			}}
			effect = {{
				any_country = {{
					limit = {{
						ai = no
						any_owned_province = {{ has_building = province_selector }}
					}}
					random_owned = {{
						limit = {{
							has_building = province_selector
						}}
						province_event = {{
							id = 144407
							days = 0
						}}
					}}
				}}
			}}
			
			ai_will_do = {{ factor = 1 }}
		}}
		
	select_prov_CHI = {{
		picture = build_kiel_canal
			potential = {{
				tag = JAN
				META_1 = {{
					owner = {{
						ai = no
						any_owned_province = {{ has_building = province_selector }}
					}}
				}}
			}}
			allow = {{
				tag = JAN
			}}
			effect = {{
				any_country = {{
					limit = {{
						ai = no
						tag = CHI
						any_owned_province = {{ has_building = province_selector }}
					}}
					clr_country_flag = CHI_mode_hub
					clr_country_flag = CHI_mode_food
					clr_country_flag = CHI_mode_sep
					clr_country_flag = CHI_mode_water
					clr_country_flag = CHI_mode_granary
					clr_country_flag = CHI_mode_port
					clr_country_flag = CHI_mode_fleet
					clr_country_flag = CHI_mode_depot
					set_country_flag = CHI_mode_hub
					clr_country_flag = CHI_routed
					clr_country_flag = CHI_pay_fired
					clr_country_flag = CHI_crisis_paid
{routes}
				}}
			}}
			
			ai_will_do = {{ factor = 1 }}
		}}
}}
"""


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
    raw = path.read_bytes().decode("utf-8")
    if "id = 144408" not in raw:
        print("JAN hub already moved")
        return
    a, b = extract_event(raw, 144408)
    text = raw[:a] + raw[b:]
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("removed hub 144408 from JAN", b - a)


def mark_region(rids, flag):
    blocks = []
    for rid in rids:
        blocks.append(
            f"""			random_owned = {{
				limit = {{
					has_province_flag = {flag}
					has_province_flag = CHI_reg_{rid}
				}}
				owner = {{ set_country_flag = CHI_act_{rid} }}
			}}"""
        )
    return "\n".join(blocks)


def build_tax_event(rids):
    mark = mark_region(rids, "CHI_do_tax_cut")
    orlim = mod.gen_region_or(rids)
    stacks = "\n".join(
        f"""			random_owned = {{
				limit = {{
					has_province_flag = CHI_do_tax_cut
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
	title = "CHI_sel_tax_cut"
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
			random_owned = {{
				limit = {{ has_province_flag = CHI_do_tax_cut }}
				province_event = {{ id = 144513 days = 1 }}
			}}
			any_owned = {{ clr_province_flag = CHI_do_tax_cut }}
			clr_country_flag = CHI_tax_stacked
{clr}
		}}
	}}
	option = {{
		name = "CHI_sel_ok"
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
            "# Water + unique river pay stages\n",
            [pays["water"], pays["unique"]],
        ),
        "CHI_crisis_21_water_worker.txt": (
            "# Water workers\n",
            [workers["water"], workers["unique"]],
        ),
        "CHI_crisis_22_water_menus.txt": (
            "# Water choice menus\n",
            [build_water_leaves()],
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
    text2 = re.sub(
        r"CHI_sep_tax_cut = \{[^}]*\}",
        "CHI_sep_tax_cut = {\n\ticon = 9\n}",
        text,
        count=1,
    )
    if text2 != text:
        text = text2
        changed = True
        print("CHI_sep_tax_cut is province marker only")
    extra_bits = []
    if "CHI_food_cd =" not in text:
        extra_bits.append("CHI_food_cd = {\n\ticon = 7\n}")
    if "CHI_sep_revolt_cd =" not in text:
        extra_bits.append(NEW_MODS.strip())
    if "CHI_sep_tax_stack_1 =" not in text:
        extra_bits.append(
            "\n".join(
                f"CHI_sep_tax_stack_{i} = {{\n\ttax_efficiency = -0.04\n\ticon = 9\n}}"
                for i in range(1, TAX_STACKS + 1)
            )
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
    path = ROOT / "common" / "triggered_modifiers.txt"
    text = path.read_bytes().decode("utf-8")
    block = """# CHI_CRISIS_WRAPPER1_START
CHI_fleet_anti_piracy_ready = {
	trigger = {
		tag = CHI
		total_amount_of_ships = 200
	}
	prestige = 0.01
}
# CHI_CRISIS_WRAPPER1_END"""
    start = "# CHI_CRISIS_WRAPPER1_START"
    end = "# CHI_CRISIS_WRAPPER1_END"
    if start in text and end in text:
        text = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            block,
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = text.rstrip() + "\n" + block + "\n"
    path.write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("triggered_modifiers ok")


def patch_loc():
    keys = {
        "CHI_Selector_EvtDesc",
        "CHI_Selector_EvtName",
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
        "CHI_need_port",
        "CHI_need_fleet",
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
            "CHI_inefficient_bureaucracy",
            "CHI_port_anti_piracy",
            "CHI_port_anti_piracy_desc",
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
        loc_line("CHI_Selector_EvtDesc", "Выберите раздел. Дальше откроется только то, что относится к этой провинции."),
        loc_line("CHI_menu_sep", "Борьба с сепаратизмом"),
        loc_line("CHI_menu_food", "Голод и вода"),
        loc_line("CHI_menu_coast", "Побережье и пиратство"),
        loc_line("CHI_menu_misc", "Прочее"),
        loc_line("CHI_menu_misc_title", "Прочее"),
        loc_line(
            "CHI_menu_misc_desc",
            "Склад снабжения и другие хозяйственные действия по провинции.",
        ),
        loc_line("CHI_sel_depot", "Провинциальный склад (500 000)"),
        loc_line("CHI_menu_hydro", "Ирригация и дамбы"),
        loc_line("CHI_menu_sep_title", "Борьба с сепаратизмом"),
        loc_line(
            "CHI_menu_sep_desc",
            "Подкуп лидеров сепаратистов за 500 000 снижает сепаратизм региона на 1 уровень (повтор через год). Снижение налогов на 2 года действует на выбранный регион и каждый раз отдельно снижает доход казны на 4%. Провокация восстания: повстанцы в провинции, после подавления уровень падает, повтор 2 года.",
        ),
        loc_line("CHI_menu_food_title", "Голод и вода"),
        loc_line(
            "CHI_menu_food_desc",
            "Ирригация, дамбы и великий амбар. Ремонт воды только поэтапно: деньги по уровню, повтор около 2.5 лет. Амбар строится из запасов: дерево, цемент, железо и пиломатериалы.",
        ),
        loc_line("CHI_menu_coast_title", "Побережье и пиратство"),
        loc_line("CHI_menu_coast_desc", "Порт ослабляет пиратство только в этой провинции, если оно здесь есть. Флот в 200 кораблей снимает пиратство по стране."),
        loc_line("CHI_sel_back", "Назад"),
        loc_line("CHI_sel_sep_1", "Подавить сепаратизм I"),
        loc_line("CHI_sel_sep_2", "Подавить сепаратизм II"),
        loc_line("CHI_sel_sep_3", "Подавить сепаратизм III"),
        loc_line("CHI_sel_sep_4", "Подавить сепаратизм IV"),
        loc_line("CHI_sel_sep_done", "Сепаратизм"),
        loc_line("CHI_sel_sep_done_desc", "Давление на регион усилено. Сепаратизм снижен на 1 уровень."),
        loc_line("CHI_need_200k", "200000"),
        loc_line("CHI_need_500k", "500000"),
        loc_line("CHI_need_1m", "1000000"),
        loc_line("CHI_need_15m", "1500000"),
        loc_line("CHI_need_2m", "2000000"),
        loc_line("CHI_need_money_desc", "В казне нет нужной суммы."),
        loc_line("CHI_need_goods", "Не хватает ресурсов"),
        loc_line(
            "CHI_need_goods_desc",
            "На складе не хватает товаров для великого амбара: дерево 250, цемент 150, железо 100, пиломатериалы 80.",
        ),
        loc_line("CHI_need_port", "Нужен порт в этой провинции"),
        loc_line("CHI_need_fleet", "Нужен флот в 200 кораблей"),
        loc_line("CHI_sel_sep_none", "В этой провинции нет сепаратизма"),
        loc_line("CHI_sel_sep_wait", "Подавление уже идёт (повтор через год)"),
        loc_line("CHI_sel_not_coast", "Эта провинция не приморская"),
        loc_line("CHI_sel_no_water", "В этой провинции нет проблем с водой"),
        loc_line("CHI_sel_no_famine", "В этой провинции нет голода"),
        loc_line("CHI_sel_no_piracy", "В этой провинции нет пиратства"),
        loc_line("CHI_sel_has_granary", "Великий амбар уже построен"),
        loc_line("CHI_sel_hydro_wait", "Ремонт ирригации уже идёт (повтор ~2.5 года)"),
        loc_line("CHI_sel_granary", "Великий амбар (дерево 250, цемент 150, железо 100, пиломатериалы 80)"),
        loc_line("CHI_menu_granary", "Великий амбар"),
        loc_line("CHI_sel_port_piracy", "Порт против пиратства"),
        loc_line("CHI_sel_fleet_piracy", "Флот против пиратства"),
        loc_line("CHI_sel_water_1", "Ремонт ирригации I (200 000 + дерево 2400, цемент 1200, железо 600, пиломатериалы 600)"),
        loc_line("CHI_sel_water_2", "Ремонт ирригации II (500 000 + дерево 3600, цемент 1800, железо 1200, пиломатериалы 900)"),
        loc_line("CHI_sel_water_3", "Ремонт ирригации III (1 000 000 + дерево 5400, цемент 3000, железо 1800, пиломатериалы 1500)"),
        loc_line("CHI_sel_water_4", "Ремонт ирригации IV (2 000 000 + дерево 7500, цемент 4500, железо 3000, пиломатериалы 2400)"),
        loc_line(
            "CHI_sel_unique_water",
            "Особые речные работы (2 000 000 + дерево 6000, цемент 3600, железо 2400, пиломатериалы 1800)",
        ),
        loc_line("CHI_sel_water_done", "Ирригация"),
        loc_line(
            "CHI_sel_water_done_desc",
            "Работы в регионе закончены. Уровень проблемы с водой снижен на 1. В этом регионе следующий ремонт примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_granary_done", "Великий амбар"),
        loc_line("CHI_sel_granary_done_desc", "Амбар заложен по всему региону из казённых запасов. Голод снижен на 1 уровень."),
        loc_line("CHI_sel_unique_done", "Речные работы"),
        loc_line(
            "CHI_sel_unique_done_desc",
            "Особая речная проблема региона снята. В этом регионе повтор примерно через 2.5 года.",
        ),
        loc_line("CHI_sep_cd", "Подавление сепаратизма"),
        loc_line("CHI_sep_cd_desc", "В регионе уже идёт кампания. Следующий заказ через год."),
        loc_line("CHI_sel_ok", "Принято"),
        loc_line("noloc", " "),
        loc_line("CHI_pay_processing", "Обработка приказа"),
        loc_line("CHI_pay_processing_desc", "Казна и склады проверяют приказ по региону."),
        loc_line("CHI_sel_bribe", "Подкупить лидеров сепаратистов (500 000)"),
        loc_line("CHI_sel_bribe_desc", "Взятки местным вожакам. Сепаратизм региона падает на 1 уровень. Стоимость 500 000. Повтор через год."),
        loc_line("CHI_sel_tax_cut", "Снизить налоги в этом регионе на 2 года"),
        loc_line("CHI_sel_revolt", "Спровоцировать восстание"),
        loc_line("CHI_sel_revolt_wait", "Восстание уже спровоцировано (2 года)"),
        loc_line("CHI_sel_revolt_wait_desc", "В этой провинции уже идёт провокация. Повтор через 2 года."),
        loc_line("CHI_sel_revolt_won", "Восстание подавлено"),
        loc_line("CHI_sel_revolt_won_desc", "Провинция снова под контролем. Сепаратизм региона снижен на 1 уровень."),
        loc_line("CHI_sep_tax_cut", "Налоговая льгота региона"),
        loc_line("CHI_sep_tax_cut_desc", "В этом регионе снижены налоги на 2 года."),
        loc_line("CHI_sep_revolt_cd", "Провокация восстания"),
        loc_line("CHI_sep_revolt_cd_desc", "В этой провинции уже спровоцировано восстание. Повтор через 2 года."),
        loc_line("CHI_sep_uprising", "Спровоцированное восстание"),
        loc_line("CHI_sep_uprising_desc", "Население поднято. После подавления восстания сепаратизм региона снизится."),
        loc_line("CHI_provoked_rebels", "Спровоцированные повстанцы"),
        loc_line("CHI_sep_menu_title", "Сепаратизм региона"),
        loc_line("CHI_sel_sep_none_desc", "В этой провинции нет сепаратизма, который можно снизить."),
        loc_line("CHI_sel_sep_wait_desc", "В регионе уже идёт подавление. Повтор через год."),
        loc_line("CHI_sel_tax_done", "Налоги снижены"),
        loc_line("CHI_sel_tax_done_desc", "Льгота действует 2 года в этом регионе. Казна теряет 4% эффективности налогов. Другие регионы можно освободить отдельно."),
        loc_line("CHI_water_choice_title", "Ирригация региона"),
        loc_line(
            "CHI_water_choice_desc",
            "Поэтапный ремонт снижает проблему воды на 1 уровень только в этом регионе. Повтор здесь примерно через 2.5 года.",
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
            "Особые речные работы снимают уникальную проблему воды в этом регионе. Стоимость: 2 000 000, дерево 6000, цемент 3600, железо 2400, пиломатериалы 1800. При коррупции: 4 000 000. Повтор в этом регионе примерно через 2.5 года.",
        ),
        loc_line("CHI_sel_no_water_desc", "В этой провинции нет проблем с водой."),
        loc_line(
            "CHI_sel_hydro_wait_desc",
            "В этом регионе уже идёт ремонт ирригации. Следующий заказ здесь примерно через 2.5 года. Другие регионы можно чинить отдельно.",
        ),
        loc_line("CHI_famine_choice_title", "Голод региона"),
        loc_line("CHI_famine_choice_desc", "Великий амбар снижает голод на 1 уровень. Стоимость из складов: дерево 250, цемент 150, железо 100, пиломатериалы 80."),
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
        loc_line("CHI_water_canal_silt", "Заиление канала"),
        loc_line("CHI_water_canal_silt_desc", "Судоходство Великого канала подорвано. Снимается особыми речными работами (2 000 000, повтор ~2.5 года)."),
        loc_line("CHI_water_yangtze_nav", "Срыв судоходства Янцзы"),
        loc_line("CHI_water_yangtze_nav_desc", "Речная торговля Янцзы парализована. Снимается особыми речными работами."),
        loc_line("CHI_water_yellow_dikes", "Дамбы Хуанхэ"),
        loc_line("CHI_water_yellow_dikes_desc", "Угроза прорыва Хуанхэ. Снимается особыми речными работами."),
        loc_line("CHI_patchwork_empire", "Лоскутная феодальная империя"),
        loc_line("CHI_inefficient_bureaucracy", "Неэффективная бюрократия"),
        loc_line("CHI_port_anti_piracy", "Портовый надзор"),
        loc_line("CHI_port_anti_piracy_desc", "Порт ослабляет приморский разбой в этой провинции."),
        loc_line(
            "CHI_famine_infra_relief_desc",
            "Если инфраструктура 2-го уровня построена во всех провинциях региона, уровень голода снижается сам. Это не решение селектора.",
        ),
    ]
    bar = mod.bar
    fam_txt = {
        1: "Прирост населения снижен, начинается исход.",
        2: "Сильный удар по приросту и привлекательности.",
        3: "Тяжёлый голод.",
        4: "Катастрофический голод, исход из региона.",
    }
    for i in range(1, 5):
        add.append(
            loc_line(
                f"CHI_famine_{i}_desc",
                f"Проблема с едой.\\nУровень: {bar(i, 4)}\\n{fam_txt[i]}\\n"
                "Снимается великим амбаром (дерево, цемент, железо, пиломатериалы). Уровень голода падает сам, если инфраструктура 2-го уровня построена во всех провинциях региона. Если голод связан с водой - ремонт воды тоже снижает его.",
            )
        )
    roman = {1: "I", 2: "II", 3: "III", 4: "IV"}
    for i in range(1, 5):
        add.append(loc_line(f"CHI_separatism_{i}", f"Сепаратизм {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_separatism_{i}_desc",
                f"Региональный сепаратизм.\\nУровень: {bar(i, 4)}\\nСнимается подкупом лидеров за 500 000 (на 1 уровень, повтор через год).",
            )
        )
        add.append(loc_line(f"CHI_water_{i}", f"Ирригация {roman[i]}"))
        add.append(
            loc_line(
                f"CHI_water_{i}_desc",
                f"Проблемы ирригации и дамб.\\nУровень: {bar(i, 4)}\\nСнимается поэтапным ремонтом (деньги по уровню, повтор ~2.5 года).",
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


def main():
    patch_jan()
    write_crises()
    write_selector()
    patch_modifiers()
    patch_triggered()
    patch_loc()
    print("done")


if __name__ == "__main__":
    main()

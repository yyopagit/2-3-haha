# -*- coding: utf-8 -*-
"""Selector: hub + per-level menus. Money checks live in JAN immediate so CHI
does not see fake income. Need-money leaves show a plain number."""
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


def jan_evt(eid):
    return f"""		JAN = {{ country_event = {{ id = {eid} days = 0 }} }}"""


MODES = [
    "CHI_mode_hub",
    "CHI_mode_food",
    "CHI_mode_sep",
    "CHI_mode_water",
    "CHI_mode_granary",
    "CHI_mode_port",
    "CHI_mode_fleet",
    "CHI_mode_depot",
]


def set_mode(mode):
    flag = f"CHI_mode_{mode}"
    clrs = "\n".join(f"			clr_country_flag = {m}" for m in MODES)
    jan = jan_evt(144440)
    return f"""		owner = {{
{clrs}
			set_country_flag = {flag}
			any_owned = {{ clr_province_flag = CHI_click }}
		}}
		set_province_flag = CHI_click
{jan}"""


def reopen_hub():
    return set_mode("hub")


def route(mode_flag, extra, eid):
    return f"""		random_owned = {{
			limit = {{
				has_province_flag = CHI_click
				owner = {{ has_country_flag = {mode_flag} }}
				owner = {{ NOT = {{ has_country_flag = CHI_routed }} }}
{extra}
			}}
			owner = {{ set_country_flag = CHI_routed }}
			province_event = {{ id = {eid} days = 0 }}
			clr_province_flag = CHI_click
		}}"""


def fallback(mode_flag, eid):
    return f"""		random_owned = {{
			limit = {{
				has_province_flag = CHI_click
				owner = {{ has_country_flag = {mode_flag} }}
				owner = {{ NOT = {{ has_country_flag = CHI_routed }} }}
			}}
			owner = {{ set_country_flag = CHI_routed }}
			province_event = {{ id = {eid} days = 0 }}
			clr_province_flag = CHI_click
		}}"""


def chi_routes(flag, rules, fallback_id):
    parts = [route(flag, extra, eid) for extra, eid in rules]
    parts.append(fallback(flag, fallback_id))
    return "\n".join(parts)


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


def hub_event(eid, sep=False, food=False, coast=False):
    opts = []
    if sep:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_sep"
{set_mode("sep")}
	}}"""
        )
    if food:
        opts.append(
            f"""	option = {{
		name = "CHI_menu_food"
{set_mode("food")}
	}}"""
        )
    if coast:
        opts.append(
            """	option = {
		name = "CHI_menu_coast"
		province_event = { id = 144442 days = 0 }
	}"""
        )
    opts.append(
        f"""	option = {{
		name = "Selector_EvtOptSupplyDepot"
{set_mode("depot")}
	}}"""
    )
    opts.append(
        """	option = {
		name = "Selector_EvtOptCancel"
		province_selector = -1
	}"""
    )
    opts.append(
        """	option = {
		name = "Selector_EvtOptRemAllSelectors"
		owner = {
			any_owned = {
				province_selector = -1
			}
		}
	}"""
    )
    joined = "\n".join(opts)
    return f"""province_event = {{
	title = "CHI_Selector_EvtName"
	desc = "CHI_Selector_EvtDesc"
	id = {eid}
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		owner = {{
			any_owned = {{
				clr_province_flag = CHI_click
			}}
		}}
		set_province_flag = CHI_click
		province_selector = -1
	}}

{joined}
}}
"""


def build_hubs():
    return "\n".join(
        [
            hub_event(144408, sep=True, food=True, coast=True),
            hub_event(144409, sep=True, food=True),
            hub_event(144410, sep=True, coast=True),
            hub_event(144411, food=True, coast=True),
            hub_event(144412, sep=True),
            hub_event(144413, food=True),
            hub_event(144414, coast=True),
            hub_event(144415),
        ]
    )


def build_hub():
    return build_hubs()


def build_submenus():
    back = reopen_hub()
    return f"""
# CHI_MENUS_START
province_event = {{
	title = "CHI_menu_food_title"
	desc = "CHI_menu_food_desc"
	id = 144441
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_menu_hydro"
{set_mode("water")}
	}}
	option = {{
		name = "CHI_sel_granary"
{set_mode("granary")}
	}}
	option = {{
		name = "CHI_sel_back"
{back}
	}}
}}

province_event = {{
	title = "CHI_menu_coast_title"
	desc = "CHI_menu_coast_desc"
	id = 144442
	picture = "Administration"
	is_triggered_only = yes
	option = {{
		name = "CHI_sel_port_piracy"
{set_mode("port")}
	}}
	option = {{
		name = "CHI_sel_fleet_piracy"
{set_mode("fleet")}
	}}
	option = {{
		name = "CHI_sel_back"
{back}
	}}
}}
"""


SEP_MENU_IDS = {}
_sep_extra_ids = iter(
    [144484, 144485, 144486, 144487, 144488, 144489, 144497, 144498, 144499, 144500, 144501, 144502]
)
for _lvl in range(1, 5):
    for _tax in (True, False):
        for _rev in (True, False):
            if _tax and _rev:
                SEP_MENU_IDS[(_lvl, _tax, _rev)] = 144479 + _lvl
            else:
                SEP_MENU_IDS[(_lvl, _tax, _rev)] = next(_sep_extra_ids)


def _sep_limit(level, tax, revolt):
    # tax/revolt True = show the button = province does not have the cooldown yet
    tax_l = (
        "				NOT = { has_province_modifier = CHI_sep_tax_cut }"
        if tax
        else "				has_province_modifier = CHI_sep_tax_cut"
    )
    rev_l = (
        "				NOT = { has_province_modifier = CHI_sep_revolt_cd }"
        if revolt
        else "				has_province_modifier = CHI_sep_revolt_cd"
    )
    return (
        f"				has_province_modifier = CHI_separatism_{level}\n"
        f"{tax_l}\n"
        f"{rev_l}"
    )


SEP_RULES = [
    (_sep_limit(lvl, tax, rev), SEP_MENU_IDS[(lvl, tax, rev)])
    for lvl in range(1, 5)
    for tax in (True, False)
    for rev in (True, False)
]

WATER_RULES = [
    ("				has_province_modifier = CHI_hydro_cd", 144458),
    ("				has_province_modifier = CHI_water_1", 144470),
    ("				has_province_modifier = CHI_water_2", 144471),
    ("				has_province_modifier = CHI_water_3", 144472),
    ("				has_province_modifier = CHI_water_4", 144473),
    (
        """				OR = {
					has_province_modifier = CHI_water_canal_silt
					has_province_modifier = CHI_water_yangtze_nav
					has_province_modifier = CHI_water_yellow_dikes
				}""",
        144474,
    ),
]

GRANARY_RULES = [
    ("				has_province_modifier = CHI_great_granary", 144460),
    (
        """				OR = {
					has_province_modifier = CHI_famine_1
					has_province_modifier = CHI_famine_2
					has_province_modifier = CHI_famine_3
					has_province_modifier = CHI_famine_4
				}""",
        144475,
    ),
]

PORT_RULES = [
    ("				NOT = { is_coastal = yes }", 144461),
    (
        """				is_coastal = yes
				naval_base = 1
				OR = {
					has_province_modifier = CHI_piracy_2
					has_province_modifier = CHI_piracy_3
					has_province_modifier = CHI_piracy_4
				}""",
        144465,
    ),
    (
        """				is_coastal = yes
				NOT = { naval_base = 1 }
				OR = {
					has_province_modifier = CHI_piracy_2
					has_province_modifier = CHI_piracy_3
					has_province_modifier = CHI_piracy_4
				}""",
        144463,
    ),
]

FLEET_RULES = [
    ("				NOT = { is_coastal = yes }", 144461),
    (
        """				is_coastal = yes
				owner = { total_amount_of_ships = 200 }
				OR = {
					has_province_modifier = CHI_piracy_1
					has_province_modifier = CHI_piracy_2
					has_province_modifier = CHI_piracy_3
					has_province_modifier = CHI_piracy_4
				}""",
        144466,
    ),
    (
        """				is_coastal = yes
				owner = { NOT = { total_amount_of_ships = 200 } }
				OR = {
					has_province_modifier = CHI_piracy_1
					has_province_modifier = CHI_piracy_2
					has_province_modifier = CHI_piracy_3
					has_province_modifier = CHI_piracy_4
				}""",
        144464,
    ),
]

DEPOT_RULES = [
    ("				owner = { money = 500000 }", 144467),
]

HUB_RULES = [
    (f"{HAS_SEP}\n{HAS_FOOD}\n{HAS_COAST}", 144408),
    (f"{HAS_SEP}\n{HAS_FOOD}", 144409),
    (f"{HAS_SEP}\n{HAS_COAST}", 144410),
    (f"{HAS_FOOD}\n{HAS_COAST}", 144411),
    (HAS_SEP, 144412),
    (HAS_FOOD, 144413),
    (HAS_COAST, 144414),
]

FOOD_CLICK_RULES = [
    (f"{HAS_WATER}\n{HAS_FAMINE}", 144441),
] + WATER_RULES + GRANARY_RULES


def build_dispatcher():
    body = "\n".join(
        [
            chi_routes("CHI_mode_hub", HUB_RULES, 144415),
            chi_routes("CHI_mode_food", FOOD_CLICK_RULES, 144457),
            chi_routes("CHI_mode_sep", SEP_RULES, 144455),
            chi_routes("CHI_mode_water", WATER_RULES, 144457),
            chi_routes("CHI_mode_granary", GRANARY_RULES, 144459),
            chi_routes("CHI_mode_port", PORT_RULES, 144462),
            chi_routes("CHI_mode_fleet", FLEET_RULES, 144462),
            chi_routes("CHI_mode_depot", DEPOT_RULES, 144451),
        ]
    )
    clr_modes = "\n".join(f"			clr_country_flag = {m}" for m in MODES)
    return f"""
country_event = {{
	id = 144440
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		CHI = {{
			clr_country_flag = CHI_routed
{body}
			any_owned = {{
				clr_province_flag = CHI_click
				clr_province_flag = CHI_open_hub
				clr_province_flag = CHI_open_food
				clr_province_flag = CHI_open_sep
				clr_province_flag = CHI_open_water
				clr_province_flag = CHI_open_granary
				clr_province_flag = CHI_open_port
				clr_province_flag = CHI_open_fleet
				clr_province_flag = CHI_open_depot
			}}
{clr_modes}
			clr_country_flag = CHI_routed
		}}
	}}
	option = {{
		name = "noloc"
	}}
}}
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
				province_event = {{ id = {eid} days = 0 }}
			}}"""


def fire_paid(flag, eid):
    return f"""			random_owned = {{
				limit = {{
					has_province_flag = {flag}
					owner = {{ has_country_flag = CHI_crisis_paid }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {eid} days = 0 }}
			}}"""


def wait_cd(flag, cd_mod, wait_id):
    return f"""			random_owned = {{
				limit = {{
					has_province_flag = {flag}
					has_province_modifier = {cd_mod}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = {wait_id} days = 0 }}
				clr_province_flag = {flag}
			}}"""


def build_pay_dispatcher():
    sep_pay = "\n".join(
        [
            pay_flag("CHI_do_sep_pay", 500000, 1000000, "CHI_separatism_1"),
            pay_flag("CHI_do_sep_pay", 1000000, 2000000, "CHI_separatism_2"),
            pay_flag("CHI_do_sep_pay", 1500000, 3000000, "CHI_separatism_3"),
            pay_flag("CHI_do_sep_pay", 2000000, 4000000, "CHI_separatism_4"),
        ]
    )
    water_pay = "\n".join(
        [
            pay_flag("CHI_do_water_pay", 200000, 400000, "CHI_water_1"),
            pay_flag("CHI_do_water_pay", 500000, 1000000, "CHI_water_2"),
            pay_flag("CHI_do_water_pay", 1000000, 2000000, "CHI_water_3"),
            pay_flag("CHI_do_water_pay", 2000000, 4000000, "CHI_water_4"),
        ]
    )
    granary_pay = pay_flag("CHI_do_granary_pay", 2000000, 4000000)
    uniq_pay = pay_flag("CHI_do_uniq_pay", 2000000, 4000000)
    sep_need = "\n".join(
        [
            fire_need("CHI_do_sep_pay", "CHI_separatism_1", 144451),
            fire_need("CHI_do_sep_pay", "CHI_separatism_2", 144452),
            fire_need("CHI_do_sep_pay", "CHI_separatism_3", 144453),
            fire_need("CHI_do_sep_pay", "CHI_separatism_4", 144454),
        ]
    )
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
    def stage(eid, next_eid, body, final=False):
        clr_tail = "\n\t\t\tclr_country_flag = CHI_pay_fired" if final else ""
        chain = f"\n\t\tcountry_event = {{ id = {next_eid} days = 0 }}" if next_eid else ""
        return f"""
country_event = {{
	id = {eid}
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		CHI = {{
{body}{clr_tail}
		}}
{chain}
	}}
	option = {{
		name = "noloc"
	}}
}}
"""

    stage_sep = f"""			clr_country_flag = CHI_crisis_paid
			clr_country_flag = CHI_pay_fired
			clr_country_flag = CHI_pay_part
{wait_cd("CHI_do_sep_pay", "CHI_sep_cd", 144456)}
{sep_pay}
{fire_paid("CHI_do_sep_pay", 144437)}
{sep_need}
			any_owned = {{ clr_province_flag = CHI_do_sep_pay }}"""

    stage_water = f"""{wait_cd("CHI_do_water_pay", "CHI_hydro_cd", 144458)}
{water_pay}
{fire_paid("CHI_do_water_pay", 144431)}
{water_need}
			any_owned = {{ clr_province_flag = CHI_do_water_pay }}"""

    stage_uniq = f"""{wait_cd("CHI_do_uniq_pay", "CHI_hydro_cd", 144458)}
{uniq_pay}
{fire_paid("CHI_do_uniq_pay", 144433)}
{uniq_need}
			any_owned = {{ clr_province_flag = CHI_do_uniq_pay }}"""

    stage_granary_revolt = f"""{granary_pay}
{fire_paid("CHI_do_granary_pay", 144432)}
			random_owned = {{
				limit = {{
					has_province_flag = CHI_do_granary_pay
					owner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}
					owner = {{ NOT = {{ has_country_flag = CHI_pay_fired }} }}
				}}
				owner = {{ set_country_flag = CHI_pay_fired }}
				province_event = {{ id = 144454 days = 0 }}
			}}
			any_owned = {{ clr_province_flag = CHI_do_granary_pay }}"""

    return (
        stage(144493, 144494, stage_sep)
        + stage(144494, 144495, stage_water)
        + stage(144495, 144496, stage_uniq)
        + stage(144496, None, stage_granary_revolt, final=True)
    )


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
		name = "{title}"
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


def pay_click(flag):
    jan = jan_evt(144493)
    return f"""		set_province_flag = {flag}
{jan}"""


def sep_methods(eid, title, tax=True, revolt=True):
    jan = jan_evt(144493)
    opts = [
        f"""	option = {{
		name = "{title}"
		set_province_flag = CHI_do_sep_pay
{jan}
	}}"""
    ]
    if tax:
        opts.append(
            f"""	option = {{
		name = "CHI_sel_tax_cut"
		add_province_modifier = {{ name = CHI_sep_tax_cut duration = 1825 }}
		owner = {{
			add_country_modifier = {{ name = CHI_sep_tax_cut duration = 1825 }}
		}}
{reopen_hub()}
	}}"""
        )
    if revolt:
        opts.append(
            f"""	option = {{
		name = "CHI_sel_revolt"
		any_pop = {{
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
			ideology = conservative
		}}
		add_province_modifier = {{ name = CHI_sep_revolt_cd duration = 1825 }}
		add_province_modifier = {{ name = CHI_sep_uprising duration = 180 }}
		set_province_flag = CHI_sep_revolt_pending
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
    return f"""province_event = {{
	id = {eid}
	title = "{title}"
	desc = "CHI_menu_sep_desc"
	picture = "Administration"
	is_triggered_only = yes
{joined}
}}
"""


def build_leaves():
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
    parts = [
        notice(144450, "CHI_need_200k", "CHI_need_money_desc", "hub"),
        notice(144451, "CHI_need_500k", "CHI_need_money_desc", "hub"),
        notice(144452, "CHI_need_1m", "CHI_need_money_desc", "hub"),
        notice(144453, "CHI_need_15m", "CHI_need_money_desc", "hub"),
        notice(144454, "CHI_need_2m", "CHI_need_money_desc", "hub"),
        notice(144455, "CHI_sel_sep_none", "CHI_sel_sep_none", "hub"),
        notice(144456, "CHI_sel_sep_wait", "CHI_sel_sep_wait", "hub"),
        notice(144457, "CHI_sel_no_water", "CHI_sel_no_water", "hub"),
        notice(144458, "CHI_sel_hydro_wait", "CHI_sel_hydro_wait", "hub"),
        notice(144459, "CHI_sel_no_famine", "CHI_sel_no_famine", "hub"),
        notice(144460, "CHI_sel_has_granary", "CHI_sel_has_granary", "hub"),
        notice(144461, "CHI_sel_not_coast", "CHI_sel_not_coast", "hub"),
        notice(144462, "CHI_sel_no_piracy", "CHI_sel_no_piracy", "hub"),
        notice(144463, "CHI_need_port", "CHI_need_port", "hub"),
        notice(144464, "CHI_need_fleet", "CHI_need_fleet", "hub"),
        notice(144490, "CHI_sel_revolt_wait", "CHI_sel_revolt_wait", "hub"),
        notice(144491, "CHI_sel_revolt_won", "CHI_sel_revolt_won_desc", "hub"),
        confirm(144465, "CHI_sel_port_piracy", "CHI_menu_coast_desc", "CHI_sel_port_piracy", port_fx, "hub"),
        confirm(144466, "CHI_sel_fleet_piracy", "CHI_menu_coast_desc", "CHI_sel_fleet_piracy", fleet_fx, "hub"),
        confirm(144467, "Selector_EvtOptSupplyDepot", "Selector_EvtDesc", "Selector_EvtOptSupplyDepot", depot_fx, "hub"),
        confirm(144470, "CHI_sel_water_1", "CHI_menu_food_desc", "CHI_sel_water_1", pay_click("CHI_do_water_pay"), "hub"),
        confirm(144471, "CHI_sel_water_2", "CHI_menu_food_desc", "CHI_sel_water_2", pay_click("CHI_do_water_pay"), "hub"),
        confirm(144472, "CHI_sel_water_3", "CHI_menu_food_desc", "CHI_sel_water_3", pay_click("CHI_do_water_pay"), "hub"),
        confirm(144473, "CHI_sel_water_4", "CHI_menu_food_desc", "CHI_sel_water_4", pay_click("CHI_do_water_pay"), "hub"),
        confirm(144474, "CHI_sel_unique_water", "CHI_menu_food_desc", "CHI_sel_unique_water", pay_click("CHI_do_uniq_pay"), "hub"),
        confirm(144475, "CHI_sel_granary", "CHI_menu_food_desc", "CHI_sel_granary", pay_click("CHI_do_granary_pay"), "hub"),
    ]
    for lvl, tax, rev in (
        (lvl, tax, rev)
        for lvl in range(1, 5)
        for tax in (True, False)
        for rev in (True, False)
    ):
        parts.append(
            sep_methods(
                SEP_MENU_IDS[(lvl, tax, rev)],
                f"CHI_sel_sep_{lvl}",
                tax=tax,
                revolt=rev,
            )
        )
    return "\n".join(parts)


def build_menus():
    return (
        build_hubs()
        + "\n"
        + build_dispatcher()
        + build_pay_dispatcher()
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
	picture = "Administration"
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
    marks = []
    for rid in rids:
        marks.append(
            f"""			any_owned = {{
				limit = {{
					has_province_flag = CHI_sep_revolt_won
					has_province_flag = CHI_reg_{rid}
				}}
				owner = {{ set_country_flag = CHI_act_{rid} }}
			}}"""
        )
    sep_drop = mod.water_drop_block(rids, indent="\t\t\t").replace("CHI_water_", "CHI_separatism_")
    clr = mod.gen_clr_act(rids)
    joined = "\n".join(marks)
    return f"""
# CHI_REVOLT_PULSE_START
country_event = {{
	id = 144492
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	trigger = {{ tag = JAN }}
	mean_time_to_happen = {{ days = 15 }}
	immediate = {{
		CHI = {{
			any_owned = {{
				limit = {{
					has_province_flag = CHI_sep_revolt_pending
					NOT = {{ has_province_modifier = CHI_sep_uprising }}
					controlled_by = owner
				}}
				set_province_flag = CHI_sep_revolt_won
				clr_province_flag = CHI_sep_revolt_pending
			}}
{joined}
{sep_drop}
			random_owned = {{
				limit = {{ has_province_flag = CHI_sep_revolt_won }}
				province_event = {{ id = 144491 days = 0 }}
			}}
			any_owned = {{ clr_province_flag = CHI_sep_revolt_won }}
{clr}
		}}
	}}
	option = {{
		name = "noloc"
	}}
}}
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
    joined = "\n".join(blocks)
    return f"""
# CHI_REGION_FLAGS_START
country_event = {{
	id = 144405
	title = "noloc"
	desc = "noloc"
	picture = "Administration"
	is_triggered_only = yes
	immediate = {{
		CHI = {{
{joined}
{pirate_drop}
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
	picture = "Administration"
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


def write_crises():
    rids = mod.rids_used()
    workers = mod.build_workers(rids)
    path = ROOT / "events" / "CHI_crises.txt"
    body = (
        "# China crisis workers + menus\n"
        + workers
        + "\n"
        + build_menus()
        + "\n"
        + build_infra_pulse(rids)
        + "\n"
        + build_revolt_pulse(rids)
        + "\n"
        + build_region_flag_event()
        + "\n"
        + build_click_event()
    )
    path.write_bytes(body.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8"))
    print("CHI_crises.txt", path.stat().st_size)


NEW_MODS = """
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
"""


def patch_modifiers():
    path = ROOT / "common" / "event_modifiers.txt"
    text = path.read_bytes().decode("utf-8")
    changed = False
    old_tax = "CHI_sep_tax_cut = {\r\n\ticon = 9\r\n}"
    new_tax = "CHI_sep_tax_cut = {\r\n\ttax_efficiency = -0.04\r\n\ticon = 9\r\n}"
    if old_tax not in text:
        old_tax = "CHI_sep_tax_cut = {\n\ticon = 9\n}"
        new_tax = "CHI_sep_tax_cut = {\n\ttax_efficiency = -0.04\n\ticon = 9\n}"
    if old_tax in text:
        text = text.replace(old_tax, new_tax, 1)
        changed = True
        print("CHI_sep_tax_cut tax_efficiency added")
    if "CHI_sep_tax_cut =" not in text:
        end = "# CHI_CRISIS_WRAPPER1_END"
        if end not in text:
            raise SystemExit("wrapper end not found")
        text = text.replace(end, NEW_MODS.strip() + "\n" + end, 1)
        changed = True
        print("sep tax/revolt mods added")
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
        loc_line("CHI_menu_hydro", "Гидротехника"),
        loc_line("CHI_menu_sep_title", "Борьба с сепаратизмом"),
        loc_line(
            "CHI_menu_sep_desc",
            "Подавление за деньги снижает сепаратизм региона на 1 уровень (коррупция x2, повтор через год). Снижение налогов на 5 лет даёт -4% к эффективности налогообложения. Провокация восстания: в провинции поднимаются повстанцы; после подавления уровень падает, повтор через 5 лет.",
        ),
        loc_line("CHI_menu_food_title", "Голод и вода"),
        loc_line("CHI_menu_food_desc", "Гидротехника и великий амбар. Уровень голода снижается сам, если инфраструктура 2-го уровня построена во всех провинциях региона."),
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
        loc_line("CHI_need_port", "Нужен порт в этой провинции"),
        loc_line("CHI_need_fleet", "Нужен флот в 200 кораблей"),
        loc_line("CHI_sel_sep_none", "В этой провинции нет сепаратизма"),
        loc_line("CHI_sel_sep_wait", "Подавление уже идёт (повтор через год)"),
        loc_line("CHI_sel_not_coast", "Эта провинция не приморская"),
        loc_line("CHI_sel_no_water", "В этой провинции нет проблем с водой"),
        loc_line("CHI_sel_no_famine", "В этой провинции нет голода"),
        loc_line("CHI_sel_no_piracy", "В этой провинции нет пиратства"),
        loc_line("CHI_sel_has_granary", "Великий амбар уже построен"),
        loc_line("CHI_sel_hydro_wait", "Гидротехнические работы уже идут (повтор через год)"),
        loc_line("CHI_sel_granary", "Великий амбар"),
        loc_line("CHI_sel_port_piracy", "Порт против пиратства"),
        loc_line("CHI_sel_fleet_piracy", "Флот против пиратства"),
        loc_line("CHI_sel_water_1", "Починить гидротехнику I"),
        loc_line("CHI_sel_water_2", "Починить гидротехнику II"),
        loc_line("CHI_sel_water_3", "Починить гидротехнику III"),
        loc_line("CHI_sel_water_4", "Починить гидротехнику IV"),
        loc_line("CHI_sel_unique_water", "Снять особую речную проблему"),
        loc_line("CHI_sel_water_done", "Гидротехника"),
        loc_line("CHI_sel_water_done_desc", "Работы в регионе начаты. Уровень проблемы с водой снижен на 1. Повторный ремонт через год."),
        loc_line("CHI_sel_granary_done", "Великий амбар"),
        loc_line("CHI_sel_granary_done_desc", "Амбар заложен по всему региону. Голод снижен на 1 уровень."),
        loc_line("CHI_sel_unique_done", "Речные работы"),
        loc_line("CHI_sel_unique_done_desc", "Особая речная проблема региона снята. Повтор через год."),
        loc_line("CHI_sep_cd", "Подавление сепаратизма"),
        loc_line("CHI_sep_cd_desc", "В регионе уже идёт кампания. Следующий заказ через год."),
        loc_line("CHI_sel_ok", "Принято"),
        loc_line("noloc", "."),
        loc_line("CHI_sel_tax_cut", "Снизить налоги на 5 лет"),
        loc_line("CHI_sel_revolt", "Спровоцировать восстание"),
        loc_line("CHI_sel_revolt_wait", "Восстание уже спровоцировано (5 лет)"),
        loc_line("CHI_sel_revolt_won", "Восстание подавлено"),
        loc_line("CHI_sel_revolt_won_desc", "Провинция снова под контролем. Сепаратизм региона снижен на 1 уровень."),
        loc_line("CHI_sep_tax_cut", "Налоговая льгота"),
        loc_line("CHI_sep_tax_cut_desc", "Налоги снижены на 5 лет. Эффективность налогообложения -4%."),
        loc_line("CHI_sep_revolt_cd", "Провокация восстания"),
        loc_line("CHI_sep_revolt_cd_desc", "В этой провинции уже спровоцировано восстание. Повтор через 5 лет."),
        loc_line("CHI_sep_uprising", "Спровоцированное восстание"),
        loc_line("CHI_sep_uprising_desc", "Население поднято. После подавления восстания сепаратизм региона снизится."),
        loc_line("CHI_provoked_rebels", "Спровоцированные повстанцы"),
        loc_line("CHI_sep_tax_cut_nation", "Налоговые льготы провинциям"),
        loc_line("CHI_sep_tax_cut_nation_desc", "В провинциях действуют налоговые льготы. Эффективность налогообложения -4%."),
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
                "Снимается амбаром. Уровень голода падает сам, если инфраструктура 2-го уровня построена во всех провинциях региона. Если голод связан с водой - ремонт воды тоже снижает его.",
            )
        )
    body = "".join(kept)
    if not body.endswith("\n"):
        body += "\r\n"
    out = (body + "".join(add)).encode("cp1251")
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

# -*- coding: utf-8 -*-
"""One-shot patch: apply water pay fixes to recovered menus."""
from pathlib import Path

src = Path(__file__).parent / "_chi_crisis_menus_recovered.py"
dst = Path(__file__).parent / "_chi_crisis_menus.py"
text = src.read_text(encoding="utf-8")

pay_goods_fn = '''
def pay_goods_flag(flag, amount, corrupt_amount, costs, level_mod=None, indent="\\t\\t"):
    """Money + goods pay blocks (Vic2 max 2M per money line)."""
    mod_line = f"{indent}\\t\\thas_province_modifier = {level_mod}\\n" if level_mod else ""
    gt = _goods_trigger(costs, indent + "\\t\\t")
    gp = _goods_pay(costs, indent + "\\t\\t")

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
            goods_lim = gt if is_last else ""
            goods_body = gp if is_last else ""
            if i == 0:
                extra = (
                    f"{mod_line}{indent}\\t\\towner = {{\\n"
                    f"{indent}\\t\\t\\t{cor}\\n"
                    f"{indent}\\t\\t\\tmoney = {n}\\n"
                    f"{goods_lim}\\n"
                    f"{indent}\\t\\t}}\\n"
                    f"{indent}\\t\\towner = {{ NOT = {{ has_country_flag = CHI_crisis_paid }} }}\\n"
                )
                if not is_last:
                    extra += f"{indent}\\t\\towner = {{ NOT = {{ has_country_flag = CHI_pay_part }} }}\\n"
            else:
                extra = (
                    f"{mod_line}{indent}\\t\\towner = {{ has_country_flag = CHI_pay_part }}\\n"
                    f"{indent}\\t\\towner = {{\\n"
                    f"{indent}\\t\\t\\t{cor}\\n"
                    f"{indent}\\t\\t\\tmoney = {n}\\n"
                    f"{goods_lim}\\n"
                    f"{indent}\\t\\t}}\\n"
                )
            if is_last:
                body = f"{indent}\\t\\tmoney = -{n}\\n{goods_body}\\n{indent}\\t\\tset_country_flag = CHI_crisis_paid"
                if i > 0:
                    body += f"\\n{indent}\\t\\tclr_country_flag = CHI_pay_part"
            else:
                body = f"{indent}\\t\\tmoney = -{n}\\n{indent}\\t\\tset_country_flag = CHI_pay_part"
            blocks.append(
                f"""{indent}random_owned = {{
{indent}\\tlimit = {{
{indent}\\t\\thas_province_flag = {flag}
{extra}{indent}\\t}}
{indent}\\towner = {{
{body}
{indent}\\t}}
{indent}}}"""
            )
        return "\\n".join(blocks)

    return one_pay(amount, False) + "\\n" + one_pay(corrupt_amount, True)


def water_level_pay(level, costs):
    return pay_goods_flag(
        "CHI_do_water_pay",
        costs["money"],
        costs["corrupt"],
        costs,
        f"CHI_water_{level}",
    )


def unique_goods_pay():
    return pay_goods_flag(
        "CHI_do_uniq_pay",
        UNIQUE_REPAIR["money"],
        UNIQUE_REPAIR["corrupt"],
        UNIQUE_REPAIR,
    )

'''

old_branch = text.split("def _water_pay_branch(corrupt, costs, worker_id):", 1)[0]
rest = text.split("def _water_pay_branch(corrupt, costs, worker_id):", 1)[1]
rest = rest.split("def water_choice(eid, step_name, costs, worker_id=144431):", 1)[1]
rest = rest.split("def build_water_leaves():", 1)[1]

new_water_choice = '''def water_choice(eid, desc_key, step_name, flag, pay_id):
    return f"""province_event = {{
\\tid = {eid}
\\ttitle = "CHI_water_choice_title"
\\tdesc = "{desc_key}"
\\tpicture = "Administration"
\\tis_triggered_only = yes
\\toption = {{
\\t\\tname = "{step_name}"
\\t\\ttrigger = {{
\\t\\t\\tNOT = {{ has_province_modifier = CHI_hydro_cd }}
\\t\\t}}
{pay_click(flag, pay_id)}
\\t}}
\\toption = {{
\\t\\tname = "CHI_sel_back"
{reopen_hub()}
\\t}}
}}
"""

'''

text = old_branch + pay_goods_fn + new_water_choice + "def build_water_leaves():" + rest

text = text.replace(
    """    water_pay = "\\n".join(
        [
            pay_flag("CHI_do_water_pay", 200000, 400000, "CHI_water_1"),
            pay_flag("CHI_do_water_pay", 500000, 1000000, "CHI_water_2"),
            pay_flag("CHI_do_water_pay", 1000000, 2000000, "CHI_water_3"),
            pay_flag("CHI_do_water_pay", 2000000, 4000000, "CHI_water_4"),
        ]
    )
    uniq_pay = pay_flag("CHI_do_uniq_pay", 2000000, 4000000)""",
    """    water_pay = "\\n".join(
        [
            water_level_pay(1, WATER_REPAIR[1]),
            water_level_pay(2, WATER_REPAIR[2]),
            water_level_pay(3, WATER_REPAIR[3]),
            water_level_pay(4, WATER_REPAIR[4]),
        ]
    )
    uniq_pay = unique_goods_pay()""",
)

text = text.replace(
    """            water_choice(144470, "CHI_sel_water_1", WATER_REPAIR[1]),
            water_choice(144471, "CHI_sel_water_2", WATER_REPAIR[2]),
            water_choice(144472, "CHI_sel_water_3", WATER_REPAIR[3]),
            water_choice(144473, "CHI_sel_water_4", WATER_REPAIR[4]),
            water_choice(144474, "CHI_sel_unique_water", UNIQUE_REPAIR, worker_id=144433),""",
    """            water_choice(144470, "CHI_water_choice_1_desc", "CHI_sel_water_1", "CHI_do_water_pay", 144494),
            water_choice(144471, "CHI_water_choice_2_desc", "CHI_sel_water_2", "CHI_do_water_pay", 144494),
            water_choice(144472, "CHI_water_choice_3_desc", "CHI_sel_water_3", "CHI_do_water_pay", 144494),
            water_choice(144473, "CHI_water_choice_4_desc", "CHI_sel_water_4", "CHI_do_water_pay", 144494),
            water_choice(144474, "CHI_water_choice_unique_desc", "CHI_sel_unique_water", "CHI_do_uniq_pay", 144495),""",
)

text = text.replace(
    """        "CHI_water.txt": (
            "# China water / unique river: workers + menus (pay is on options)\\n",
            [
                workers["water"],
                workers["unique"],
                build_water_leaves(),
            ],
        ),""",
    """        "CHI_water.txt": (
            "# China water / unique river: pay, workers, menus\\n",
            [
                pays["water"],
                pays["unique"],
                workers["water"],
                workers["unique"],
                build_water_leaves(),
            ],
        ),""",
)

if '"CHI_water_choice_1_desc"' not in text:
    text = text.replace(
        '        "CHI_water_choice_title",\n        "CHI_water_choice_desc",',
        '        "CHI_water_choice_title",\n        "CHI_water_choice_desc",\n        "CHI_water_choice_1_desc",\n        "CHI_water_choice_2_desc",\n        "CHI_water_choice_3_desc",\n        "CHI_water_choice_4_desc",\n        "CHI_water_choice_unique_desc",',
    )
    text = text.replace(
        '        loc_line("CHI_water_choice_title", "Ирригация региона"),\n        loc_line(\n            "CHI_water_choice_desc",',
        '        loc_line("CHI_water_choice_title", "Ирригация региона"),\n        loc_line("CHI_water_choice_1_desc", "Уровень I. Стоимость на кнопке."),\n        loc_line("CHI_water_choice_2_desc", "Уровень II. Стоимость на кнопке."),\n        loc_line("CHI_water_choice_3_desc", "Уровень III. Стоимость на кнопке."),\n        loc_line("CHI_water_choice_4_desc", "Уровень IV. Стоимость на кнопке."),\n        loc_line("CHI_water_choice_unique_desc", "Особая речная проблема. Стоимость на кнопке."),\n        loc_line(\n            "CHI_water_choice_desc",',
    )

dst.write_text(text, encoding="utf-8", newline="\n")
print("written", dst, "lines", text.count("\n") + 1)

# -*- coding: utf-8 -*-
"""Color money/goods in CHI construction event loc. Does not rewrite event txt via menus.py."""
from pathlib import Path

ROOT = Path(r"c:\Games\Vic2LV2\Victoria 2\mod\5")
CSV = ROOT / "localisation" / "a.csv"

WATER = {
    1: {"money": 200000, "corrupt": 400000, "timber": 2400, "cement": 1200, "iron": 600, "lumber": 600},
    2: {"money": 500000, "corrupt": 1000000, "timber": 3600, "cement": 1800, "iron": 1200, "lumber": 900},
    3: {"money": 1000000, "corrupt": 2000000, "timber": 5400, "cement": 3000, "iron": 1800, "lumber": 1500},
    4: {"money": 2000000, "corrupt": 4000000, "timber": 7500, "cement": 4500, "iron": 3000, "lumber": 2400},
}
CANAL = {"money": 1000000, "corrupt": 2000000, "timber": 3000, "cement": 1500, "iron": 1000, "lumber": 800}
YANG = {"money": 1000000, "corrupt": 2000000, "timber": 2500, "cement": 1200, "iron": 1500, "lumber": 700}
YELL = {
    "money": 1000000,
    "corrupt": 1000000,
    "timber": 12000,
    "lumber": 6000,
    "cement": 10000,
    "iron": 8000,
    "steel": 4000,
    "coal": 5000,
}
GRAN = {"timber": 250, "cement": 150, "iron": 100, "lumber": 80}
UNIQ = {"money": 2000000, "corrupt": 4000000, "timber": 6000, "cement": 3600, "iron": 2400, "lumber": 1800}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
ORDER = (
    ("timber", "дерево"),
    ("lumber", "пиломатериалы"),
    ("cement", "цемент"),
    ("iron", "железо"),
    ("steel", "сталь"),
    ("coal", "уголь"),
)


def fmt(n):
    return f"{int(n):,}".replace(",", " ")


def Y(n):
    return f"§Y{fmt(n)}§W"


def G(n):
    return f"§G{fmt(n)}§W"


def R(n):
    return f"§R{fmt(n)}§W"


def goods_line(c):
    return ", ".join(f"{ru} {G(c[k])}" for k, ru in ORDER if k in c)


def goods_block(c):
    return "\n".join(f"{ru} {G(c[k])}" for k, ru in ORDER if k in c)


def cost_block(c):
    lines = [f"Казна: {Y(c['money'])}"]
    cor = c.get("corrupt")
    if cor is not None:
        if cor == c["money"]:
            lines.append("Коррупция эту цену не меняет.")
        else:
            lines.append(f"При коррупции казна: {R(cor)} (вдвое).")
    gb = goods_block(c)
    if gb:
        lines.append("Склад:")
        lines.append(gb)
    return "\n".join(lines)


def loc(key, text):
    text = text.replace("\r\n", "\n").replace("\n", "\\n")
    return f"{key};{text};X;X;X;X;X;X"


def rows():
    out = []
    out.append(
        loc(
            "CHI_Selector_EvtDesc",
            "Только бедствия этой провинции.\n"
            "§YСепаратизм, вода, голод§W - весь регион.\n"
            "§YПорт§W - только сюда.\n\n"
            "При высокой коррупции денежные цены §Rвдвое§W.",
        )
    )
    out.append(
        loc(
            "Selector_EvtDesc",
            f"Склад снабжения: {Y(500000)}, только в этой провинции. "
            f"Старый склад в других провинциях этой страны снимается. "
            f"Без {Y(500000)} в казне склад ставить нельзя.",
        )
    )
    out.append(loc("Selector_EvtOptSupplyDepot", f"Снабженческий склад ({Y(500000)})"))
    out.append(
        loc(
            "CHI_menu_misc_desc",
            f"Склад снабжения: {Y(500000)}, только в этой провинции. "
            f"Старый склад в других провинциях снимается. "
            f"Если в казне меньше {Y(500000)}, кнопки склада не будет.",
        )
    )
    out.append(loc("CHI_sel_depot", f"Провинциальный склад  ·  {Y(500000)}"))
    out.append(
        loc(
            "CHI_menu_river_desc",
            "Проекты на весь регион. Один заказ закрывает все провинции штата.\n\n"
            f"§YКанал§W - ил Великого канала\n{cost_block(CANAL)}\n\n"
            f"§YЯнцзы§W - фарватер\n{cost_block(YANG)}\n\n"
            f"§YХуанхэ§W - дамбы (Южный Чжили, Хэнань, Нанкин, Шаньдун, Циндао)\n"
            f"{cost_block(YELL)}\n"
            "Прогресс дамб - карточка страны «Дамбы Хуанхэ N/5». С 1845 непройденное снимается решением без награды.",
        )
    )
    out.append(
        loc(
            "CHI_menu_sep_desc",
            f"§YПодкуп§W - сепаратизм региона -1. Казна: {Y(500000)}. При коррупции {R(1000000)}. Повтор год.\n"
            "§YНалог§W - льгота региону на 2 года. Казна -§Y4%§W эффективности за каждый такой регион (до 20).\n"
            "§YПровокация§W - только эта провинция. Через полгода при контроле Китая сепаратизм региона -1.",
        )
    )
    out.append(
        loc(
            "CHI_menu_food_desc",
            "Вода и еда лечатся на весь регион.\n\n"
            "§YИрригация§W - вода -1 уровень. Повтор около 2.5 лет. Цена зависит от ступени (смотри страницу заказа).\n"
            f"§YАмбар§W - голод -1, сельское хозяйство +5%. Склад: {goods_line(GRAN)}. Повтор 2 года.\n"
            "§YХуанхэ§W - дамбы селектором по 5 регионам. Прогресс на карточке страны.",
        )
    )
    out.append(loc("CHI_need_200k", Y(200000)))
    out.append(loc("CHI_need_500k", Y(500000)))
    out.append(loc("CHI_need_1m", Y(1000000)))
    out.append(loc("CHI_need_15m", Y(1500000)))
    out.append(loc("CHI_need_2m", Y(2000000)))
    out.append(
        loc(
            "CHI_need_money_desc",
            f"В казне нет нужной суммы. При высокой коррупции денежная цена §Rвдвое§W. "
            f"Суммы больше {Y(2000000)} игра принимает только кусками по {Y(2000000)}.",
        )
    )
    out.append(
        loc(
            "CHI_need_goods_desc",
            f"На складе не хватает товаров.\nАмбар: {goods_line(GRAN)}.\n"
            "Ирригация и реки - объёмы больше, они написаны на странице заказа.",
        )
    )
    out.append(loc("CHI_need_fleet", "Флота меньше §Y200§W кораблей"))
    out.append(
        loc(
            "CHI_need_fleet_desc",
            "Нужно не меньше §Y200§W кораблей у страны. Тогда флот снимет пиратство со всех провинций. "
            "Текущее число кораблей это окно показать не может - смотрите флот в интерфейсе страны.",
        )
    )
    out.append(loc("CHI_sel_fleet_piracy", "Флот §Y200+§W: снять пиратство в стране"))
    out.append(
        loc(
            "CHI_sel_fleet_piracy_desc",
            "В строю не меньше §Y200§W кораблей. Нажмите Понятно: пиратство снимется со всех провинций страны. "
            "Откатить нельзя. Точное число кораблей окно показать не может.",
        )
    )
    out.append(loc("CHI_depot_title", f"Склад снабжения: {Y(500000)}"))
    out.append(
        loc(
            "CHI_depot_desc",
            f"Склад ставится только в этой провинции.\nКазна: {Y(500000)}.\n"
            "Старый склад в других провинциях снимается.",
        )
    )
    out.append(loc("CHI_sel_granary", "Великий амбар  ·  склад"))
    for i in range(1, 5):
        out.append(loc(f"CHI_sel_water_{i}", f"Ирригация {ROMAN[i]}  ·  {Y(WATER[i]['money'])}"))
    out.append(loc("CHI_sel_canal_silt", f"Очистка канала  ·  {Y(CANAL['money'])}"))
    out.append(loc("CHI_sel_yangtze_nav", f"Фарватер Янцзы  ·  {Y(YANG['money'])}"))
    out.append(loc("CHI_sel_yellow_dikes", f"Дамбы Хуанхэ  ·  {Y(YELL['money'])}"))
    out.append(
        loc(
            "CHI_pay_processing_desc",
            "Казна и склады проверяют приказ.\nЕсли денег или товаров не хватает, списывать не будут.",
        )
    )
    out.append(loc("CHI_pay_granary", f"Амбар: {goods_line(GRAN)}"))
    out.append(
        loc(
            "CHI_pay_granary_desc",
            "§YВеликий амбар§W. Денег не берёт. Если товаров не хватает, списывать не будут.\n\n"
            f"Склад: {goods_line(GRAN)}.",
        )
    )
    out.append(loc("CHI_pay_bribe", f"Подкуп: казна {Y(500000)}"))
    out.append(
        loc(
            "CHI_pay_bribe_desc",
            "§YПодкуп§W местных вожаков. Если денег не хватает, списывать не будут.\n\n"
            f"Казна: {Y(500000)}.\nПри коррупции: {R(1000000)} (вдвое).",
        )
    )
    out.append(loc("CHI_pay_canal", f"Канал: казна {Y(CANAL['money'])}"))
    out.append(
        loc(
            "CHI_pay_canal_desc",
            "§YОчистка Великого канала§W от ила в этом регионе. Если казны или товаров не хватает, списывать не будут.\n\n"
            + cost_block(CANAL),
        )
    )
    out.append(loc("CHI_pay_yangtze", f"Янцзы: казна {Y(YANG['money'])}"))
    out.append(
        loc(
            "CHI_pay_yangtze_desc",
            "§YФарватер Янцзы§W в этом регионе. Если казны или товаров не хватает, списывать не будут.\n\n"
            + cost_block(YANG),
        )
    )
    out.append(loc("CHI_pay_yellow", f"Дамбы Хуанхэ: казна {Y(YELL['money'])}"))
    out.append(
        loc(
            "CHI_pay_yellow_desc",
            "§YДамбы Хуанхэ§W на весь регион. Если казны или товаров не хватает, списывать не будут.\n\n"
            f"{cost_block(YELL)}\n\n"
            "Таких регионов пять. Успех всех пяти до 1845 - бонус стране. "
            "С 1845 непройденное можно снять решением двора без награды.",
        )
    )
    for i in range(1, 5):
        r = ROMAN[i]
        c = WATER[i]
        out.append(loc(f"CHI_pay_water_{i}", f"Ирригация {r}: казна {Y(c['money'])}"))
        out.append(
            loc(
                f"CHI_pay_water_{i}_desc",
                f"§YИрригация {r}§W. Если казны или товаров не хватает, списывать не будут.\n\n"
                + cost_block(c),
            )
        )
    out.append(loc("CHI_pay_unique", f"Речные работы: казна {Y(UNIQ['money'])}"))
    out.append(
        loc(
            "CHI_pay_unique_desc",
            "§YОсобый речной проект§W региона. Если казны или товаров не хватает, списывать не будут.\n\n"
            + cost_block(UNIQ),
        )
    )
    out.append(loc("CHI_sel_bribe", f"Подкуп  ·  {Y(500000)}"))
    out.append(
        loc(
            "CHI_sel_bribe_desc",
            "Взятки местным вожакам. Сепаратизм региона -1.\n\n"
            f"Казна: {Y(500000)}.\nПри коррупции: {R(1000000)} (вдвое).\nПовтор через год.",
        )
    )
    out.append(
        loc(
            "CHI_sel_tax_cut_desc",
            "Маркер на регион на 2 года. Казна отдельно теряет §Y4%§W эффективности налогов за каждый такой регион (до 20). "
            "В самом маркере провинции налога нет - штраф только в страновом стеке.",
        )
    )
    out.append(
        loc(
            "CHI_sel_tax_done_desc",
            "Льгота действует 2 года в этом регионе. Казна теряет §Y4%§W эффективности налогов. "
            "Другие регионы можно освободить отдельно.",
        )
    )
    out.append(
        loc(
            "CHI_sep_tax_cut_desc",
            "Маркер региона на 2 года. В этой карточке нет штрафа налога: казна теряет §Y4%§W эффективности за стек CHI_sep_tax_stack, по одному на регион.",
        )
    )
    for i in range(1, 21):
        out.append(
            loc(
                f"CHI_sep_tax_stack_{i}_desc",
                "Казна теряет §Y4%§W эффективности налогов, пока в одном из регионов действует льгота. Несколько регионов складываются.",
            )
        )
    out.append(
        loc(
            "CHI_water_choice_desc",
            "Ремонт снижает воду на 1 уровень в этом регионе. Один заказ на весь штат. Если ремонт уже идёт, кнопок нет.\n\n"
            + "\n\n".join(f"§Y{ROMAN[i]}§W\n{cost_block(WATER[i])}" for i in range(1, 5)),
        )
    )
    for i in range(1, 5):
        r = ROMAN[i]
        out.append(
            loc(
                f"CHI_water_choice_{i}_desc",
                f"§YИрригация {r}§W - вода региона -1 ступень. Один заказ на весь штат.\n\n"
                f"{cost_block(WATER[i])}\n\n"
                "Если казны или товаров не хватает, списывать не будут. Повтор в этом регионе около 2.5 лет.",
            )
        )
    out.append(
        loc(
            "CHI_water_choice_unique_desc",
            "Речные проекты региона. Кнопка есть только если этот модификатор висит в провинции.\n\n"
            f"§YКанал§W\n{cost_block(CANAL)}\n\n"
            f"§YЯнцзы§W\n{cost_block(YANG)}\n\n"
            f"§YХуанхэ§W\n{cost_block(YELL)}\n\n"
            "Перенос русла Хуанхэ - решение двора.",
        )
    )
    out.append(
        loc(
            "CHI_famine_choice_desc",
            "§YВеликий амбар§W - голод региона -1 ступень, сельское хозяйство +5%. Прирост населения не даёт. Один заказ на весь штат.\n\n"
            f"Склад: {goods_line(GRAN)}.\nДенег не берёт.\n\n"
            "Если программа уже идёт, кнопки амбара нет - повтор 2 года. "
            "Если амбар уже стоит и голода нет, заказывать нечего.",
        )
    )
    return out


def main():
    raw = CSV.read_bytes().decode("cp1251")
    by_key = {}
    order = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        key = line.split(";", 1)[0]
        if key not in by_key:
            order.append(key)
        by_key[key] = line if line.endswith("\r") else line
    for row in rows():
        key = row.split(";", 1)[0]
        if key not in by_key:
            order.append(key)
        by_key[key] = row.rstrip("\r")
    body = "\r\n".join(by_key[k].rstrip("\r") for k in order) + "\r\n"
    body = (
        body.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2212", "-")
        .replace("\u2026", "...")
    )
    CSV.write_bytes(body.encode("cp1251"))
    print("colored loc keys", len(rows()), "csv lines", len(order))


if __name__ == "__main__":
    main()

"""Штраф фабрик: −70% без города, −25% при urban в штате, 0% при town_infrastructure."""
import re
from pathlib import Path

PROD = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5\common\production_types.txt")

EXCLUDED = {
    "steel_manufactory",
    "fabric_factory",
    "fabric_factory_w",
    "lumber_mill",
    "glass_factory",
    "paper_mill",
}

FACTORIES = {
    "aeroplane_factory",
    "barrel_factory",
    "automobile_factory",
    "radio_factory",
    "telephone_factory",
    "electric_gear_factory",
    "machine_parts_factory",
    "synthetic_oil_factory",
    "synthetic_rubber_factory",
    "synthetic_sulphur_factory",
    "fuel_refinery",
    "steamer_shipyard",
    "luxury_clothes_factory",
    "luxury_furniture_factory",
    "steel_factory",
    "artillery_factory",
    "clipper_shipyard",
    "small_arms_factory",
    "furniture_factory",
    "regular_clothes_factory",
    "explosives_factory",
    "ammunition_factory",
    "canned_food_factory",
    "canned_food_factory_fish",
    "canned_food_factory_cattle",
    "canned_food_factory_fruit",
    "dye_factory",
    "liquor_distillery",
    "winery",
    "cement_factory",
    "fertilizer_factory",
}

PENALTY_BLOCK = """
# town_penalty_bonus — нет города: −70% (no urban) / −25% (urban, не non_colonial) / inner_colonisation −10% (urban) / −20% (no urban); non_colonial без города на urban — штраф не работает
\tbonus = {
\t\ttrigger = {
\t\t\tAND = {
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\thas_building = town_infrastructure
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\tterrain = urban
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tNOT = { colonial_politics = inner_colonisation }
\t\t\t}
\t\t}
\t\tvalue = -0.7
\t}
\tbonus = {
\t\ttrigger = {
\t\t\tAND = {
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\thas_building = town_infrastructure
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tstate_scope = {
\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\tterrain = urban
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tNOT = { colonial_politics = inner_colonisation }
\t\t\t\tNOT = { colonial_politics = non_colonial }
\t\t\t}
\t\t}
\t\tvalue = -0.25
\t}
\tbonus = {
\t\ttrigger = {
\t\t\tAND = {
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\thas_building = town_infrastructure
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tstate_scope = {
\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\tterrain = urban
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tcolonial_politics = inner_colonisation
\t\t\t}
\t\t}
\t\tvalue = -0.10
\t}
\tbonus = {
\t\ttrigger = {
\t\t\tAND = {
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\thas_building = town_infrastructure
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tNOT = {
\t\t\t\t\tstate_scope = {
\t\t\t\t\t\tany_owned_province = {
\t\t\t\t\t\t\tterrain = urban
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\tcolonial_politics = inner_colonisation
\t\t\t}
\t\t}
\t\tvalue = -0.20
\t}"""

MARKER = "# town_penalty_bonus"
OLD = re.compile(MARKER + r"(?:\n\tbonus = \{.*?\n\t\})+", re.DOTALL)


def patch() -> None:
    text = PROD.read_text(encoding="utf-8")
    text = OLD.sub("", text)

    for name in sorted(FACTORIES - EXCLUDED):
        block_re = re.compile(
            rf"({re.escape(name)} = \{{)(.*?)(\n\}})",
            re.DOTALL,
        )
        match = block_re.search(text)
        if not match:
            raise SystemExit(f"not found: {name}")
        body = match.group(2).rstrip()
        if MARKER in body:
            body = body[: body.index(MARKER)].rstrip()
        new_body = body + PENALTY_BLOCK + "\n"
        text = text[: match.start()] + match.group(1) + new_body + match.group(3) + text[match.end() :]

    PROD.write_text(text, encoding="utf-8")
    print(f"patched {len(FACTORIES - EXCLUDED)} factories")


if __name__ == "__main__":
    patch()

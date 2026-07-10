"""Штраф фабрик (Г) без города в штате — production_types.txt.

Кэш: has_province_modifier = state_has_town / state_has_urban
(штамп на все провинции штата, см. events/TownCache.txt).
"""
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

NO_TOWN = "\n\t\t\t\tNOT = { has_province_modifier = state_has_town }"
HAS_URBAN = "\n\t\t\t\thas_province_modifier = state_has_urban"
NO_URBAN = "\n\t\t\t\tNOT = { has_province_modifier = state_has_urban }"

# 4 взаимоисключающих bonus. colonial_politics — через owner; town/urban — кэш O(1).
PENALTY_BLOCK = f"""
# town_penalty (Г) — кэш state_has_town / state_has_urban (events/TownCache.txt)
	bonus = {{
		trigger = {{
			AND = {{
				owner = {{ NOT = {{ colonial_politics = inner_colonisation }} }}{NO_TOWN}{NO_URBAN}
			}}
		}}
		value = -0.7
	}}
	bonus = {{
		trigger = {{
			AND = {{
				owner = {{ NOT = {{ colonial_politics = inner_colonisation }} }}
				owner = {{ NOT = {{ colonial_politics = non_colonial }} }}{NO_TOWN}{HAS_URBAN}
			}}
		}}
		value = -0.25
	}}
	bonus = {{
		trigger = {{
			AND = {{
				owner = {{ colonial_politics = inner_colonisation }}{NO_TOWN}{HAS_URBAN}
			}}
		}}
		value = -0.10
	}}
	bonus = {{
		trigger = {{
			AND = {{
				owner = {{ colonial_politics = inner_colonisation }}{NO_TOWN}{NO_URBAN}
			}}
		}}
		value = -0.20
	}}"""

MARKER = "# town_penalty"


def remove_penalty_blocks(text: str) -> str:
    while MARKER in text:
        idx = text.index(MARKER)
        line_start = text.rfind("\n", 0, idx) + 1
        pos = text.find("\n", idx) + 1
        while pos < len(text) and text[pos : pos + 10].lstrip().startswith("bonus"):
            start = text.find("bonus", pos)
            depth = 0
            started = False
            i = start
            while i < len(text):
                if text[i] == "{":
                    depth += 1
                    started = True
                elif text[i] == "}":
                    depth -= 1
                    if started and depth == 0:
                        pos = i + 1
                        break
                i += 1
            else:
                break
        text = text[:line_start] + text[pos:].lstrip("\n")
    return text


def patch() -> None:
    text = remove_penalty_blocks(PROD.read_text(encoding="utf-8"))

    for name in sorted(FACTORIES - EXCLUDED):
        block_re = re.compile(
            rf"(?m)(^{re.escape(name)} = \{{)(.*?)(\n\}})",
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

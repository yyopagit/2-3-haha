"""Городские бонусы poptypes: state any_owned → провинциальный has_building / terrain."""
from __future__ import annotations

import re
from pathlib import Path

POPTYPES = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5\poptypes")

# state_scope { any_owned_province { has_building = town_infrastructure } } → has_building
TOWN_STATE = re.compile(
    r"state_scope\s*=\s*\{\s*"
    r"any_owned_province\s*=\s*\{\s*"
    r"has_building\s*=\s*town_infrastructure\s*"
    r"\}\s*\}",
    re.MULTILINE,
)

# state_scope { any_owned_province { terrain = urban } } → terrain = urban
URBAN_STATE = re.compile(
    r"state_scope\s*=\s*\{\s*"
    r"any_owned_province\s*=\s*\{\s*"
    r"terrain\s*=\s*urban\s*"
    r"\}\s*\}",
    re.MULTILINE,
)

# NOT = { state_scope { any_owned... town } } → NOT = { has_building = town_infrastructure }
NOT_TOWN_STATE = re.compile(
    r"NOT\s*=\s*\{\s*"
    r"state_scope\s*=\s*\{\s*"
    r"any_owned_province\s*=\s*\{\s*"
    r"has_building\s*=\s*town_infrastructure\s*"
    r"\}\s*\}\s*\}",
    re.MULTILINE,
)


def patch_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text
    text = NOT_TOWN_STATE.sub("NOT = { has_building = town_infrastructure }", text)
    text = TOWN_STATE.sub("has_building = town_infrastructure", text)
    text = URBAN_STATE.sub("terrain = urban", text)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return 1
    return 0


def main() -> None:
    n = 0
    for path in sorted(POPTYPES.glob("*.txt")):
        if patch_file(path):
            print(f"patched {path.name}")
            n += 1
    print(f"done, {n} files")


if __name__ == "__main__":
    main()

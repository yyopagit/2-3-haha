"""Убрать штрафы из production_types (крашит). Штраф — через модификаторы в JAN.txt."""
import re
from pathlib import Path

PROD = Path(r"C:\Games\Vic2LV2\Victoria 2\mod\5\common\production_types.txt")

BLOCK = re.compile(
    r"\n# town_penalty_bonus\n"
    r"\tbonus = \{.*?"
    r"value = 0\.55\n"
    r"\t\}\n",
    re.DOTALL,
)


def main() -> None:
    text = PROD.read_text(encoding="utf-8")
    text, n = BLOCK.subn("\n", text)
    PROD.write_text(text, encoding="utf-8")
    print(f"removed {n} town_penalty_bonus blocks from production_types.txt")


if __name__ == "__main__":
    main()

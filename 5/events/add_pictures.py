# -*- coding: utf-8 -*-
"""Добавляет picture = "MARKET" в события, где картинки ещё нет."""
import os
import re
EVENTS_FILE = os.path.join(os.path.dirname(__file__) or ".", "Other.txt")

def main():
    with open(EVENTS_FILE, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    # Вставка picture после desc, если дальше идёт trigger/is_triggered_only/option без picture между ними
    pattern = re.compile(
        r'(desc\s*=\s*"[^"]*"\s*\n)'
        r'(\s*)'
        r'((?:(?!picture\s*=).)*?)'
        r'(\s*(?:trigger\s*=\s*\{|is_triggered_only\s*=|option\s*=\s*\{|mean_time_to_happen\s*=\s*\{|news\s*=\s*|fire_only_once\s*=))',
        re.DOTALL
    )
    added = 0
    def repl(m):
        if "picture" in m.group(3):
            return m.group(0)
        nonlocal added
        added += 1
        return m.group(1) + m.group(2) + '\tpicture = "MARKET"\n' + m.group(2) + m.group(3) + m.group(4)
    new_text = pattern.sub(repl, text)
    if added:
        with open(EVENTS_FILE, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
    with open("add_pictures_log.txt", "w", encoding="utf-8") as log:
        log.write("Added picture to %d events.\n" % added)

if __name__ == "__main__":
    main()

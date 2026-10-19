"""Compare part quantities in the schematic description with bom/bom_draft.py (per LCSC code).

Usage: python scripts/check_bom.py
"""

import sys
from collections import Counter

import bom_draft
import build_schematic


def main():
    sch = Counter(p.fields["LCSC"] for s in build_schematic.build() for p in s.parts
                  if p.in_bom and p.fields.get("LCSC"))
    bom = Counter()
    for p in bom_draft.PARTS:
        if p.lcsc not in bom_draft.NOT_ASSEMBLED:
            bom[p.lcsc] += p.qty
    errors = 0
    for code in sorted(set(sch) | set(bom)):
        if sch[code] != bom[code]:
            errors += 1
            mpn = next((p.mpn for p in bom_draft.PARTS if p.lcsc == code), "?")
            print(f"{code} {mpn}: schematic {sch[code]}, BOM {bom[code]}")
    print(f"{sum(sch.values())} parts in schematic, {sum(bom.values())} in BOM, {errors} mismatch(es)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

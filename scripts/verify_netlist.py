"""Check that the schematic connectivity exported by KiCad matches the design description.

Exports the netlist with kicad-cli, groups pins by net, and compares the partition with the
pin -> net mapping declared in scripts/build_schematic.py. Exits nonzero on any mismatch.

Usage: python scripts/verify_netlist.py
"""

import subprocess
import sys

import build_schematic
import schgen
from kicad_env import PROJECT_DIR, kicad_cli, project_file
from sexpr import find, find_all, parse

NETLIST = PROJECT_DIR / "out" / "reports" / "netlist.net"


def exported_groups():
    subprocess.run([kicad_cli(), "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", str(NETLIST), str(project_file(".kicad_sch"))],
                   check=True, capture_output=True)
    tree = parse(NETLIST.read_text(encoding="utf-8"))
    groups = {}
    for net in find_all(find(tree, "nets"), "net"):
        name = find(net, "name")[1]
        nodes = frozenset((find(n, "ref")[1], find(n, "pin")[1]) for n in find_all(net, "node")
                          if not find(n, "ref")[1].startswith("#"))
        if nodes:
            groups[name] = nodes
    return groups


def expected_groups():
    sheets = build_schematic.build()
    nets = {}
    for sheet in sheets:
        for part in sheet.parts:
            if part.ref.startswith("#"):
                continue
            for pin, net in schgen.resolve_pins(part):
                key = net if net is not None else f"NC:{part.ref}:{pin.number}"
                nets.setdefault(key, set()).add((part.ref, pin.number))
    return {k: frozenset(v) for k, v in nets.items()}


def main():
    got = set(exported_groups().values())
    want = expected_groups()
    errors = 0
    for name, pins in sorted(want.items()):
        if pins not in got:
            errors += 1
            print(f"MISMATCH net {name}: expected {sorted(pins)}")
    extra = got - set(want.values())
    for pins in extra:
        errors += 1
        print(f"UNEXPECTED net: {sorted(pins)}")
    print(f"{len(want)} expected nets, {len(got)} exported nets, {errors} mismatch(es)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

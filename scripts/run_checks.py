"""Run ERC on the schematic and DRC on the board, write JSON reports to out/reports/.

Exits with a nonzero code if any error-level violation (or unconnected item) is found.

Usage: python scripts/run_checks.py [--erc-only | --drc-only] [--schematic-parity]
"""

import argparse
import json
import subprocess
import sys

from kicad_env import PROJECT_DIR, kicad_cli, project_file

REPORTS_DIR = PROJECT_DIR / "out" / "reports"


def count_errors(violations):
    return sum(1 for v in violations if v.get("severity") == "error")


def run_erc():
    report = REPORTS_DIR / "erc.json"
    subprocess.run(
        [kicad_cli(), "sch", "erc", "--format", "json", "--severity-all",
         "-o", str(report), str(project_file(".kicad_sch"))],
        check=True,
    )
    data = json.loads(report.read_text(encoding="utf-8"))
    violations = [v for sheet in data.get("sheets", []) for v in sheet.get("violations", [])]
    errors = count_errors(violations)
    print(f"ERC: {errors} error(s), {len(violations) - errors} other violation(s) -> {report.name}")
    return errors


def run_drc(schematic_parity):
    report = REPORTS_DIR / "drc.json"
    cmd = [kicad_cli(), "pcb", "drc", "--format", "json", "--severity-all",
           "-o", str(report)]
    if schematic_parity:
        cmd.append("--schematic-parity")
    cmd.append(str(project_file(".kicad_pcb")))
    subprocess.run(cmd, check=True)
    data = json.loads(report.read_text(encoding="utf-8"))
    violations = data.get("violations", [])
    unconnected = data.get("unconnected_items", [])
    parity = data.get("schematic_parity", [])
    errors = count_errors(violations) + len(unconnected) + count_errors(parity)
    print(f"DRC: {count_errors(violations)} error(s), {len(unconnected)} unconnected, "
          f"{len(parity)} parity issue(s), {len(violations) - count_errors(violations)} "
          f"other violation(s) -> {report.name}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--erc-only", action="store_true")
    group.add_argument("--drc-only", action="store_true")
    parser.add_argument("--schematic-parity", action="store_true")
    args = parser.parse_args()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0
    if not args.drc_only:
        errors += run_erc()
    if not args.erc_only:
        errors += run_drc(args.schematic_parity)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

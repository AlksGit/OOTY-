"""Report decoupling quality: distance from each capacitor to the IC power pad it decouples.

Uses the schematic groups (scripts/build_schematic.py): a capacitor on power nets only is
matched with the nearest same-net pad of an IC in its group. Run with KiCad's Python.

Usage: "C:\Program Files\KiCad\10.0\bin\python.exe" scripts/check_placement.py
"""

import math

import pcbnew

import build_schematic
from kicad_env import project_file

LIMIT_MM = 3.0


def main():
    board = pcbnew.LoadBoard(str(project_file(".kicad_pcb")))
    groups = {}
    for sheet in build_schematic.build():
        for i, grp in enumerate(sheet.groups):
            for p in grp.parts:
                groups[p.ref] = (sheet.name, i)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    rows = []
    for ref, fp in fps.items():
        if not ref.startswith("C"):
            continue
        nets = {p.GetNetname() for p in fp.Pads()} - {"GND"}
        ics = [f for r, f in fps.items() if r.startswith("U") and groups.get(r) == groups.get(ref)]
        best = None
        for ic in ics:
            for pad in ic.Pads():
                if pad.GetNetname() in nets:
                    for cp in fp.Pads():
                        if cp.GetNetname() == pad.GetNetname():
                            d = pcbnew.ToMM((pad.GetPosition() - cp.GetPosition()).EuclideanNorm())
                            if best is None or d < best[0]:
                                best = (d, ic.GetReference(), pad.GetNumber(), pad.GetNetname())
        if best:
            rows.append((best[0], ref) + best[1:])
    rows.sort(reverse=True)
    far = [r for r in rows if r[0] > LIMIT_MM]
    for d, ref, ic, pin, net in far:
        print(f"{ref}: {d:.1f} mm from {ic} pin {pin} ({net})")
    print(f"{len(rows)} decoupling caps checked, {len(far)} farther than {LIMIT_MM} mm")


if __name__ == "__main__":
    main()

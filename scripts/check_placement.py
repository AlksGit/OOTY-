"""Report placement quality: decoupling distances and ratsnest length.

- Decoupling: for every capacitor declared with `near` in scripts/build_schematic.py, distance
  from its pad on the shared net to the pin it decouples. Fails above LIMIT_MM (high-frequency
  decoupling, below 1 uF) or BULK_LIMIT_MM (bulk capacitors, 1 uF and more).
- Ratsnest: minimum spanning tree length of each signal net (power and ground nets excluded),
  with the longest nets listed, to compare placement iterations.

Run with KiCad's Python.

Usage: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/check_placement.py
"""

import math
import sys

import pcbnew

import build_schematic
from kicad_env import project_file

LIMIT_MM = 3.0
BULK_LIMIT_MM = 6.0
BULK_UF = 1.0
PLANE_NETS = {"GND", "+3V3", "+5V", "VBUS", "VIO"}


def pos(pad):
    p = pad.GetPosition()
    return pcbnew.ToMM(p.x), pcbnew.ToMM(p.y)


def mst_length(points):
    """Length of the minimum spanning tree over the points (Prim)."""
    if len(points) < 2:
        return 0.0
    done = [points[0]]
    rest = points[1:]
    total = 0.0
    while rest:
        d, i = min((math.dist(a, b), i) for i, b in enumerate(rest) for a in done)
        total += d
        done.append(rest.pop(i))
    return total


def microfarads(value):
    """'100nF/50V' -> 0.1, '22uF/25V' -> 22.0."""
    number = value.split("/")[0].rstrip("F")
    scale = {"p": 1e-6, "n": 1e-3, "u": 1.0}[number[-1]]
    return float(number[:-1]) * scale


def check_decoupling(fps, near):
    rows = []
    for cap, (owner, pin) in near.items():
        target = fps[owner].FindPadByNumber(pin)
        net = target.GetNetname()
        pads = [p for p in fps[cap].Pads() if p.GetNetname() == net]
        d = min(math.dist(pos(p), pos(target)) for p in pads)
        limit = BULK_LIMIT_MM if microfarads(fps[cap].GetValue()) >= BULK_UF else LIMIT_MM
        rows.append((d / limit, d, limit, cap, owner, pin, net))
    rows.sort(reverse=True)
    far = [r for r in rows if r[0] > 1.0]
    for _, d, limit, cap, owner, pin, net in rows[:8]:
        flag = "  FAR" if d > limit else ""
        print(f"  {cap}: {d:.1f} mm from {owner} pin {pin} ({net}, limit {limit} mm){flag}")
    print(f"{len(rows)} decoupling caps checked, {len(far)} beyond their limit")
    return len(far)


def ratsnest(board):
    nets = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            name = pad.GetNetname()
            if name and name not in PLANE_NETS and not name.startswith("unconnected"):
                nets.setdefault(name, []).append(pos(pad))
    lengths = sorted(((mst_length(pts), name) for name, pts in nets.items()), reverse=True)
    total = sum(length for length, _ in lengths)
    print(f"Signal ratsnest: {total:.0f} mm over {len(lengths)} nets; longest:")
    for length, name in lengths[:12]:
        print(f"  {name}: {length:.0f} mm")


def main():
    board = pcbnew.LoadBoard(str(project_file(".kicad_pcb")))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    near = build_schematic.decoupling(build_schematic.build())
    far = check_decoupling(fps, near)
    ratsnest(board)
    return 1 if far else 0


if __name__ == "__main__":
    sys.exit(main())

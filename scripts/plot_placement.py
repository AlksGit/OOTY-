"""Draw a placement review image: board outline, courtyards, references and signal ratsnest.

Step 1 (KiCad's Python) dumps the board geometry to out/renders/placement.json; step 2 (system
Python with matplotlib) draws out/renders/pcb_placement_ratsnest.png (both sides).

Usage: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/plot_placement.py
       python scripts/plot_placement.py --draw
"""

import json
import math
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
DUMP = PROJECT_DIR / "out" / "renders" / "placement.json"
IMAGE = PROJECT_DIR / "out" / "renders" / "pcb_placement_ratsnest.png"
PLANE_NETS = {"GND", "+3V3", "+5V", "VBUS", "VIO"}
ORIGIN = (100.0, 100.0)


def dump():
    import pcbnew
    from kicad_env import project_file

    board = pcbnew.LoadBoard(str(project_file(".kicad_pcb")))

    def xy(v):
        return pcbnew.ToMM(v.x) - ORIGIN[0], pcbnew.ToMM(v.y) - ORIGIN[1]

    parts, nets = [], {}
    for fp in board.GetFootprints():
        poly = fp.GetCourtyard(pcbnew.F_CrtYd)
        bb = poly.BBox() if poly.OutlineCount() else fp.GetBoundingBox(False)
        x0, y0 = xy(bb.GetOrigin())
        x1, y1 = xy(bb.GetEnd())
        parts.append({"ref": fp.GetReference(), "box": [x0, y0, x1, y1]})
        for pad in fp.Pads():
            name = pad.GetNetname()
            if name and name not in PLANE_NETS and not name.startswith("unconnected"):
                nets.setdefault(name, []).append(xy(pad.GetPosition()))
    DUMP.write_text(json.dumps({"parts": parts, "nets": nets}), encoding="utf-8")


def mst_edges(points):
    if len(points) < 2:
        return []
    done, rest, edges = [points[0]], points[1:], []
    while rest:
        _, a, i = min((math.dist(a, b), a, i) for i, b in enumerate(rest) for a in done)
        edges.append((a, rest[i]))
        done.append(rest.pop(i))
    return edges


def draw():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    data = json.loads(DUMP.read_text(encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(17, 11), dpi=110)
    ax.add_patch(Rectangle((0, 0), 85, 55, fill=False, lw=1.5, color="black"))
    for name, pts in data["nets"].items():
        for a, b in mst_edges([tuple(p) for p in pts]):
            ax.plot([a[0], b[0]], [a[1], b[1]], lw=0.4, color="tab:orange", alpha=0.7)
    for part in data["parts"]:
        x0, y0, x1, y1 = part["box"]
        color = "tab:blue" if part["ref"][0] in "UJ" else "tab:gray"
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.6, color=color))
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, part["ref"], fontsize=5, ha="center", va="center")
    ax.set_xlim(-2, 87)
    ax.set_ylim(57, -2)
    ax.set_aspect("equal")
    ax.set_xticks(range(0, 86, 5))
    ax.set_yticks(range(0, 56, 5))
    ax.grid(lw=0.2)
    fig.tight_layout()
    fig.savefig(IMAGE)
    print(f"wrote {IMAGE.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    if "--draw" in sys.argv:
        draw()
    else:
        dump()

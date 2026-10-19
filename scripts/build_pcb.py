"""Build OOTY.kicad_pcb from the schematic netlist (run with KiCad's Python).

- 4-layer JLCPCB stack-up (JLC04161H-7628), design rules and net classes (saved in OOTY.kicad_pro)
- board outline 85 x 55 mm with rounded corners, 4 x M3 holes
- every schematic footprint imported with its nets and schematic path (DRC parity)
- placement from scripts/placement.py; parts without a position are parked beside the board

Usage: "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" scripts/build_pcb.py
"""

import subprocess
import sys
from pathlib import Path

import pcbnew

from kicad_env import PROJECT_DIR, kicad_cli, project_file
from sexpr import dumps, find, find_all, parse
import autoplace
import build_schematic
import placement
import silk

FOOTPRINT_DIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\footprints")
NETLIST = PROJECT_DIR / "out" / "reports" / "netlist.net"

BOARD_W = 85.0
BOARD_H = 55.0
CORNER_R = 2.0
HOLE_INSET = 3.5

# JLCPCB JLC04161H-7628 (1.6 mm): outer 1 oz, inner 0.5 oz, 7628 prepreg 0.2104 mm, core 1.065 mm.
# The stack-up is not exposed by the pcbnew SWIG API: it is written into the file after saving.
STACKUP = """(stackup
  (layer "F.SilkS" (type "Top Silk Screen"))
  (layer "F.Paste" (type "Top Solder Paste"))
  (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
  (layer "F.Cu" (type "copper") (thickness 0.035))
  (layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
  (layer "In1.Cu" (type "copper") (thickness 0.0152))
  (layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.6) (loss_tangent 0.02))
  (layer "In2.Cu" (type "copper") (thickness 0.0152))
  (layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "7628") (epsilon_r 4.4) (loss_tangent 0.02))
  (layer "B.Cu" (type "copper") (thickness 0.035))
  (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
  (layer "B.Paste" (type "Bottom Solder Paste"))
  (layer "B.SilkS" (type "Bottom Silk Screen"))
  (copper_finish "HAL lead-free")
  (dielectric_constraints no))"""

# Rules (SPEC.md section 7): conservative values above JLCPCB minimums.
RULES = {
    "clearance": 0.15,
    "track": 0.15,
    "via_diameter": 0.6,
    "via_drill": 0.3,
    "copper_edge": 0.3,
    "hole_to_hole": 0.5,
    "annular": 0.13,
}

NETCLASSES = {
    # name: (track width, clearance, via diameter, via drill, patterns)
    "Power": (0.5, 0.15, 0.8, 0.4, ["+3V3", "5V_SW*", "5V_DUT", "3V3_SW*", "3V3_DUT", "VIO*", "GND"]),
    "HighCurrent": (1.0, 0.2, 0.8, 0.4, ["VBUS", "+5V", "*SW_3V3"]),
    "USB": (0.25, 0.15, 0.6, 0.3, ["USB_DP", "USB_DM"]),
}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def read_netlist():
    tree = parse(NETLIST.read_text(encoding="utf-8"))
    comps = []
    for c in find_all(find(tree, "components"), "comp"):
        sheet_tstamps = find(find(c, "sheetpath"), "tstamps")[1]
        comps.append({
            "ref": find(c, "ref")[1],
            "value": find(c, "value")[1],
            "footprint": find(c, "footprint")[1] if find(c, "footprint") else "",
            "path": sheet_tstamps + find(c, "tstamps")[1],
            "sheet": find(find(c, "sheetpath"), "names")[1],
            "fields": {find(f, "name")[1]: (f[2] if len(f) > 2 else "")
                       for f in find_all(find(c, "fields"), "field")},
            "props": {find(p, "name")[1] for p in find_all(c, "property")},
        })
    pads = {}
    for net in find_all(find(tree, "nets"), "net"):
        name = find(net, "name")[1]
        for node in find_all(net, "node"):
            pads[(find(node, "ref")[1], find(node, "pin")[1])] = name
    return comps, pads


def export_netlist():
    subprocess.run([kicad_cli(), "sch", "export", "netlist", "--format", "kicadsexpr",
                    "-o", str(NETLIST), str(project_file(".kicad_sch"))],
                   check=True, capture_output=True)


def setup_board(board):
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()

    ds.m_MinClearance = mm(RULES["clearance"])
    ds.m_TrackMinWidth = mm(RULES["track"])
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_CopperEdgeClearance = mm(RULES["copper_edge"])
    ds.m_HoleToHoleMin = mm(RULES["hole_to_hole"])
    ds.m_ViasMinAnnularWidth = mm(RULES["annular"])

    ns = ds.m_NetSettings
    default = ns.GetDefaultNetclass()
    default.SetClearance(mm(RULES["clearance"]))
    default.SetTrackWidth(mm(0.2))
    default.SetViaDiameter(mm(RULES["via_diameter"]))
    default.SetViaDrill(mm(RULES["via_drill"]))
    ns.ClearNetclasses()
    ns.ClearNetclassPatternAssignments()
    for name, (track, clearance, via_d, via_drill, patterns) in NETCLASSES.items():
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(mm(track))
        nc.SetClearance(mm(clearance))
        nc.SetViaDiameter(mm(via_d))
        nc.SetViaDrill(mm(via_drill))
        if name == "USB":
            nc.SetDiffPairWidth(mm(0.25))
            nc.SetDiffPairGap(mm(0.2))
        ns.SetNetclass(name, nc)
        for pattern in patterns:
            ns.SetNetclassPatternAssignment(pattern, name)


def draw_outline(board):
    x0, y0 = placement.ORIGIN
    x1, y1 = x0 + BOARD_W, y0 + BOARD_H
    r = CORNER_R
    segs = [((x0 + r, y0), (x1 - r, y0)), ((x1, y0 + r), (x1, y1 - r)),
            ((x1 - r, y1), (x0 + r, y1)), ((x0, y1 - r), (x0, y0 + r))]
    for a, b in segs:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)
    k = r * (1 - 0.7071067811865476)
    arcs = [((x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0)),
            ((x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r)),
            ((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1)),
            ((x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r))]
    for a, m, b in arcs:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(pt(*a), pt(*m), pt(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)


def load_footprint(fpid):
    lib, name = fpid.split(":", 1)
    fp = pcbnew.FootprintLoad(str(FOOTPRINT_DIR / f"{lib}.pretty"), name)
    if fp is None:
        raise FileNotFoundError(fpid)
    return fp


def add_footprints(board, comps, pads):
    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    park_x0 = placement.ORIGIN[0] + BOARD_W + 10
    park_x, park_y, row_h = park_x0, placement.ORIGIN[1], 0.0
    parked = 0
    for c in comps:
        if not c["footprint"]:
            raise ValueError(f"{c['ref']} has no footprint")
        fp = load_footprint(c["footprint"])
        lib, name = c["footprint"].split(":", 1)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(c["ref"])
        for key, val in c["fields"].items():
            if key in ("Footprint",):
                continue
            fp.SetField(key, val)
            fp.GetField(key).SetVisible(False)
        if c["ref"].startswith(("TP", "H")) or "DNP" in c["value"]:
            fp.SetExcludedFromBOM(True)
            fp.SetExcludedFromPosFiles(True)
        if "dnp" in c["props"] or "DNP" in c["value"]:
            fp.SetDNP(True)
        fp.SetValue(c["value"])
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetSheetname(c["sheet"].strip("/"))
        fp.SetSheetfile(f"{c['sheet'].strip('/')}.kicad_sch")
        for pad in fp.Pads():
            key = (c["ref"], pad.GetNumber())
            if key in pads:
                pad.SetNet(net(pads[key]))
        pos = placement.position(c["ref"], c["value"])
        if pos is None:
            bb = fp.GetBoundingBox(False)
            w, h = pcbnew.ToMM(bb.GetWidth()) + 1.0, pcbnew.ToMM(bb.GetHeight()) + 1.0
            if park_x + w > park_x0 + 80:
                park_x, park_y, row_h = park_x0, park_y + row_h, 0.0
            fp.SetPosition(pt(park_x + w / 2, park_y + h / 2))
            park_x += w
            row_h = max(row_h, h)
            parked += 1
        else:
            x, y, rot, side = pos
            fp.SetPosition(pt(x, y))
            if side == "B":
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            fp.SetOrientationDegrees(rot)
            fp.SetLocked(True)
        board.Add(fp)
    return parked


def write_stackup(path):
    """Insert the JLC stack-up into (setup ...) and set the board thickness."""
    tree = parse(path.read_text(encoding="utf-8"))
    setup = find(tree, "setup")
    old = find(setup, "stackup")
    if old is not None:
        setup.remove(old)
    setup.insert(1, parse(STACKUP))
    general = find(tree, "general")
    thickness = find(general, "thickness")
    thickness[1] = parse("(x 1.6062)")[1]
    path.write_text(dumps(tree) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([kicad_cli(), "pcb", "upgrade", "--force", str(path)], check=True,
                   capture_output=True)


def main():
    export_netlist()
    comps, pads = read_netlist()
    pcb_path = project_file(".kicad_pcb")
    board = pcbnew.NewBoard(str(pcb_path))
    setup_board(board)
    draw_outline(board)
    parked = add_footprints(board, comps, pads)
    if "--no-autoplace" not in sys.argv:
        groups = {}
        for sheet in build_schematic.build():
            for i, grp in enumerate(sheet.groups):
                for p in grp.parts:
                    groups[p.ref] = f"{sheet.name}:{i}"
        area = placement.absolute(placement.AREA)
        keepouts = [placement.absolute(k) for k in placement.KEEPOUTS]
        failed = autoplace.run(board, area, keepouts, groups)
        parked = len(failed)
        if failed:
            print("not placed:", " ".join(failed))
        ox, oy = placement.ORIGIN
        marking = [(t, ox + x, oy + y, h) for t, x, y, h in placement.MARKING]
        hidden = silk.run(board, placement.absolute((0.6, 0.6, 84.4, 54.4)),
                          placement.refs_with_value(placement.HEADERS_BOTTOM),
                          placement.refs_with_value(placement.HEADERS_RIGHT), marking)
        print(f"{len(hidden)} references moved to F.Fab (no room on silkscreen)")
    board.BuildConnectivity()
    pcbnew.SaveBoard(str(pcb_path), board)
    write_stackup(pcb_path)
    print(f"{len(comps)} footprints, {parked} parked outside the board -> {pcb_path.name}")


if __name__ == "__main__":
    sys.exit(main())

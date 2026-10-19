"""Greedy placer for satellite parts (passives, small ICs) around hand-placed anchors.

For each unplaced footprint, a target point is chosen:
1. the pad of an already placed footprint sharing the most specific signal net, or
2. for parts on power nets only (decoupling), the matching power pad of the first IC of the same
   schematic group, or
3. the board centre.
The part is then put at the nearest free spot (courtyard + margin) found on a spiral grid.
Runs inside KiCad's Python (pcbnew).
"""

import math

import pcbnew

POWER_NETS = {"GND", "+3V3", "+5V", "VBUS", "VIO"}
GRID = 0.25
MARGIN = 0.25          # between ICs
PASSIVE_MARGIN = 0.8   # around resistors: leaves some room for references
DECOUPLING_MARGIN = 0.3
MAX_RADIUS = 30.0


def mm(v):
    return pcbnew.FromMM(v)


def to_mm(v):
    return pcbnew.ToMM(v)


def courtyard_box(fp):
    poly = fp.GetCourtyard(pcbnew.F_CrtYd)
    if poly.OutlineCount() == 0:
        poly = fp.GetCourtyard(pcbnew.B_CrtYd)
    bb = poly.BBox() if poly.OutlineCount() else fp.GetBoundingBox(False)
    return (to_mm(bb.GetX()), to_mm(bb.GetY()), to_mm(bb.GetRight()), to_mm(bb.GetBottom()))


def overlaps(a, b, margin=MARGIN):
    return not (a[2] + margin <= b[0] or b[2] + margin <= a[0] or
                a[3] + margin <= b[1] or b[3] + margin <= a[1])


class Placer:
    def __init__(self, board, area, keepouts, groups):
        """area: (x0, y0, x1, y1) allowed region; keepouts: list of boxes; groups: ref -> group id."""
        self.board = board
        self.area = area
        self.boxes = list(keepouts)
        self.groups = groups
        self.placed = set()

    def mark_placed(self, fp):
        self.placed.add(fp.GetReference())
        self.boxes.append(courtyard_box(fp))

    def _pads_by_net(self):
        index = {}
        for fp in self.board.GetFootprints():
            if fp.GetReference() not in self.placed:
                continue
            for pad in fp.Pads():
                name = pad.GetNetname()
                if name:
                    index.setdefault(name, []).append((fp, pad))
        return index

    def _group_ic_pad(self, fp, nets):
        group = self.groups.get(fp.GetReference())
        for other in self.board.GetFootprints():
            ref = other.GetReference()
            if ref in self.placed and ref.startswith("U") and self.groups.get(ref) == group:
                for pad in other.Pads():
                    if pad.GetNetname() in nets and pad.GetNetname() != "GND":
                        return to_mm(pad.GetPosition().x), to_mm(pad.GetPosition().y)
        return None

    def target(self, fp, index):
        nets = [p.GetNetname() for p in fp.Pads() if p.GetNetname()]
        if fp.GetReference().startswith("C"):
            pad = self._group_ic_pad(fp, nets)
            if pad:
                return pad
        signal = [n for n in nets if n not in POWER_NETS and not n.startswith("unconnected")]
        best = None
        for n in signal:
            cands = index.get(n, [])
            if cands and (best is None or len(cands) < len(best)):
                best = cands
        if best:
            xs = [to_mm(p.GetPosition().x) for _, p in best]
            ys = [to_mm(p.GetPosition().y) for _, p in best]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        group = self.groups.get(fp.GetReference())
        for other in self.board.GetFootprints():
            ref = other.GetReference()
            if ref in self.placed and ref.startswith("U") and self.groups.get(ref) == group:
                for pad in other.Pads():
                    if pad.GetNetname() in nets and pad.GetNetname() != "GND":
                        return to_mm(pad.GetPosition().x), to_mm(pad.GetPosition().y)
                c = other.GetPosition()
                return to_mm(c.x), to_mm(c.y)
        x0, y0, x1, y1 = self.area
        return (x0 + x1) / 2, (y0 + y1) / 2

    def _fits(self, box, margin=MARGIN):
        x0, y0, x1, y1 = self.area
        if box[0] < x0 or box[1] < y0 or box[2] > x1 or box[3] > y1:
            return False
        return not any(overlaps(box, other, margin) for other in self.boxes)

    def place(self, fp):
        index = self._pads_by_net()
        tx, ty = self.target(fp, index)
        small = len(fp.Pads()) <= 3
        rotations = [0, 90] if small else [0, 90, 180, 270]
        ref = fp.GetReference()
        if ref.startswith("C"):
            margin = DECOUPLING_MARGIN
        elif small:
            margin = PASSIVE_MARGIN
        else:
            margin = MARGIN
        steps = int(MAX_RADIUS / GRID)
        for r in range(0, steps):
            ring = []
            if r == 0:
                ring = [(0, 0)]
            else:
                for i in range(-r, r + 1):
                    ring += [(i, -r), (i, r)]
                for j in range(-r + 1, r):
                    ring += [(-r, j), (r, j)]
            ring.sort(key=lambda d: d[0] * d[0] + d[1] * d[1])
            for dx, dy in ring:
                x, y = tx + dx * GRID, ty + dy * GRID
                for rot in rotations:
                    fp.SetOrientationDegrees(rot)
                    fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    box = courtyard_box(fp)
                    if self._fits(box, margin):
                        self.mark_placed(fp)
                        return True
        return False


def priority(fp):
    """Placement order: ICs and protection first, then capacitors, resistors, test points."""
    ref = fp.GetReference()
    order = {"U": 0, "Q": 1, "D": 1, "F": 1, "L": 1, "C": 2, "R": 3, "TP": 4}
    key = "TP" if ref.startswith("TP") else ref[0]
    num = int("".join(ch for ch in ref if ch.isdigit()) or 0)
    return order.get(key, 5), num


def run(board, area, keepouts, groups):
    placer = Placer(board, area, keepouts, groups)
    pending = []
    for fp in board.GetFootprints():
        if fp.IsLocked():
            placer.mark_placed(fp)
        else:
            pending.append(fp)
    # Each IC is followed by the capacitors of its schematic group, so decoupling gets the
    # spots closest to the IC pins before anything else competes for them.
    ordered = []
    ics = [fp for fp in board.GetFootprints() if fp.GetReference().startswith("U")]
    for ic in sorted(ics, key=lambda f: (not f.IsLocked(), priority(f))):
        if not ic.IsLocked():
            ordered.append(ic)
        grp = groups.get(ic.GetReference())
        for fp in sorted(pending, key=priority):
            if (fp.GetReference().startswith("C") and groups.get(fp.GetReference()) == grp
                    and fp not in ordered):
                ordered.append(fp)
    ordered += [fp for fp in sorted(pending, key=priority) if fp not in ordered]
    failed = []
    for fp in ordered:
        if not placer.place(fp):
            failed.append(fp.GetReference())
    return failed

"""Greedy placer for satellite parts (passives, small ICs) around hand-placed anchors.

For each unplaced footprint, a target point is chosen:
1. for decoupling capacitors, the pad they decouple (build_schematic.decoupling), or
2. the pad of an already placed footprint sharing the most specific signal net, or
3. the power pad of the first IC of the same schematic group, or
4. the board centre.
The part is then put at the nearest free spot (courtyard + margin) found on a spiral grid.
Runs inside KiCad's Python (pcbnew).
"""

import math

import pcbnew

POWER_NETS = {"GND", "+3V3", "+5V", "VBUS", "VIO"}
GRID = 0.25
MARGIN = 0.25          # between ICs
PASSIVE_MARGIN = 0.4   # around resistors (their references are on the assembly drawing)
DECOUPLING_MARGIN = 0.1
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


def bottom_only(fp):
    """True for a footprint on the bottom side with no through-hole pad: it does not take any
    room on the top side (test points, solder jumpers, unfitted parts)."""
    return fp.IsFlipped() and all(p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())


def overlaps(a, b, margin=MARGIN):
    return not (a[2] + margin <= b[0] or b[2] + margin <= a[0] or
                a[3] + margin <= b[1] or b[3] + margin <= a[1])


class Placer:
    def __init__(self, board, area, keepouts, groups, near):
        """area: (x0, y0, x1, y1) allowed region; keepouts: list of boxes; groups: ref -> group id;
        near: capacitor ref -> (part ref, pad number) it decouples."""
        self.board = board
        self.area = area
        self.boxes = list(keepouts)
        self.groups = groups
        self.near = near
        self.placed = set()
        self.fps = {fp.GetReference(): fp for fp in board.GetFootprints()}

    def mark_placed(self, fp):
        self.placed.add(fp.GetReference())
        if not bottom_only(fp):
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

    def target(self, fp, index):
        nets = [p.GetNetname() for p in fp.Pads() if p.GetNetname()]
        near = self.near.get(fp.GetReference())
        if near and near[0] in self.placed:
            pad = self.fps[near[0]].FindPadByNumber(near[1])
            return to_mm(pad.GetPosition().x), to_mm(pad.GetPosition().y)
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


def run(board, area, keepouts, groups, near, only=None):
    """Place every unlocked footprint (or only the refs in `only`) and lock it. Returns the refs
    that found no spot."""
    placer = Placer(board, area, keepouts, groups, near)
    pending = []
    for fp in board.GetFootprints():
        if fp.IsLocked():
            placer.mark_placed(fp)
        elif only is None or fp.GetReference() in only:
            pending.append(fp)
    # Each part is followed by the capacitors that decouple it, so decoupling gets the spots
    # closest to the pins before anything else competes for them.
    ordered = []
    owners = [fp for fp in board.GetFootprints() if not fp.GetReference().startswith("C")]
    for owner in sorted(owners, key=lambda f: (not f.IsLocked(), priority(f))):
        if not owner.IsLocked() and owner in pending:
            ordered.append(owner)
        for fp in sorted(pending, key=priority):
            target = near.get(fp.GetReference())
            if target and target[0] == owner.GetReference() and fp not in ordered:
                ordered.append(fp)
    ordered += [fp for fp in sorted(pending, key=priority) if fp not in ordered]
    failed = []
    for fp in ordered:
        if placer.place(fp):
            fp.SetLocked(True)
        else:
            failed.append(fp.GetReference())
    return failed

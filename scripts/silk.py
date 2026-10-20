"""Silkscreen: readable reference designators, DUT header pin labels, board marking.

- References: 1.0 mm text (JLCPCB minimum readable height), horizontal, placed on the first free
  side of the courtyard (top, bottom, left, right) without touching pads, other courtyards or
  other text, so that no reference can be read as belonging to a neighbour. ICs, connectors,
  diodes, transistors, switches and test points are placed first; a passive reference that finds
  no room is moved to F.Fab (assembly drawing) only. Test points show their net name instead.
- Header pin labels: net name next to each pin of the DUT headers.
- Bottom-side parts (test points, solder jumpers, unfitted parts) get their text on B.SilkS,
  checked against bottom-side obstacles and through-hole parts only.
- A key part whose reference finds no room on the top side gets it on B.SilkS, right under the
  part (same position seen through the board), so it cannot be read as a neighbour's.
Runs inside KiCad's Python (pcbnew).
"""

import pcbnew

from autoplace import bottom_only, courtyard_box, overlaps, to_mm

TEXT_H = 1.0
TEXT_T = 0.15
GAP = 0.25
# A reference must be within OWN_MAX of its own courtyard and closer to it than to any other.
OWN_MAX = 2.0
# Reference prefixes that always get a silkscreen reference (placed before the passives).
KEY_PARTS = ("U", "J", "D", "Q", "F", "L", "SW", "TP", "JP")

# Short pin labels for the DUT headers (net name -> silkscreen text).
PIN_LABELS = {
    "5V_DUT": "5V", "5V_SW": "5VS", "3V3_DUT": "3V3", "3V3_SW": "3VS", "VIO": "VIO",
    "GND": "GND", "SWDIO": "DIO", "SWCLK": "CLK", "SWO": "SWO", "RESET": "RST", "BOOT": "BT",
    "I2C_SDA": "SDA", "I2C_SCL": "SCL", "SPI_SCK": "SCK", "SPI_MOSI": "MOSI",
    "SPI_MISO": "MISO", "SPI_CS": "CS", "TX": "TX", "RX": "RX", "AIN1": "AI1", "AIN2": "AI2",
    "AOUT": "AO", "OUT1": "O1", "OUT2": "O2", "OUT3": "O3", "OUT4": "O4",
    "IN1": "I1", "IN2": "I2", "IN3": "I3", "IN4": "I4",
}


def mm(v):
    return pcbnew.FromMM(v)


def box_distance(point, box):
    """Distance from a point to a box (0 inside)."""
    dx = max(box[0] - point[0], 0.0, point[0] - box[2])
    dy = max(box[1] - point[1], 0.0, point[1] - box[3])
    return (dx * dx + dy * dy) ** 0.5


def text_box(item):
    bb = item.GetBoundingBox()
    return (to_mm(bb.GetX()), to_mm(bb.GetY()), to_mm(bb.GetRight()), to_mm(bb.GetBottom()))


class Silk:
    def __init__(self, board, area, refs=None, bottom=False):
        """refs: footprints taken into account (default: all); see refresh(). bottom: work on
        B.SilkS against bottom-side parts and through-hole parts (present on both sides)."""
        self.board = board
        self.area = area
        self.bottom = bottom
        self.texts = []
        self.refresh(refs)

    def on_side(self, fp):
        if self.bottom:
            return bottom_only(fp) or any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
                                          for p in fp.Pads())
        return not bottom_only(fp)

    def refresh(self, refs=None):
        """Recompute pad and courtyard obstacles, e.g. after more footprints were placed."""
        fps = [fp for fp in self.board.GetFootprints()
               if (refs is None or fp.GetReference() in refs) and self.on_side(fp)]
        self.obstacles = []
        for fp in fps:
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                self.obstacles.append((to_mm(bb.GetX()), to_mm(bb.GetY()),
                                       to_mm(bb.GetRight()), to_mm(bb.GetBottom())))
        self.courtyards = {fp.GetReference(): courtyard_box(fp) for fp in fps}

    def _free(self, box, owner):
        x0, y0, x1, y1 = self.area
        if box[0] < x0 or box[1] < y0 or box[2] > x1 or box[3] > y1:
            return False
        if any(overlaps(box, o, GAP) for o in self.obstacles):
            return False
        if any(overlaps(box, t, GAP) for t in self.texts):
            return False
        if any(overlaps(box, c, 0.0) for ref, c in self.courtyards.items() if ref != owner):
            return False
        centre = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
        own = box_distance(centre, self.courtyards[owner])
        return own <= OWN_MAX and all(own < box_distance(centre, c)
                                      for ref, c in self.courtyards.items() if ref != owner)

    def place_reference(self, fp):
        """Place the reference (the net name for a test point) on the silkscreen."""
        silk_layer = pcbnew.B_SilkS if self.bottom else pcbnew.F_SilkS
        fab_layer = pcbnew.B_Fab if self.bottom else pcbnew.F_Fab
        if fp.GetReference().startswith("TP"):
            ref = fp.Value()
            fp.Reference().SetLayer(fab_layer)
        else:
            ref = fp.Reference()
        ref.SetMirrored(self.bottom)
        ref.SetTextSize(pcbnew.VECTOR2I(mm(TEXT_H), mm(TEXT_H)))
        ref.SetTextThickness(mm(TEXT_T))
        ref.SetKeepUpright(True)
        ref.SetTextAngleDegrees(0)
        ref.SetLayer(silk_layer)
        ref.SetVisible(True)
        cx0, cy0, cx1, cy1 = self.courtyards[fp.GetReference()]
        cx, cy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        vertical_part = (cy1 - cy0) > (cx1 - cx0)
        angles = (90, 0) if vertical_part else (0, 90)
        for angle in angles:
            ref.SetTextAngleDegrees(angle)
            ref.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
            tb = text_box(ref)
            w, h = tb[2] - tb[0], tb[3] - tb[1]
            for extra in (0.0, 0.6, 1.2, 2.0):
                g = GAP + extra
                candidates = [
                    (cx, cy0 - h / 2 - g), (cx, cy1 + h / 2 + g),
                    (cx0 - w / 2 - g, cy), (cx1 + w / 2 + g, cy),
                    (cx0 - w / 2 - g, cy0 - h / 2 - g), (cx1 + w / 2 + g, cy0 - h / 2 - g),
                    (cx0 - w / 2 - g, cy1 + h / 2 + g), (cx1 + w / 2 + g, cy1 + h / 2 + g),
                ]
                for x, y in candidates:
                    ref.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
                    box = text_box(ref)
                    if self._free(box, fp.GetReference()):
                        self.texts.append(box)
                        return True
        ref.SetTextAngleDegrees(0)
        # No room on the silkscreen: keep the reference on the assembly drawing only.
        ref.SetLayer(fab_layer)
        ref.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
        return False

    def place_under(self, fp):
        """Bottom silkscreen only: put a top-side part's reference under its own centre (or as
        close as possible inside its courtyard)."""
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(TEXT_H), mm(TEXT_H)))
        ref.SetTextThickness(mm(TEXT_T))
        ref.SetKeepUpright(True)
        ref.SetLayer(pcbnew.B_SilkS)
        ref.SetMirrored(True)
        ref.SetVisible(True)
        cx0, cy0, cx1, cy1 = courtyard_box(fp)
        cx, cy = (cx0 + cx1) / 2, (cy0 + cy1) / 2
        vertical_part = (cy1 - cy0) > (cx1 - cx0)
        for angle in ((90, 0) if vertical_part else (0, 90)):
            ref.SetTextAngleDegrees(angle)
            for dx, dy in ((0, 0), (0, -0.5), (0, 0.5), (-0.5, 0), (0.5, 0)):
                ref.SetPosition(pcbnew.VECTOR2I(mm(cx + dx), mm(cy + dy)))
                box = text_box(ref)
                inside = (box[0] >= cx0 - GAP and box[2] <= cx1 + GAP and
                          box[1] >= cy0 - GAP and box[3] <= cy1 + GAP)
                if (inside and not any(overlaps(box, o, GAP) for o in self.obstacles)
                        and not any(overlaps(box, o, GAP) for o in self.texts)):
                    self.texts.append(box)
                    return True
        ref.SetMirrored(False)
        return False

    def add_text(self, text, x, y, angle=0, size=TEXT_H):
        t = pcbnew.PCB_TEXT(self.board)
        t.SetText(text)
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
        t.SetTextThickness(mm(TEXT_T if size <= 1.2 else 0.2))
        t.SetTextAngleDegrees(angle)
        t.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        self.board.Add(t)
        self.texts.append(text_box(t))
        return t


def pin_labels(silk, fp, side):
    """Label each pin of a DUT header and put its reference in the gap before pin 1.
    side: 'above' (bottom-row headers) or 'left' (right column)."""
    pin1 = fp.FindPadByNumber("1")
    x1, y1 = to_mm(pin1.GetPosition().x), to_mm(pin1.GetPosition().y)
    ref = fp.Reference()
    ref.SetTextSize(pcbnew.VECTOR2I(mm(TEXT_H), mm(TEXT_H)))
    ref.SetTextThickness(mm(TEXT_T))
    ref.SetLayer(pcbnew.F_SilkS)
    ref.SetVisible(True)
    ref.SetKeepUpright(True)
    if side == "above":
        ref.SetTextAngleDegrees(90)
        ref.SetPosition(pcbnew.VECTOR2I(mm(x1 - 1.9), mm(y1 - 3.4)))
    else:
        ref.SetTextAngleDegrees(0)
        ref.SetPosition(pcbnew.VECTOR2I(mm(x1 - 3.7), mm(y1 - 1.9)))
    silk.texts.append(text_box(ref))
    for pad in fp.Pads():
        label = PIN_LABELS.get(pad.GetNetname().split("/")[-1])
        if not label:
            continue
        x, y = to_mm(pad.GetPosition().x), to_mm(pad.GetPosition().y)
        if side == "above":
            t = silk.add_text(label, x, y - 2.4 - 0.5 * len(label) * TEXT_H * 0.6, angle=90)
        else:
            t = silk.add_text(label, x - 2.3 - 0.35 * len(label) * TEXT_H, y)
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)


def reserve(board, area, headers_bottom, headers_right, marking):
    """Before auto-placement: header pin labels, board marking and the references of the
    already placed (locked) key parts. Returns the Silk object; its texts are keepouts for the
    auto-placer."""
    locked = {fp.GetReference() for fp in board.GetFootprints() if fp.IsLocked()}
    silk = Silk(board, area, locked)
    for fp in board.GetFootprints():
        if fp.GetReference() in headers_bottom:
            pin_labels(silk, fp, "above")
        elif fp.GetReference() in headers_right:
            pin_labels(silk, fp, "left")
    for text, x, y, size in marking:
        silk.add_text(text, x, y, size=size)
    silk.done = set(headers_bottom) | set(headers_right)
    for fp in sorted(board.GetFootprints(), key=lambda f: -len(f.Pads())):
        ref = fp.GetReference()
        if (ref in locked and ref not in silk.done and ref.startswith(KEY_PARTS)
                and not bottom_only(fp) and silk.place_reference(fp)):
            silk.done.add(ref)
    return silk


def finish(silk):
    """After auto-placement: references of every other part, key parts first; a key part that
    finds no room on top gets its reference under it on B.SilkS. Returns the refs moved to the
    assembly drawing (F.Fab / B.Fab) only."""
    board = silk.board
    silk.refresh()
    bottom = Silk(board, silk.area, bottom=True)
    hidden, under = [], []
    remaining = [fp for fp in board.GetFootprints() if fp.GetReference() not in silk.done]
    for fp in sorted(remaining, key=lambda f: (not f.GetReference().startswith(KEY_PARTS),
                                                -len(f.Pads()))):
        if fp.GetReference().startswith("H"):
            fp.Reference().SetVisible(False)
            continue
        side = bottom if bottom_only(fp) else silk
        if side.place_reference(fp):
            continue
        if (side is silk and fp.GetReference().startswith(KEY_PARTS)
                and not fp.GetReference().startswith("TP") and bottom.place_under(fp)):
            under.append(fp.GetReference())
            continue
        hidden.append(fp.GetReference())
    for fp in board.GetFootprints():
        if not fp.GetReference().startswith("TP"):
            fp.Value().SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
    if under:
        print("references under their part (B.SilkS):", " ".join(under))
    return hidden

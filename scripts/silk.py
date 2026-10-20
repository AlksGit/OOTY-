"""Silkscreen: readable reference designators, DUT header pin labels, board marking.

- References: 1.0 mm text (JLCPCB minimum readable height), horizontal, placed on the first free
  side of the courtyard (top, bottom, left, right) without touching pads, courtyards or other
  text. A reference that cannot be placed is moved to F.Fab (assembly drawing) only.
- Header pin labels: net name next to each pin of the DUT headers.
Runs inside KiCad's Python (pcbnew).
"""

import pcbnew

from autoplace import courtyard_box, overlaps, to_mm

TEXT_H = 1.0
TEXT_T = 0.15
GAP = 0.25

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


def text_box(item):
    bb = item.GetBoundingBox()
    return (to_mm(bb.GetX()), to_mm(bb.GetY()), to_mm(bb.GetRight()), to_mm(bb.GetBottom()))


class Silk:
    def __init__(self, board, area):
        self.board = board
        self.area = area
        self.obstacles = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                bb = pad.GetBoundingBox()
                self.obstacles.append((to_mm(bb.GetX()), to_mm(bb.GetY()),
                                       to_mm(bb.GetRight()), to_mm(bb.GetBottom())))
        self.courtyards = {fp.GetReference(): courtyard_box(fp) for fp in board.GetFootprints()}
        self.texts = []

    def _free(self, box, owner):
        x0, y0, x1, y1 = self.area
        if box[0] < x0 or box[1] < y0 or box[2] > x1 or box[3] > y1:
            return False
        if any(overlaps(box, o, GAP) for o in self.obstacles):
            return False
        if any(overlaps(box, t, GAP) for t in self.texts):
            return False
        # Text may run over a neighbour's body, but never over an IC or connector courtyard.
        return not any(overlaps(box, c, 0.0) for ref, c in self.courtyards.items()
                       if ref != owner and ref[0] in "UJ")

    def place_reference(self, fp):
        ref = fp.Reference()
        ref.SetTextSize(pcbnew.VECTOR2I(mm(TEXT_H), mm(TEXT_H)))
        ref.SetTextThickness(mm(TEXT_T))
        ref.SetKeepUpright(True)
        ref.SetTextAngleDegrees(0)
        ref.SetLayer(pcbnew.F_SilkS)
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
        ref.SetLayer(pcbnew.F_Fab)
        ref.SetPosition(pcbnew.VECTOR2I(mm(cx), mm(cy)))
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
    """Label each pin of a DUT header. side: 'above' (bottom-row headers) or 'left' (right column)."""
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


def run(board, area, headers_bottom, headers_right, marking):
    silk = Silk(board, area)
    for fp in board.GetFootprints():
        if fp.GetReference() in headers_bottom:
            pin_labels(silk, fp, "above")
        elif fp.GetReference() in headers_right:
            pin_labels(silk, fp, "left")
    for text, x, y, size in marking:
        silk.add_text(text, x, y, size=size)
    hidden = []
    for fp in sorted(board.GetFootprints(), key=lambda f: -len(f.Pads())):
        if fp.GetReference().startswith("H"):
            fp.Reference().SetVisible(False)
            continue
        if not silk.place_reference(fp):
            hidden.append(fp.GetReference())
    for fp in board.GetFootprints():
        fp.Value().SetLayer(pcbnew.F_Fab)
    return hidden

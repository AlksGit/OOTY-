"""Netlist-driven KiCad schematic generator.

Each part pin is connected through a short wire stub to a net label (local or global)
or to a power symbol. Sheets are laid out automatically as columns of functional groups.
Files are written in the KiCad 8 format (20231120) and then upgraded with kicad-cli.
"""

import math
import subprocess
import uuid
from dataclasses import dataclass, field

from kicad_env import PROJECT_DIR, PROJECT_NAME, kicad_cli
import symlib
from sexpr import Sym, dumps, fmt_num

GRID = 1.27
STUB = 2.54
FONT = 1.27
CHAR_W = 1.0           # approximate label character width (mm) at 1.27 mm font
SCH_VERSION = "20231120"

# Nets drawn with power symbols instead of labels.
POWER_SYMBOLS = {
    "GND": "power:GND",
    "+3V3": "power:+3V3",
    "+5V": "power:+5V",
    "VBUS": "power:VBUS",
}

PAPER = {"A4": (297.0, 210.0), "A3": (420.0, 297.0)}
MARGIN = 20.0
NOTES_HEIGHT = 30.0    # reserved band above the bottom border for sheet notes
POWER_STUB = 3.81


_UUID_NS = uuid.UUID("6f6f7479-0000-4000-8000-000000000000")
_uid_scope = {"name": "global", "count": 0}


def uid(key=None):
    """Deterministic UUID: from `key` if given, else from the current scope and a counter.

    Stable UUIDs keep the schematic <-> PCB link (footprint paths) across regenerations.
    """
    if key is None:
        _uid_scope["count"] += 1
        key = f"{_uid_scope['name']}:{_uid_scope['count']}"
    return str(uuid.uuid5(_UUID_NS, key))


def uid_scope(name):
    _uid_scope["name"] = name
    _uid_scope["count"] = 0


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def S(*items):
    return [Sym(items[0]), *items[1:]]


def at(x, y, a=None):
    node = [Sym("at"), Sym(fmt_num(x)), Sym(fmt_num(y))]
    if a is not None:
        node.append(Sym(fmt_num(a)))
    return node


def effects(justify=None, hide=False):
    node = S("effects", S("font", S("size", Sym("1.27"), Sym("1.27"))))
    if justify:
        node.append(S("justify", *[Sym(j) for j in justify.split()]))
    if hide:
        node.append(S("hide", Sym("yes")))
    return node


def yesno(flag):
    return Sym("yes" if flag else "no")


def transform(px, py, rot):
    """Library offset (y up) -> sheet offset (y down) for a CCW rotation `rot`."""
    dx, dy = px, -py
    t = math.radians(rot)
    c, s = round(math.cos(t)), round(math.sin(t))
    return dx * c + dy * s, -dx * s + dy * c


def direction(angle):
    t = math.radians(angle)
    return round(math.cos(t)), -round(math.sin(t))


@dataclass
class Part:
    ref: str
    lib_id: str
    value: str
    nets: dict
    rot: int = 0
    unit: int = 1
    fields: dict = field(default_factory=dict)
    in_bom: bool = True
    dnp: bool = False
    hide_value: bool = False
    x: float = 0.0
    y: float = 0.0


@dataclass
class Group:
    title: str
    parts: list = field(default_factory=list)
    column_break: bool = False


class Sheet:
    def __init__(self, name, title, paper="A3"):
        self.name = name
        self.title = title
        self.paper = paper
        self.groups = []
        self.notes = []
        self.uuid = uid(f"sheet:{name}")

    def group(self, title, column_break=False):
        self.groups.append(Group(title, column_break=column_break))
        return self

    def add(self, ref, lib_id, value, nets, rot=0, unit=1, fields=None, in_bom=True, dnp=False,
            hide_value=False):
        if not self.groups:
            self.group("")
        part = Part(ref, lib_id, value, dict(nets), rot, unit, dict(fields or {}), in_bom, dnp,
                    hide_value)
        self.groups[-1].parts.append(part)
        return part

    def note(self, text):
        self.notes.append(text)

    @property
    def parts(self):
        return [p for g in self.groups for p in g.parts]


# ---------------------------------------------------------------------------
# Geometry helpers


def resolve_pins(part):
    """Return [(pin, net)] for the part unit; nets keyed by pin number or pin name."""
    sym = symlib.load(part.lib_id)
    pins = sym.pins_of_unit(part.unit)
    by_number = {p.number: p for p in pins}
    by_name = {}
    for p in pins:
        by_name.setdefault(p.name, []).append(p)
    resolved = {}
    for key, net in part.nets.items():
        if key in by_number:
            resolved[key] = (by_number[key], net)
        elif key in by_name:
            for p in by_name[key]:
                resolved[p.number] = (p, net)
        else:
            raise KeyError(f"{part.ref}: pin '{key}' not found in {part.lib_id}")
    missing = [p for p in pins if p.number not in resolved]
    if missing:
        names = ", ".join(f"{p.number}:{p.name}" for p in missing)
        raise ValueError(f"{part.ref}: unassigned pins {names}")
    return list(resolved.values())


def body_box(part):
    """Approximate symbol body box (sheet offsets) from pins and graphics."""
    sym = symlib.load(part.lib_id)
    pts = []
    for p in sym.pins_of_unit(part.unit):
        pts.append(transform(p.x, p.y, part.rot))
    for sub in sym.node:
        if isinstance(sub, list) and sub and sub[0] == "symbol":
            for g in sub[2:]:
                if not isinstance(g, list):
                    continue
                for item in g:
                    if isinstance(item, list) and item and item[0] in ("start", "end", "center"):
                        pts.append(transform(float(item[1]), float(item[2]), part.rot))
                    if isinstance(item, list) and item and item[0] == "pts":
                        for xy in item[1:]:
                            pts.append(transform(float(xy[1]), float(xy[2]), part.rot))
    xs = [p[0] for p in pts] or [0]
    ys = [p[1] for p in pts] or [0]
    return min(xs), min(ys), max(xs), max(ys)


def power_rotation(lib_id, outward):
    """Rotation that makes a power symbol point along the stub direction (sheet angle)."""
    sym = symlib.load(lib_id)
    ys = []
    for sub in sym.node:
        if isinstance(sub, list) and sub and sub[0] == "symbol":
            for g in sub[2:]:
                if isinstance(g, list):
                    for item in g:
                        if isinstance(item, list) and item and item[0] == "pts":
                            ys += [float(xy[2]) for xy in item[1:]]
    points_down = sum(ys) < 0
    natural = 270 if points_down else 90
    return int((outward - natural) % 360)


def label_extent(net):
    return STUB + len(net) * CHAR_W + 3.0


def footprint_box(part):
    """Box including stubs and labels, as offsets from the part origin."""
    x0, y0, x1, y1 = body_box(part)
    for pin, net in resolve_pins(part):
        if net is None:
            continue
        px, py = transform(pin.x, pin.y, part.rot)
        dx, dy = direction(pin.angle + 180 + part.rot)
        ext = 6.0 if net in POWER_SYMBOLS else label_extent(net)
        ex, ey = px + dx * ext, py + dy * ext
        x0, x1 = min(x0, ex), max(x1, ex)
        y0, y1 = min(y0, ey), max(y1, ey)
    return x0 - 2.54, y0 - 3.81, x1 + 2.54, y1 + 3.81


def layout(sheet):
    """Place groups in columns; parts stacked vertically inside each group."""
    width, height = PAPER[sheet.paper]
    x = MARGIN
    y = MARGIN + 10
    col_width = 0.0
    for grp in sheet.groups:
        boxes = [footprint_box(p) for p in grp.parts]
        grp_h = sum(b[3] - b[1] for b in boxes) + 8.0
        grp_w = max([b[2] - b[0] for b in boxes] + [len(grp.title) * 1.7])
        limit = height - MARGIN - (NOTES_HEIGHT if sheet.notes else 0)
        if grp.column_break or (y + grp_h > limit and y > MARGIN + 10):
            x += col_width + 8.0
            y = MARGIN + 10
            col_width = 0.0
        grp.origin = (snap(x), snap(y))
        cy = y + 6.0
        for part, box in zip(grp.parts, boxes):
            part.x = snap(x - box[0])
            part.y = snap(cy - box[1])
            cy += box[3] - box[1]
        y = cy + 8.0
        col_width = max(col_width, grp_w)
    if x + col_width > width - MARGIN + 1e-6:
        raise ValueError(f"sheet {sheet.name}: content too wide ({x + col_width:.0f} mm)")


# ---------------------------------------------------------------------------
# Serialization


class Writer:
    def __init__(self, root_uuid):
        self.root_uuid = root_uuid
        self.pwr_index = 0

    def next_pwr(self, prefix):
        self.pwr_index += 1
        return f"{prefix}{self.pwr_index:03d}"


def instance_node(part, ref, sym, path, value, fields, pos, in_bom, on_board=True,
                  hide_value=False, dnp=False, outward=None):
    x, y = pos
    x0, y0, x1, y1 = body_box(part)
    node = S("symbol", S("lib_id", part.lib_id), at(x, y, part.rot), S("unit", Sym(str(part.unit))),
             S("exclude_from_sim", Sym("no")), S("in_bom", yesno(in_bom)),
             S("on_board", yesno(on_board)), S("dnp", yesno(dnp)),
             S("fields_autoplaced", Sym("yes")), S("uuid", uid(f"symbol:{path}:{ref}")))
    ref_hide = ref.startswith("#")
    # Field angles are stored in sheet orientation; keep text horizontal on rotated symbols.
    fa = 90 if part.rot in (90, 270) else 0
    cx = snap(x + (x0 + x1) / 2)
    if len(sym.pins) >= 3:
        ref_at, ref_just = at(snap(x + x1), snap(y + y0 - 2.54), fa), "right"
    else:
        ref_at, ref_just = at(cx, snap(y + y0 - 1.27), fa), None
    node.append(S("property", "Reference", ref, ref_at, effects(ref_just, hide=ref_hide)))
    if outward is None:
        val_at, val_just = at(cx, snap(y + y1 + 1.27), fa), None
    elif outward == 0:
        val_at, val_just = at(snap(x + x1 + 0.6), y, 0), "left"
    elif outward == 180:
        val_at, val_just = at(snap(x + x0 - 0.6), y, 0), "right"
    elif outward == 90:
        val_at, val_just = at(x, snap(y + y0 - 0.8), 0), None
    else:
        val_at, val_just = at(x, snap(y + y1 + 1.6), 0), None
    if outward is not None and part.rot in (90, 270):
        val_at[3] = Sym("90")
        # Justification is applied in the rotated symbol frame.
        if val_just and part.rot == 90:
            val_just = {"left": "right", "right": "left"}[val_just]
    node.append(S("property", "Value", value, val_at, effects(val_just, hide=hide_value)))
    for key in ("Footprint", "Datasheet", "Description"):
        node.append(S("property", key, fields.get(key, ""), at(x, y, 0), effects(hide=True)))
    for key, val in fields.items():
        if key not in ("Footprint", "Datasheet", "Description"):
            node.append(S("property", key, val, at(x, y, 0), effects(hide=True)))
    for pin in sym.pins_of_unit(part.unit):
        node.append(S("pin", pin.number, S("uuid", uid())))
    node.append(S("instances", S("project", PROJECT_NAME,
                                 S("path", path, S("reference", ref), S("unit", Sym(str(part.unit)))))))
    return node


def label_node(kind, net, x, y, angle):
    left = angle in (0, 90)
    if kind == "global":
        return S("global_label", net, S("shape", Sym("bidirectional")), at(x, y, angle),
                 S("fields_autoplaced", Sym("yes")),
                 effects("left" if left else "right"), S("uuid", uid()),
                 S("property", "Intersheetrefs", "${INTERSHEET_REFS}", at(x, y, angle),
                   effects("left" if left else "right", hide=True)))
    return S("label", net, at(x, y, angle), S("fields_autoplaced", Sym("yes")),
             effects("left bottom" if left else "right bottom"), S("uuid", uid()))


def wire_node(x0, y0, x1, y1):
    return S("wire", S("pts", S("xy", Sym(fmt_num(x0)), Sym(fmt_num(y0))),
                       S("xy", Sym(fmt_num(x1)), Sym(fmt_num(y1)))),
             S("stroke", S("width", Sym("0")), S("type", Sym("default"))), S("uuid", uid()))


def sheet_header(sheet_uuid, title, paper, rev, date):
    return [Sym("kicad_sch"), S("version", Sym(SCH_VERSION)), S("generator", "eeschema"),
            S("generator_version", "8.0"), S("uuid", sheet_uuid), S("paper", paper),
            S("title_block", S("title", title), S("date", date), S("rev", rev),
              S("company", PROJECT_NAME))]


def build_sheet(sheet, writer, global_nets, bom_fields, path, rev, date):
    uid_scope(sheet.name)
    layout(sheet)
    lib_ids = {p.lib_id for p in sheet.parts}
    body = []
    for part in sheet.parts:
        sym = symlib.load(part.lib_id)
        fields = dict(bom_fields(part))
        fields.update(part.fields)
        body.append(instance_node(part, part.ref, sym, path, part.value, fields, (part.x, part.y),
                                  part.in_bom, hide_value=part.hide_value, dnp=part.dnp))
        power_ends = {}
        for pin, net in resolve_pins(part):
            px, py = transform(pin.x, pin.y, part.rot)
            px, py = snap(part.x + px), snap(part.y + py)
            if net is None:
                body.append(S("no_connect", at(px, py), S("uuid", uid())))
                continue
            vis = (pin.angle + 180 + part.rot) % 360
            dx, dy = direction(vis)
            length = POWER_STUB if net in POWER_SYMBOLS else STUB
            ex, ey = snap(px + dx * length), snap(py + dy * length)
            body.append(wire_node(px, py, ex, ey))
            if net in POWER_SYMBOLS:
                power_ends.setdefault((net, vis), []).append((ex, ey))
            else:
                kind = "global" if net in global_nets else "local"
                body.append(label_node(kind, net, ex, ey, vis))
        # Same power net on the same side: join stub ends with one wire and one symbol.
        for (net, vis), ends in power_ends.items():
            ends.sort()
            for (x0, y0), (x1, y1) in zip(ends, ends[1:]):
                body.append(wire_node(x0, y0, x1, y1))
            for jx, jy in ends[1:-1]:
                body.append(S("junction", at(jx, jy), S("diameter", Sym("0")),
                              S("color", Sym("0"), Sym("0"), Sym("0"), Sym("0")), S("uuid", uid())))
            lib_id = POWER_SYMBOLS[net]
            lib_ids.add(lib_id)
            pwr = Part("", lib_id, net, {}, rot=power_rotation(lib_id, vis))
            body.append(instance_node(pwr, writer.next_pwr("#PWR"), symlib.load(lib_id), path,
                                      net, {}, ends[0], in_bom=False, outward=vis))
    # Group titles and notes.
    for grp in sheet.groups:
        if grp.title:
            gx, gy = grp.origin
            body.append(S("text", grp.title, S("exclude_from_sim", Sym("no")), at(gx, gy, 0),
                          S("effects", S("font", S("size", Sym("2"), Sym("2")), S("bold", Sym("yes"))),
                            S("justify", Sym("left"), Sym("bottom"))), S("uuid", uid())))
    width, height = PAPER[sheet.paper]
    for i, text in enumerate(sheet.notes):
        body.append(S("text", text, S("exclude_from_sim", Sym("no")),
                      at(MARGIN, snap(height - MARGIN - NOTES_HEIGHT + 8 + i * 5), 0),
                      effects("left bottom"), S("uuid", uid())))
    node = sheet_header(sheet.uuid, sheet.title, sheet.paper, rev, date)
    node.append(S("lib_symbols", *[symlib.load(l).node for l in sorted(lib_ids)]))
    node.extend(body)
    return node


def build_root(root_uuid, title, sheets, rev, date, notes):
    node = sheet_header(root_uuid, title, "A4", rev, date)
    node.append(S("lib_symbols"))
    x, y = 30.0, 40.0
    for i, sheet in enumerate(sheets):
        w, h = 50.8, 20.32
        node.append(S("sheet", at(x, y), S("size", Sym(fmt_num(w)), Sym(fmt_num(h))),
                      S("fields_autoplaced", Sym("yes")),
                      S("stroke", S("width", Sym("0.1524")), S("type", Sym("solid"))),
                      S("fill", S("color", Sym("0"), Sym("0"), Sym("0"), Sym("0.0000"))),
                      S("uuid", sheet.uuid),
                      S("property", "Sheetname", sheet.name, at(x, snap(y - 0.7), 0),
                        effects("left bottom")),
                      S("property", "Sheetfile", f"{sheet.name}.kicad_sch",
                        at(x, snap(y + h + 0.6), 0), effects("left top")),
                      S("instances", S("project", PROJECT_NAME,
                                       S("path", f"/{root_uuid}", S("page", str(i + 2)))))))
        x += 63.5
        if x > 230:
            x = 30.0
            y += 40.64
    for i, text in enumerate(notes):
        node.append(S("text", text, S("exclude_from_sim", Sym("no")), at(30, snap(150 + i * 5), 0),
                      effects("left bottom"), S("uuid", uid())))
    node.append(S("sheet_instances", S("path", "/", S("page", "1"))))
    return node


def write_project(sheets, bom_fields, title, rev, date, root_notes=()):
    """Write the root schematic and all sub-sheets, then upgrade them to the KiCad format."""
    nets_per_sheet = {}
    for sheet in sheets:
        nets = set()
        for part in sheet.parts:
            nets.update(n for n in part.nets.values() if n and n not in POWER_SYMBOLS)
        nets_per_sheet[sheet.name] = nets
    global_nets = {n for s in nets_per_sheet.values() for n in s
                   if sum(n in other for other in nets_per_sheet.values()) > 1}

    root_uuid = uid("root")
    writer = Writer(root_uuid)
    files = []
    for sheet in sheets:
        node = build_sheet(sheet, writer, global_nets, bom_fields,
                           f"/{root_uuid}/{sheet.uuid}", rev, date)
        path = PROJECT_DIR / f"{sheet.name}.kicad_sch"
        path.write_text(dumps(node) + "\n", encoding="utf-8", newline="\n")
        files.append(path)
    uid_scope("root")
    root = PROJECT_DIR / f"{PROJECT_NAME}.kicad_sch"
    root.write_text(dumps(build_root(root_uuid, title, sheets, rev, date, root_notes)) + "\n",
                    encoding="utf-8", newline="\n")
    files.append(root)
    for path in files:
        subprocess.run([kicad_cli(), "sch", "upgrade", "--force", str(path)], check=True,
                       capture_output=True)
    return files

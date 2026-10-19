"""Load KiCad library symbols, flatten `extends`, and expose pin geometry."""

import copy
from dataclasses import dataclass, field
from pathlib import Path

from kicad_env import PROJECT_DIR, PROJECT_NAME
from sexpr import Sym, find, find_all, parse

KICAD_SYMBOL_DIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")
PROJECT_SYMBOL_LIB = PROJECT_DIR / "lib" / f"{PROJECT_NAME}.kicad_sym"


@dataclass
class Pin:
    number: str
    name: str
    etype: str
    x: float
    y: float
    angle: float
    unit: int
    alternates: list = field(default_factory=list)


@dataclass
class LibSymbol:
    lib_id: str
    node: list           # flattened symbol node, named with the full lib_id
    pins: list           # all pins, all units
    is_power: bool

    def pins_of_unit(self, unit):
        return [p for p in self.pins if p.unit in (0, unit)]


_lib_cache = {}
_sym_cache = {}


def _library_path(lib):
    if lib == PROJECT_NAME:
        return PROJECT_SYMBOL_LIB
    return KICAD_SYMBOL_DIR / f"{lib}.kicad_sym"


def _load_library(lib):
    if lib not in _lib_cache:
        tree = parse(_library_path(lib).read_text(encoding="utf-8"))
        _lib_cache[lib] = {s[1]: s for s in find_all(tree, "symbol")}
    return _lib_cache[lib]


def _flatten(lib, name):
    """Return a deep copy of symbol `name`, with any `extends` parent merged in."""
    symbols = _load_library(lib)
    sym = copy.deepcopy(symbols[name])
    ext = find(sym, "extends")
    if ext is None:
        return sym
    parent = _flatten(lib, ext[1])
    child_props = {p[1]: p for p in find_all(sym, "property")}
    merged = [Sym("symbol"), name]
    for item in parent[2:]:
        if isinstance(item, list) and item[0] == "property" and item[1] in child_props:
            merged.append(child_props.pop(item[1]))
        elif isinstance(item, list) and item[0] == "symbol":
            sub = copy.deepcopy(item)
            sub[1] = name + sub[1][len(parent[1]):]
            merged.append(sub)
        else:
            merged.append(item)
    for prop in child_props.values():
        merged.insert(2, prop)
    return merged


def _unit_of(subname):
    # Sub-symbol names end with _<unit>_<style>.
    unit, style = subname.rsplit("_", 2)[-2:]
    return int(unit), int(style)


def load(lib_id):
    """Return the LibSymbol for 'Lib:Name'."""
    if lib_id in _sym_cache:
        return _sym_cache[lib_id]
    lib, name = lib_id.split(":", 1)
    node = _flatten(lib, name)
    pins = []
    for sub in find_all(node, "symbol"):
        unit, style = _unit_of(sub[1])
        if style == 2:
            continue
        for pin in find_all(sub, "pin"):
            at = find(pin, "at")
            alternates = [a[1] for a in find_all(pin, "alternate")]
            pins.append(Pin(
                number=find(pin, "number")[1],
                name=find(pin, "name")[1],
                etype=str(pin[1]),
                x=float(at[1]), y=float(at[2]), angle=float(at[3]),
                unit=unit,
                alternates=alternates,
            ))
    named = copy.deepcopy(node)
    named[1] = lib_id
    sym = LibSymbol(lib_id, named, pins, find(node, "power") is not None)
    _sym_cache[lib_id] = sym
    return sym

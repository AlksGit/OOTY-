"""Generate the project symbol library lib/OOTY.kicad_sym.

Symbols missing from the official KiCad libraries:
- AP22653W6: Diodes AP22653 current-limited switch, SOT26 (DS41186 Rev. 5-2, Pin Descriptions):
  1 IN, 2 GND, 3 EN (active high), 4 FAULT (open drain, active low), 5 ILIM, 6 OUT.
- TLV9001IDBV: TI TLV9001 in SOT-23-5 (DBV): 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+.
  Same pin mapping as the official OPA333xxDBV symbol, whose graphics are reused.

Usage: python scripts/build_symbols.py
"""

import copy
import subprocess

from kicad_env import kicad_cli
import symlib
from sexpr import Sym, dumps, find_all
from schgen import S, at, effects

AP22653_DATASHEET = "https://www.diodes.com/assets/Datasheets/AP22652_53_52A_53A.pdf"
TLV9001_DATASHEET = "https://www.ti.com/lit/ds/symlink/tlv9001.pdf"


def prop(name, value, x, y, hide=False):
    return S("property", name, value, at(x, y, 0), effects(hide=hide))


def pin(etype, x, y, angle, name, number):
    return S("pin", Sym(etype), Sym("line"), at(x, y, angle), S("length", Sym("2.54")),
             S("name", name, effects()), S("number", number, effects()))


def ap22653():
    name = "AP22653W6"
    body = S("symbol", f"{name}_0_1",
             S("rectangle", S("start", Sym("-7.62"), Sym("5.08")), S("end", Sym("7.62"), Sym("-7.62")),
               S("stroke", S("width", Sym("0.254")), S("type", Sym("default"))),
               S("fill", S("type", Sym("background")))))
    pins = S("symbol", f"{name}_1_1",
             pin("power_in", -10.16, 2.54, 0, "IN", "1"),
             pin("input", -10.16, -2.54, 0, "EN", "3"),
             pin("power_out", 10.16, 2.54, 180, "OUT", "6"),
             pin("open_collector", 10.16, -2.54, 180, "~{FAULT}", "4"),
             pin("power_in", -2.54, -10.16, 90, "GND", "2"),
             pin("passive", 2.54, -10.16, 90, "ILIM", "5"))
    return S("symbol", name, S("exclude_from_sim", Sym("no")), S("in_bom", Sym("yes")),
             S("on_board", Sym("yes")),
             prop("Reference", "U", 0, 7.62),
             prop("Value", name, 0, -12.7),
             prop("Footprint", "Package_TO_SOT_SMD:SOT-23-6", 0, -15.24, hide=True),
             prop("Datasheet", AP22653_DATASHEET, 0, -17.78, hide=True),
             prop("Description", "Current-limited power switch, adjustable ILIM, active-high EN, "
                                 "open-drain FAULT, output discharge, SOT26", 0, -20.32, hide=True),
             body, pins)


def tlv9001():
    name = "TLV9001IDBV"
    src = copy.deepcopy(symlib.load("Amplifier_Operational:OPA333xxDBV").node)
    old = "OPA333xxDBV"
    src[1] = name
    for sub in find_all(src, "symbol"):
        sub[1] = name + sub[1][len(old):]
    for p in find_all(src, "property"):
        if p[1] == "Value":
            p[2] = name
        elif p[1] == "Datasheet":
            p[2] = TLV9001_DATASHEET
        elif p[1] == "Description":
            p[2] = "1 MHz RRIO single op-amp, SOT-23-5 (DBV)"
        elif p[1] == "Footprint":
            p[2] = "Package_TO_SOT_SMD:SOT-23-5"
        elif p[1] == "ki_keywords":
            p[2] = "single opamp rrio"
    return src


def main():
    lib = [Sym("kicad_symbol_lib"), S("version", Sym("20231120")),
           S("generator", "kicad_symbol_editor"), S("generator_version", "8.0"),
           ap22653(), tlv9001()]
    path = symlib.PROJECT_SYMBOL_LIB
    path.write_text(dumps(lib) + "\n", encoding="utf-8", newline="\n")
    subprocess.run([kicad_cli(), "sym", "upgrade", "--force", str(path)], check=True,
                   capture_output=True)
    print(f"wrote {path.name}")


if __name__ == "__main__":
    main()

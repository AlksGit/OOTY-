"""Create the empty OOTY KiCad project, library tables and output tree.

Idempotent: existing files are never overwritten. Minimal files are written in
an older S-expression format, then upgraded to the installed KiCad format with
`kicad-cli ... upgrade`.

Usage: python scripts/create_project.py
"""

import json
import subprocess
import uuid

from kicad_env import PROJECT_DIR, PROJECT_NAME, kicad_cli, project_file

DIRECTORIES = [
    "bom",
    "scripts",
    f"lib/{PROJECT_NAME}.pretty",
    "out/reports",
    "out/renders",
    "out/fab",
]

PCB_LAYERS = """\
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )
"""


def write_if_missing(path, content):
    """Write content to path unless it already exists. Return True if written."""
    if path.exists():
        print(f"keep    {path.relative_to(PROJECT_DIR)}")
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"create  {path.relative_to(PROJECT_DIR)}")
    return True


def upgrade(kind, path):
    """Upgrade a KiCad file to the installed version format."""
    subprocess.run([kicad_cli(), kind, "upgrade", str(path)], check=True)


def create_directories():
    for rel in DIRECTORIES:
        directory = PROJECT_DIR / rel
        directory.mkdir(parents=True, exist_ok=True)
        keep = directory / ".gitkeep"
        if not any(directory.iterdir()):
            keep.touch()


def create_project_file():
    content = {"meta": {"filename": f"{PROJECT_NAME}.kicad_pro", "version": 1}}
    write_if_missing(project_file(".kicad_pro"), json.dumps(content, indent=2) + "\n")


def create_schematic():
    path = project_file(".kicad_sch")
    content = (
        "(kicad_sch (version 20231120) (generator \"eeschema\") (generator_version \"8.0\")\n"
        f"  (uuid \"{uuid.uuid4()}\")\n"
        "  (paper \"A4\")\n"
        "  (lib_symbols)\n"
        "  (sheet_instances (path \"/\" (page \"1\")))\n"
        ")\n"
    )
    if write_if_missing(path, content):
        upgrade("sch", path)


def create_board():
    path = project_file(".kicad_pcb")
    content = (
        "(kicad_pcb (version 20240108) (generator \"pcbnew\") (generator_version \"8.0\")\n"
        "  (general (thickness 1.6) (legacy_teardrops no))\n"
        "  (paper \"A4\")\n"
        f"{PCB_LAYERS}"
        "  (setup (pad_to_mask_clearance 0))\n"
        "  (net 0 \"\")\n"
        ")\n"
    )
    if write_if_missing(path, content):
        upgrade("pcb", path)


def create_symbol_library():
    path = PROJECT_DIR / "lib" / f"{PROJECT_NAME}.kicad_sym"
    content = (
        "(kicad_symbol_lib (version 20231120) (generator \"kicad_symbol_editor\")"
        " (generator_version \"8.0\"))\n"
    )
    if write_if_missing(path, content):
        upgrade("sym", path)


def create_library_tables():
    write_if_missing(
        PROJECT_DIR / "sym-lib-table",
        "(sym_lib_table\n"
        "  (version 7)\n"
        f"  (lib (name \"{PROJECT_NAME}\")(type \"KiCad\")"
        f"(uri \"${{KIPRJMOD}}/lib/{PROJECT_NAME}.kicad_sym\")(options \"\")"
        f"(descr \"{PROJECT_NAME} project symbols\"))\n"
        ")\n",
    )
    write_if_missing(
        PROJECT_DIR / "fp-lib-table",
        "(fp_lib_table\n"
        "  (version 7)\n"
        f"  (lib (name \"{PROJECT_NAME}\")(type \"KiCad\")"
        f"(uri \"${{KIPRJMOD}}/lib/{PROJECT_NAME}.pretty\")(options \"\")"
        f"(descr \"{PROJECT_NAME} project footprints\"))\n"
        ")\n",
    )


def main():
    create_directories()
    create_project_file()
    create_schematic()
    create_board()
    create_symbol_library()
    create_library_tables()


if __name__ == "__main__":
    main()

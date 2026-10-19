"""Export the schematic to out/OOTY_schematic.pdf and one PNG per sheet in out/renders/.

PNG rendering uses PyMuPDF (pip install pymupdf).

Usage: python scripts/render_schematic.py
"""

import subprocess

import fitz

from kicad_env import PROJECT_DIR, PROJECT_NAME, kicad_cli, project_file

PDF = PROJECT_DIR / "out" / f"{PROJECT_NAME}_schematic.pdf"
RENDERS = PROJECT_DIR / "out" / "renders"


def main():
    subprocess.run([kicad_cli(), "sch", "export", "pdf", "-o", str(PDF),
                    str(project_file(".kicad_sch"))], check=True, capture_output=True)
    RENDERS.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    for i, page in enumerate(doc, 1):
        out = RENDERS / f"schematic_p{i}.png"
        page.get_pixmap(dpi=110).save(out)
        print(f"wrote {out.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()

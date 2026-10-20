"""Export PCB review renders to out/renders/: 3D views, placement SVG, assembly drawing PDF.

Usage: python scripts/render_pcb.py [prefix]   (default prefix: pcb_placement)
"""

import subprocess
import sys

from kicad_env import PROJECT_DIR, kicad_cli, project_file

RENDERS = PROJECT_DIR / "out" / "renders"


def run(*args):
    subprocess.run([kicad_cli(), *args], check=True, capture_output=True)


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else "pcb_placement"
    pcb = str(project_file(".kicad_pcb"))
    RENDERS.mkdir(parents=True, exist_ok=True)
    views = {
        "top": ["--side", "top"],
        "bottom": ["--side", "bottom"],
        "iso": ["--rotate", "-40,0,30", "--perspective"],
    }
    for name, opts in views.items():
        run("pcb", "render", *opts, "-w", "1800", "-h", "1200", "--zoom", "1.3",
            "-o", str(RENDERS / f"{prefix}_{name}.png"), pcb)
    run("pcb", "export", "svg", "--layers", "F.Cu,F.Silkscreen,F.Courtyard,Edge.Cuts",
        "--mode-single", "--page-size-mode", "2", "--exclude-drawing-sheet",
        "-o", str(RENDERS / f"{prefix}_top.svg"), pcb)
    run("pcb", "export", "pdf", "--layers", "F.Fab,Edge.Cuts", "--mode-single",
        "--sketch-pads-on-fab-layers", "--crossout-DNP-footprints-on-fab-layers",
        "--include-border-title", "-o", str(RENDERS / f"{prefix}_assembly_top.pdf"), pcb)
    # Bottom side: test points, bypass bridges, unfitted parts and the references printed under
    # top-side parts that had no room on the top silkscreen.
    run("pcb", "export", "svg", "--layers", "B.Cu,B.Silkscreen,B.Courtyard,Edge.Cuts", "--mirror",
        "--mode-single", "--page-size-mode", "2", "--exclude-drawing-sheet",
        "-o", str(RENDERS / f"{prefix}_bottom.svg"), pcb)
    run("pcb", "export", "pdf", "--layers", "B.Fab,Edge.Cuts", "--mode-single", "--mirror",
        "--sketch-pads-on-fab-layers", "--crossout-DNP-footprints-on-fab-layers",
        "--include-border-title", "-o", str(RENDERS / f"{prefix}_assembly_bottom.pdf"), pcb)
    print(f"renders written to {RENDERS.relative_to(PROJECT_DIR)} ({prefix}_*)")


if __name__ == "__main__":
    main()

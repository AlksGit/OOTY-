# NOTES — OOTY

Décisions de design, calculs, versions d'outils, warnings justifiés.

---

## Environnement (2026-10-19)

| Outil | Version | Remarque |
|---|---|---|
| KiCad / `kicad-cli` | 10.0.7 | `C:\Program Files\KiCad\10.0\bin\kicad-cli.exe` — pas dans le `PATH`, localisé par `scripts/kicad_env.py` (surcharge possible via la variable `KICAD_CLI`) |
| `pcbnew` (bindings SWIG) | 10.0.7 | Disponible uniquement via le Python embarqué de KiCad : `C:\Program Files\KiCad\10.0\bin\python.exe` |
| Python système | 3.11.6 | Utilisé pour les scripts qui ne nécessitent pas `pcbnew` |
| `kiutils` | 1.4.8 | Installé avec `pip install kiutils` (Python système). Conçu pour les formats KiCad 6–8 : **compatibilité avec le format KiCad 10 non garantie**, à vérifier avant usage en écriture |
| Java | absent | Freerouting indisponible pour l'instant (optionnel, à installer seulement si besoin en Phase 5) |

### Conséquences sur l'outillage
- Les fichiers KiCad sont créés dans un format minimal ancien, puis convertis au format KiCad 10 par `kicad-cli sch|pcb|sym upgrade`.
- Pour les manipulations PCB scriptées, on privilégie `pcbnew` via le Python de KiCad. `kiutils` sera validé au cas par cas sur le format KiCad 10.

## Scripts

| Script | Rôle |
|---|---|
| `scripts/kicad_env.py` | Localisation de `kicad-cli` et des fichiers du projet |
| `scripts/create_project.py` | Création idempotente du projet vide, des tables de librairies et de l'arborescence |
| `scripts/run_checks.py` | ERC + DRC en JSON dans `out/reports/` (`--erc-only`, `--drc-only`, `--schematic-parity`) |

## Couches
Le projet est initialisé en **2 couches** cuivre (F.Cu / B.Cu) par défaut. Le choix définitif 2 vs 4 couches sera fait et justifié en Phase 0 (TASK-003) puis appliqué en Phase 3.

## Rapports ERC / DRC justifiés

### TASK-002 — projet vide
- **ERC** : 0 violation.
- **DRC** : 1 erreur `invalid_outline` (« Board has malformed outline (no edges found on Edge.Cuts layer) »). Attendue : le contour de carte n'est dessiné qu'en Phase 3. Ne bloque pas les phases 0 à 2.

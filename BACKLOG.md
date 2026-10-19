# Backlog

## TODO
- [ ] TASK-005 | Phase 2 — Schéma
  > Schéma complet selon conventions CLAUDE.md, ERC 0 erreur (warnings justifiés dans NOTES.md), PDF dans out/, commit "phase 2: ...".
  > ⏸ Checkpoint : schéma relu par l'utilisateur.
  > Blocked by: TASK-004 (BOM validée), TASK-002 (projet KiCad + libs)

- [ ] TASK-006 | Phase 3 — Setup PCB
  > Outline, trous de fixation, keepouts, stack-up, net classes, import du schéma, rendu 3D vide avec connecteurs placés.
  > ⏸ Checkpoint : outline + règles validés.
  > Blocked by: TASK-005 (import du schéma nécessaire)

- [ ] TASK-007 | Phase 4 — Placement
  > Placement complet, rendus 3D dessus/dessous + SVG dans out/renders/.
  > ⏸ Checkpoint : placement validé avant tout routage.
  > Blocked by: TASK-006

- [ ] TASK-008 | Phase 5 — Routage
  > Routage complet, zones remplies, DRC --schematic-parity : 0 erreur, 0 net non connecté. SVG par couche + rendu 3D.
  > ⏸ Checkpoint : routage relu.
  > Blocked by: TASK-007 (placement validé)

- [ ] TASK-009 | Phase 6 — Fabrication
  > Gerbers + drill + CPL + BOM fab zippés dans out/fab/<projet>_<rev>.zip, checklist finale dans NOTES.md.
  > ⏸ Checkpoint final.
  > Blocked by: TASK-008 (DRC propre)

## IN PROGRESS
- [ ] TASK-004 | Phase 1 — BOM préliminaire
  > bom/bom_draft.csv complet (Ref, Valeur, MPN, Fabricant, Package, Footprint, LCSC, Prix, Stock, Datasheet), chaque MPN vérifié avec source.
  > Calculs dimensionnants dans NOTES.md.
  > ⏸ Checkpoint : BOM validée par l'utilisateur.
  > Branch: feat/task-004-bom
  > Blocked by: TASK-003 (les composants découlent de la spec validée) — levé

## ON HOLD

## DONE
- [x] TASK-003 | Phase 0 — Spécification
  > Merged in: devape (2026-10-19) — spec validée au checkpoint
- [x] TASK-002 | Setup environnement + arborescence
  > Merged in: devape (2026-10-19)
- [x] TASK-001 | Remplir §1 de CLAUDE.md + créer la branche devape
  > Merged in: devape (2026-10-19)

## CANCELLED

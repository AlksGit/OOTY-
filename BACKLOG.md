# Backlog

## TODO
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
- [ ] TASK-005 | Phase 2 — Schéma
  > Schéma complet selon conventions CLAUDE.md, ERC 0 erreur (warnings justifiés dans NOTES.md), PDF dans out/, commit "phase 2: ...".
  > ⏸ Checkpoint : schéma relu par l'utilisateur.
  > Sous-étapes (une feuille hiérarchique chacune, un commit par feuille, ERC après chaque) :
  >   1. Feuille racine + structure hiérarchique, script de génération
  >   2. power : USB-C, protection VBUS, buck 3V3, 4 limiteurs AP22653, LED alim
  >   3. mcu : STM32G431 + découplage, SWD HIL, BOOT0, LED heartbeat
  >   4. sensing : 2 INA226 + shunts, I2C interne, écran OLED, ADC/DAC (diviseurs, TLV9001), lecture CC
  >   5. vio_io : TPS2116 + AP2127 (VIO), level shifters, TCA9517A, RESET/BOOT open-drain
  >   6. connectors : headers DUT, ESD TPD4E05U06, résistances série
  >   7. ERC global 0 erreur, export PDF dans out/, rendu SVG vérifié visuellement
  > Branch: feat/task-005-schematic
  > Blocked by: TASK-004 (BOM validée), TASK-002 (projet KiCad + libs) — levés

## ON HOLD

## DONE
- [x] TASK-004 | Phase 1 — BOM préliminaire
  > Merged in: devape (2026-10-19) — BOM validée au checkpoint (recommandations retenues), choix du fabricant reporté en Phase 6
- [x] TASK-003 | Phase 0 — Spécification
  > Merged in: devape (2026-10-19) — spec validée au checkpoint
- [x] TASK-002 | Setup environnement + arborescence
  > Merged in: devape (2026-10-19)
- [x] TASK-001 | Remplir §1 de CLAUDE.md + créer la branche devape
  > Merged in: devape (2026-10-19)

## CANCELLED

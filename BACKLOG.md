# Backlog

## TODO
- [ ] TASK-004 | Phase 1 — BOM préliminaire
  > bom/bom_draft.csv complet (Ref, Valeur, MPN, Fabricant, Package, Footprint, LCSC, Prix, Stock, Datasheet), chaque MPN vérifié avec source.
  > Calculs dimensionnants dans NOTES.md.
  > ⏸ Checkpoint : BOM validée par l'utilisateur.
  > Blocked by: TASK-003 (les composants découlent de la spec validée)

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
- [ ] TASK-003 | Phase 0 — Spécification
  > SPEC.md : blocs fonctionnels, budget de puissance, interfaces, contraintes méca, règles de fab.
  > Schéma bloc Mermaid dans SPEC.md.
  > Décision 2 vs 4 couches justifiée dans NOTES.md.
  > Périmètre :
  > Base :
  > - Alimentation USB-C
  > - Rails DUT : 3V3 et 5V fixes + 3V3 et 5V commutés (hard reboot du DUT)
  > - UART TX/RX + GND
  > - 4 entrées + 4 sorties numériques
  > - MCU STM32 + connecteur de programmation (pour la carte HIL elle-même)
  > Améliorations retenues :
  > - (1) Sonde SWD/JTAG intégrée vers le DUT (CMSIS-DAP) pour flasher/debugger le DUT
  > - (2) Mesure tension/courant de la consommation du DUT sur les rails commutés (plage de mesure à définir)
  > - (3) Limitation de courant / eFuse sur les rails commutés + remontée du flag de défaut au MCU
  > - (4) Lignes RESET et BOOT open-drain vers le DUT
  > - (5) Tension d'IO réglable (1.8 / 3.3 / 5 V) avec level shifters sur UART et IO
  > - (6) Entrées analogiques (ADC) + sortie DAC
  > - (8) Bus I2C et SPI exposés
  > - (9) Protection ESD (TVS) + résistances série sur toutes les pins exposées
  > - LED "alim OK" (directement sur le rail) + LED "heartbeat" pilotée par le firmware
  > Hors périmètre rev A : IO multifonction, LED par IO, entrée alim externe / USB-PD, isolation galvanique, switch USB DUT, n° de série custom, watchdog hôte.
  > ⏸ Checkpoint : spec validée par l'utilisateur.
  > Branch: feat/task-003-spec
  > Blocked by: TASK-001 (la spec reformule les infos projet de §1) — levé

## ON HOLD

## DONE
- [x] TASK-002 | Setup environnement + arborescence
  > Merged in: devape (2026-10-19)
- [x] TASK-001 | Remplir §1 de CLAUDE.md + créer la branche devape
  > Merged in: devape (2026-10-19)

## CANCELLED

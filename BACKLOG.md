# Backlog

## TODO
- [ ] TASK-008 | Phase 5 — Routage
  > Routage complet, zones remplies, DRC --schematic-parity : 0 erreur, 0 net non connecté. SVG par couche + rendu 3D.
  > ⏸ Checkpoint : routage relu.
  > Blocked by: TASK-012 (placement final validé)

- [ ] TASK-009 | Phase 6 — Fabrication
  > Gerbers + drill + CPL + BOM fab zippés dans out/fab/<projet>_<rev>.zip, checklist finale dans NOTES.md.
  > ⏸ Checkpoint final.
  > Blocked by: TASK-008 (DRC propre)

## IN PROGRESS
- [ ] TASK-012 | Placement — intégration des nouveaux blocs + finition de la sérigraphie
  > Blocs de mesure au plus près des shunts (Kelvin, boucle de bascule courte). Toutes les pièces clés ont leur référence en sérigraphie, sans ambiguïté. DRC + parité 0 erreur, découplage dans les limites, rendus 3D. Relecture indépendante « prêt pour le routage ». Clôt aussi TASK-005/006/007 (merge de toute la pile après accord utilisateur).
  > Branch: feat/task-010-dual-range
  > Blocked by: TASK-011 — levé

- [ ] TASK-011 | Schéma — mesure double calibre ×2 + retours de tension des rails fixes
  > Blocs double calibre sur 3V3_SW et 5V_SW, diviseurs 5V_DUT / 3V3_DUT vers l'ADC, générés par script. ERC 0 erreur, netlist et BOM sans écart, PDF + rendus exportés. Relecture indépendante contre les datasheets.
  > Branch: feat/task-010-dual-range (même branche que TASK-010)
  > Statut : ✅ terminé (ERC 0 erreur, netlist 196 nets et BOM 242 pièces sans écart, relecture indépendante sans bloquant ni majeur, mineurs appliqués) ; mergée avec la pile après TASK-012.
  > Blocked by: TASK-010 — levé

- [ ] TASK-010 | Spec + composants — mesure double calibre (3V3_SW, 5V_SW) et retours de tension des rails fixes
  > Mesure de courant double calibre sur 3V3_SW et 5V_SW : shunt fort (veille, ~1 µA min, résolution ~0.1 µA) + shunt faible (éveil), bascule matérielle en quelques µs, chute de tension max vue par le DUT bornée. Retour de tension 5V_DUT / 3V3_DUT par diviseurs vers l'ADC.
  > Livrables : SPEC.md + NOTES.md (architecture, valeurs des shunts, seuil/temps de bascule, chute max, plage et précision par calibre, débit), MPN vérifiés (datasheet + stock) ajoutés à bom/bom_draft.csv, broches MCU réaffectées.
  > ⏸ Checkpoint : relecture indépendante + décisions utilisateur.
  > Branch: feat/task-010-dual-range (empilée sur fix/task-005-007-review)
  > Statut : ✅ validée par l'utilisateur le 2026-10-20 (revue indépendante appliquée) ; mergée avec la pile après TASK-012.
  > Blocked by: —

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
  > Statut : terminé côté dev/revue (ERC 0 erreur, netlist et BOM vérifiées, revue électrique indépendante appliquée). ⏸ En attente du checkpoint utilisateur avant merge (merge sans relecture refusé par le mode auto).
  > Blocked by: TASK-004 (BOM validée), TASK-002 (projet KiCad + libs) — levés

- [ ] TASK-006 | Phase 3 — Setup PCB
  > Outline, trous de fixation, keepouts, stack-up, net classes, import du schéma, rendu 3D vide avec connecteurs placés.
  > ⏸ Checkpoint : outline + règles validés.
  > Branch: feat/task-006-pcb-setup (empilée sur feat/task-005-schematic)
  > Statut : setup fait en mode autonome (85×55, 4 couches, règles, classes de nets, connecteurs placés, DRC 0 erreur). ⏸ Checkpoint à valider.
  > Blocked by: TASK-005

- [ ] TASK-007 | Phase 4 — Placement
  > Placement complet, rendus 3D dessus/dessous + SVG dans out/renders/.
  > ⏸ Checkpoint : placement validé avant tout routage.
  > Branch: feat/task-007-placement (empilée sur feat/task-006-pcb-setup)
  > Statut : placement fait en mode autonome (DRC 0 erreur, parité 0, découplage vérifié). ⏸ Checkpoint placement à valider AVANT tout routage.
  > Blocked by: TASK-006

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

# CLAUDE.md — Conception PCB avec KiCad

Ce projet sert à concevoir un PCB complet (schéma + layout + fichiers de fab) avec KiCad, piloté par Claude Code.
Tu travailles par **phases**, tu valides chaque phase avec les outils KiCad, et tu t'arrêtes aux **checkpoints** pour que je relise.

---

## 1. Le projet (à remplir)

- **Nom** : `OOTY`
- **Fonction** : carte HIL (Hardware-In-the-Loop) pilotée par USB depuis un PC, pour tester un DUT dans des workflows automatisés (notamment Claude) et faciliter le télétravail : alimenter / couper le DUT, le flasher et le debugger, mesurer sa consommation, piloter et lire ses IO, dialoguer en UART/I2C/SPI.
- **Alimentation** : USB-C 5 V (la carte HIL et les rails fournis au DUT). Budget de puissance à établir en Phase 0.
- **MCU / composants imposés** : STM32 (modèle à choisir en Phase 1), programmé via son propre connecteur JTAG/SWD.
- **Interfaces** :
  - USB-C vers le PC hôte
  - Rails DUT : 3V3 et 5V fixes, 3V3 et 5V commutés (hard reboot), avec limitation de courant / eFuse + flag de défaut, et mesure tension/courant
  - Sonde SWD/JTAG intégrée vers le DUT (CMSIS-DAP)
  - Lignes RESET et BOOT open-drain vers le DUT
  - UART TX/RX + GND
  - 4 entrées + 4 sorties numériques
  - Entrées analogiques (ADC) + sortie DAC
  - Bus I2C et SPI exposés
  - Tension d'IO réglable (1.8 / 3.3 / 5 V) via level shifters (UART, IO)
  - Protection ESD (TVS) + résistances série sur toutes les pins exposées
  - LED « alim OK » + LED « heartbeat » firmware
  - Connecteur de programmation/debug du STM32 de la carte HIL
- **Contraintes mécaniques** : 85 × 55 mm max (plus petit = mieux). Connecteurs DUT en headers 2.54 mm. Trous de fixation et hauteur max : à définir en Phase 0.
- **Couches** : à décider en Phase 0 (2 vs 4 selon densité et coût, justification dans `NOTES.md`).
- **Fabricant / assemblage** : le moins cher — PCBWay proposé, à comparer avec JLCPCB en Phase 0 — **règles de fab** : à fixer en Phase 0 selon le fabricant retenu.
- **Préférence composants** : CMS, 0402 ou 0603 minimum, pièces en stock chez le fabricant si assemblage

Si une info manque et qu'elle impacte le design, **demande avant de deviner**.

---

## 2. Environnement & outils

Avant de commencer, vérifie l'environnement et note les versions dans `NOTES.md` :

```bash
kicad-cli version
python3 -c "import pcbnew; print(pcbnew.Version())"   # bindings SWIG, peuvent être absents/dépréciés selon la version
python3 -c "import kiutils"                            # pip install kiutils
java -version                                          # pour Freerouting (optionnel)
```

Outils à utiliser, par ordre de préférence :

| Besoin | Outil |
|---|---|
| ERC / DRC | `kicad-cli sch erc` / `kicad-cli pcb drc` (sortie JSON) |
| Lire/écrire `.kicad_sch` / `.kicad_pcb` | `kiutils` (Python) ; édition S-expression directe en dernier recours |
| Placement / manipulations PCB scriptées | `pcbnew` Python si dispo, sinon `kiutils` |
| Netlist, BOM, exports | `kicad-cli sch export netlist|bom|pdf|svg` |
| Autorouting | Freerouting (export `.dsn` → route → import `.ses`), seulement pour les nets non critiques |
| Rendus pour revue | `kicad-cli sch export svg`, `kicad-cli pcb export svg`, `kicad-cli pcb render` (3D) |
| Fichiers de fab | `kicad-cli pcb export gerbers|drill|pos`, `kicad-cli sch export bom` |

Ne jamais inventer une option de `kicad-cli` : en cas de doute, `kicad-cli <cmd> --help`.

---

## 3. Règles de travail

- **Ne modifie jamais un fichier KiCad ouvert dans l'interface** : demande-moi de fermer KiCad avant d'écrire dans `.kicad_sch` / `.kicad_pcb`.
- **Git** : commit à la fin de chaque phase (`phase N: ...`). Avant toute modification lourde scriptée, commit l'état courant.
- **Scripts reproductibles** : toute génération/modification passe par un script Python dans `scripts/` (pas de bidouille one-shot non tracée). Les scripts doivent être idempotents quand c'est possible.
- **Validation systématique** : après chaque modif du schéma → ERC ; après chaque modif du PCB → DRC. Rapports dans `out/reports/`. Zéro erreur avant de passer à la phase suivante ; chaque warning restant est justifié dans `NOTES.md`.
- **Vérifie visuellement** : après chaque étape significative, exporte un SVG/PNG ou un rendu 3D dans `out/renders/` et **regarde-le** (lis l'image) pour détecter les incohérences (symboles superposés, labels illisibles, composants hors board, etc.).
- **Pas d'hallucination de composants** : chaque référence fabricant (MPN) doit exister. Vérifie datasheet / stock (web) et note la source dans la BOM. Pinout et footprint vérifiés contre la datasheet, pas de mémoire.
- **Librairies** : utilise en priorité les librairies KiCad officielles. Symboles/footprints custom dans `lib/<projet>.kicad_sym` et `lib/<projet>.pretty/`, référencés via les `sym-lib-table` / `fp-lib-table` **du projet** (chemins relatifs `${KIPRJMOD}`).
- **Décisions** : toute décision de design non triviale (choix de régulateur, topologie, stack-up, largeur de piste) est consignée dans `NOTES.md` avec la justification (calcul, note d'application).

---

## 4. Phases & checkpoints

### Phase 0 — Spécification
- Reformule le besoin dans `SPEC.md` : blocs fonctionnels, budget de puissance, interfaces, contraintes méca, règles de fab.
- Schéma bloc (Mermaid dans `SPEC.md`).
- ⏸ **Checkpoint** : je valide la spec.

### Phase 1 — Choix des composants
- BOM préliminaire dans `bom/bom_draft.csv` : Ref, Valeur, MPN, Fabricant, Package, Footprint KiCad, Fournisseur/code (ex. LCSC), Prix, Stock, Lien datasheet.
- Calculs dimensionnants (diviseurs, régulateurs, résistances de pull-up, filtrage, cristaux/caps de charge) dans `NOTES.md`.
- ⏸ **Checkpoint** : je valide la BOM.

### Phase 2 — Schéma
- Schéma hiérarchique si > ~30 composants (une feuille par bloc : alim, MCU, capteurs, connecteurs...).
- Conventions :
  - Labels de nets explicites (`VBAT`, `3V3`, `I2C_SDA`, `SWDIO`...), pas de nets anonymes sur les signaux importants.
  - Symboles power pour les rails, `PWR_FLAG` où nécessaire pour l'ERC.
  - Découplage à côté de chaque pin d'alim du CI concerné (100 nF + bulk selon datasheet).
  - Test points sur les rails et bus de debug ; header de programmation/debug.
  - Champs remplis pour chaque composant : `Footprint`, `MPN`, `Datasheet`, (`LCSC` si JLC).
  - Grille 50 mil (1.27 mm), pas de fils qui se croisent sur une pin, schéma lisible (flux gauche → droite, entrées → sorties).
- `kicad-cli sch erc` → 0 erreur.
- Export PDF du schéma dans `out/`.
- ⏸ **Checkpoint** : je relis le schéma (PDF).

### Phase 3 — Setup PCB
- Contour de carte (Edge.Cuts), trous de fixation, keepouts, position des connecteurs selon contraintes méca.
- Stack-up et règles (Board Setup + net classes) selon le fabricant : largeur/espace min, vias, net classes `Power`, `Default`, signaux sensibles (USB diff 90 Ω, RF 50 Ω si besoin — calcul d'impédance documenté).
- Import du schéma dans le PCB (mise à jour depuis le schéma).
- ⏸ **Checkpoint** : je valide outline + règles (rendu 3D vide avec connecteurs placés).

### Phase 4 — Placement
- Ordre : connecteurs et pièces mécaniquement imposées → MCU/CI principaux → alim → découplages au plus près des pins → reste.
- Grouper par bloc fonctionnel, minimiser les croisements de ratsnest, respecter les recommandations de layout des datasheets (régulateurs à découpage, cristal, antenne/keepout RF, USB).
- Références silkscreen lisibles, orientées de façon cohérente, hors pads.
- Exporte un rendu 3D (dessus + dessous) et un SVG du placement.
- ⏸ **Checkpoint** : je valide le placement **avant tout routage**.

### Phase 5 — Routage
- Routage manuel (scripté) en priorité pour : alimentation (largeur selon courant, calcul IPC-2221 noté), boucles de découpage courtes, cristal, paires différentielles, RF.
- Plans de masse (zones GND) sur les couches adaptées, stitching vias, pas de coupure de plan sous les signaux rapides.
- Autorouteur (Freerouting) autorisé uniquement pour les signaux lents restants ; vérifier et nettoyer le résultat.
- Remplir les zones puis `kicad-cli pcb drc` (avec `--schematic-parity`) → 0 erreur, 0 net non connecté.
- ⏸ **Checkpoint** : je relis le routage (SVG par couche + rendu 3D).

### Phase 6 — Fabrication
- Gerbers + drill (format attendu par le fabricant), fichier de position (CPL), BOM finale au format du fabricant.
- Zip dans `out/fab/<projet>_<rev>.zip`.
- Checklist finale dans `NOTES.md` : DRC/ERC propres, BOM vs schéma cohérents, polarités/pin 1 marqués, fiducials si assemblage, rev + date sur le silkscreen.
- ⏸ **Checkpoint final**.

---

## 5. Arborescence

```
.
├── CLAUDE.md
├── SPEC.md
├── NOTES.md              # décisions, calculs, versions outils, warnings justifiés
├── <projet>.kicad_pro
├── <projet>.kicad_sch    # + sous-feuilles
├── <projet>.kicad_pcb
├── sym-lib-table
├── fp-lib-table
├── lib/
│   ├── <projet>.kicad_sym
│   └── <projet>.pretty/
├── bom/
├── scripts/              # tous les scripts de génération/modif
└── out/
    ├── reports/          # ERC/DRC JSON
    ├── renders/          # SVG, PNG, rendus 3D
    └── fab/
```

---

## 6. Ce que je n'attends pas de toi

- Passer une phase sans checkpoint.
- Désactiver une règle DRC/ERC pour faire disparaître une erreur sans me le dire.
- Remplacer un composant de la BOM validée sans me demander.
- Dire « c'est routé » sans rapport DRC propre à l'appui.

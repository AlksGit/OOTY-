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

## Décisions Phase 0 (TASK-003) — validées au checkpoint du 2026-10-19

Validé par l'utilisateur : lecture CC, limites de courant par rail, limitation aussi sur les rails fixes, 2 ADC 0–5 V + 1 DAC 0–3.3 V, option VIO externe, 4 trous M3 sans contrainte de hauteur, JLCPCB, 4 couches. Ajout utilisateur : petit écran I2C bon marché.

### Limitation des rails fixes
Issue de la revue de la spec : le 3V3 fixe du DUT sort du même buck que le STM32 de la carte HIL. Sans limiteur dédié, un court-circuit sur ce rail ferait chuter le 3V3 du MCU et la carte deviendrait injoignable (Claude ne pourrait plus rien relancer). Chaque rail fixe passe donc par un limiteur toujours actif avec flag FAULT, comme les rails commutés.

### Écran : module OLED 0.91" 128 × 32 SSD1306 I2C
- Choix : le format le plus courant et le moins cher, piloté en I2C (2 fils, sur le bus interne déjà présent pour les moniteurs de courant, aucune broche MCU en plus), alimenté en 3.3 V, adresse 0x3C. Le module fait ~36 × 12.5 mm ; un 0.96" 128 × 64 serait plus lisible mais occupe ~27 × 27 mm, trop pour une carte visée à ~70 × 50 mm.
- Module sur header 4 broches (GND/VCC/SCL/SDA) plutôt que dalle nue sur nappe FPC : pas de pompe de charge ni de connecteur FPC à concevoir, remplaçable.
- Vérifier en Phase 1 : l'ordre des broches du module retenu (il varie selon les fabricants, GND/VCC parfois inversés), la disponibilité chez LCSC, l'absence de conflit d'adresse I2C avec les moniteurs de courant.
- Source : https://waveshare.com/0.91inch-OLED-Module.htm (3.3/5 V, 36 × 12.5 mm, SSD1306, I2C).

### Couches : 4 (Signal / GND / Power / Signal)
Le projet KiCad est encore initialisé en 2 couches ; le passage en 4 couches sera appliqué en Phase 3.

Justification :
- **Densité** : ~40 signaux MCU, une dizaine de level shifters / TVS, 2 eFuses, 2 moniteurs de courant, un régulateur à découpage et 6 connecteurs sur ≤ 85 × 55 mm. En 2 couches, le plan de masse serait très découpé.
- **Plan GND continu** sous tout le routage : retour de courant propre pour l'USB, le buck et les mesures analogiques (ADC, shunts de courant à faible tension).
- **Distribution d'alimentation** : la couche interne Power porte 5V_SYS / 3V3 en zones larges, ce qui libère les couches externes pour les signaux.
- **Coût** : chez JLCPCB, l'écart 2 → 4 couches pour un prototype de 5 pièces de cette taille est de l'ordre de quelques dollars à une dizaine de dollars (un relevé utilisateur de 2024 donne ~9.55 $ pour 5 pièces 100 × 100 mm en 4 couches ; non officiel, à confirmer par devis). Négligeable devant l'assemblage et les composants.

### Fabricant : JLCPCB recommandé (au lieu de PCBWay)
Critère imposé : le moins cher.
- Les comparatifs consultés s'accordent : JLCPCB est le moins cher pour les cartes simples et l'assemblage de petites séries, PCBWay offre plus d'options et plus de support humain. Un test utilisateur (2023, 114 × 114 mm) donnait PCBWay 2.8× plus cher en 2 couches et 2× en 4 couches.
- L'assemblage JLCPCB s'appuie sur la bibliothèque LCSC : les pièces « Basic » n'ont pas de frais de chargement, les « Extended » en ont. On privilégiera les Basic en Phase 1.
- Sources (tierces, à confirmer par un devis réel avec notre BOM en Phase 1) :
  - https://lcamtuf.substack.com/p/comparing-hobby-pcb-vendors
  - https://forums.atariage.com/topic/349426-pcbway-vs-jlcpcb-which-is-cheaper
  - https://jlcpcb.com/news/discount-on-quality-4-layer-pcbs
  - https://eevblog.com/forum/manufacture/a-good-pcb-manufacture-for-hobby-pcb/msg5569241

### Règles de fab (proposées)
- Minima JLCPCB multicouche relevés sur leur page de capacités : piste/espace 0.09 mm, via perçage 0.2 mm / diamètre 0.45 mm (https://api.jlcpcb.com/capabilities/Capabilities, https://jlcpcb.com/help/article/243-BGA-Design-Guidelines---PCB-Layout-Recommendations-for-BGA-packages).
- Valeurs retenues avec marge : piste/espace 0.15 / 0.15 mm, via 0.3 / 0.6 mm, 1.6 mm. Pas besoin de s'approcher des minima vu la densité attendue ; évite tout surcoût lié aux petits perçages.

### Régulateur 3V3 : buck plutôt que LDO (orientation, choix du composant en Phase 1)
Charge 3V3 max ≈ 0.3 + 0.5 (DUT) + 0.055 (HIL) ≈ 0.86 A. Un LDO 5 → 3.3 V dissiperait (5 − 3.3) × 0.86 ≈ 1.46 W : trop pour un boîtier CMS compact sans grande surface de cuivre. Un buck (η ≈ 85 %) dissipe ≈ 0.5 W au total, réparti.

### Budget VBUS
Pire cas ≈ 2.2 A @5V (détail dans `SPEC.md` §3) : il faut une source USB-C 3 A pour exploiter toutes les limites. D'où la proposition de lire les lignes CC pour connaître la capacité de la source.

### Mesure de courant (orientation)
- INA226 : plage ±81.92 mV, LSB 2.5 µV. Avec un shunt de 50 mΩ : pleine échelle 1.64 A, résolution 50 µA. Insuffisant pour mesurer une veille au µA.
- INA228 (20 bits) : plage ±163.84 mV, LSB 312.5 nV. Avec 50 mΩ : pleine échelle 3.3 A, résolution ≈ 6.25 µA.
- Orientation : INA228 (ou équivalent haute résolution) si disponible en stock LCSC à coût raisonnable. Valeurs à revérifier dans les datasheets en Phase 1.

## Rapports ERC / DRC justifiés

### TASK-002 — projet vide
- **ERC** : 0 violation.
- **DRC** : 1 erreur `invalid_outline` (« Board has malformed outline (no edges found on Edge.Cuts layer) »). Attendue : le contour de carte n'est dessiné qu'en Phase 3. Ne bloque pas les phases 0 à 2.

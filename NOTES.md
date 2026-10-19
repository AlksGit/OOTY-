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

## Phase 1 — Choix des composants (TASK-004)

Recherche du 2026-10-19 : prix et stocks LCSC / JLCPCB relevés ce jour-là (ils bougent vite, à revérifier avant commande). Détail ligne par ligne dans `bom/bom_draft.csv`.

### MCU : STM32G431RBT6 (LQFP-64)
- **Seul candidat réellement en stock** chez JLCPCB/LCSC (≈ 2 600 pcs). STM32G0B1RET6 et STM32F072RBT6 : stock 0 le 2026-10-19.
- DS12589 : USB FS sans quartz (HSI48 + CRS, §3.34/§3.36), 128 KiB flash, 32 KiB SRAM, 3× I2C, 3× SPI, 4 U(S)ART, DAC (2 voies sur broches), 2 ADC, 52 GPIO en LQFP-64 (besoin ≈ 46).
- USB : 8 endpoints, 1 KiB de PMA → EP0 + 2 × CDC + CMSIS-DAP v2 ≈ 6 endpoints, ≈ 600 octets (estimation).
- Point faible : pas de port open-source CMSIS-DAP existant sur G4 (dap42 vise F042/F072). Le portage de la couche GPIO de la référence ARM CMSIS-DAP est simple ; à prévoir côté firmware.
- Découplage (DS12589 §5.1.6, Figure 16) : VDD 4 × 100 nF + 1 × 4.7 µF ; VDDA 10 nF + 1 µF ; VREF+ 100 nF + 1 µF ; NRST 100 nF (Figure 27) ; VBAT relié au 3V3 avec 100 nF (pratique de conception, pas une exigence de la datasheet).
- BOOT0 (PB8, broche 61) : pull-down 10 kΩ + pastille vers 3V3 pour forcer le bootloader en secours. Le fonctionnement du DFU USB sans quartz (AN2606) reste à vérifier ; le SWD est le chemin de programmation principal.

### Buck 5 V → 3.3 V : TLV62569DBVR
- Entrée 2.5–5.5 V (couvre l'USB 4.4–5.5 V), 2 A, SOT-23-5.
- **Diviseur** (SLVSDG1C §8.2.2.2) : Vout = 0.6 × (1 + R1/R2). R1 = 100 kΩ, R2 = 22 kΩ → **3.327 V** (+0.8 %), plage 3.26–3.39 V avec la tolérance de VFB.
- **Inductance** (§8.2.2.4) : ΔIL = Vout·(1 − Vout/Vin)/(L·fsw) = 3.3 × 0.4 / (2.2 µH × 1.5 MHz) ≈ 0.40 A à Vin = 5.5 V. Pic à 1.2 A de charge ≈ 1.4 A → FXL0420-2R2 (Isat 5 A, au-dessus de la limite de 3 A du buck : pas de saturation en court-circuit).
- Cin 10 µF + 100 nF ; Cout 2 × 22 µF 0805 (compense la perte de capacité sous tension DC). Empreinte Cff 0402 non montée.
- **Charge 3V3 max** : 3V3 fixe (limite max 405 mA) + 3V3_SW (limite max 718 mA) + HIL 70 mA ≈ 1.2 A < 2 A.

### Limiteurs de courant : AP22653W6-7 (× 4)
- Un seul modèle pour les 4 rails : 3.0–5.5 V, FAULT open-drain (filtre 6 ms), **décharge de sortie** (600 Ω), **blocage du courant inverse** à l'arrêt, repli du courant en court-circuit. Préféré au TPS2553 (pas de décharge de sortie, blocage inverse limité) et au SY6280 (pas de FAULT).
- **RLIM** (DS41186 p.10, à VIN = 5 V) : ILIM_typ = 30321 / R^1.055 (mA, R en kΩ) ; min = 28955 / R^1.075 ; max = 31033 / R^1.031.

| Rail | Cible | RLIM | min / typ / max |
|---|---|---|---|
| 5V_SW | 1.0 A DUT | 22 kΩ | 1033 / 1163 / 1295 mA |
| 5V fixe | 0.5 A | 39 kΩ | 558 / 636 / 718 mA |
| 3V3_SW | 0.5 A | 39 kΩ | 558 / 636 / 718 mA |
| 3V3 fixe | 0.3 A | 68 kΩ | 307 / 354 / 405 mA |

- Équations caractérisées à VIN = 5 V : la limite réelle sur les rails 3V3 est à **mesurer au banc**.
- Rails fixes : EN relié à IN. Rails commutés : EN piloté par le MCU avec pull-down 100 kΩ (OFF pendant le boot ; VIH min 1.5 V).

### Protection d'entrée VBUS
- PTC 1812 SMD1812P260TF (8 V, Ihold 2.6 A, Itrip 5 A) : dernier recours pour un défaut sur 5V_SYS lui-même ; la limitation fine est faite par les 4 AP22653. Chute ≈ 30 mV à 2.2 A.
- Somme des limites typiques des 4 rails ≈ 2.6 A (≈ 2.95 A aux limites max) : ne dépasse Ihold que si tous les rails sont en limitation en même temps (double défaut). La charge nominale max (2.2 A) reste sous Ihold.
- TVS SMAJ5.0A sur VBUS (VBR 6.4 V, Vc 9.2 V) ; USBLC6-2SC6 sur D+/D-.
- CC1/CC2 : Rd 5.1 kΩ vers GND, tension lue par l'ADC. Seuils de la spec USB Type-C (vRd) : < 0.66 V = USB par défaut, 0.66–1.23 V = 1.5 A, > 1.23 V = 3 A (à confirmer en Phase 2).

### Mesure de courant
- **INA228 introuvable** chez LCSC/JLCPCB (stock 0 sur toutes les variantes le 2026-10-19) → décision au checkpoint.
- Shunts : 50 mΩ sur 5V_SW, 100 mΩ sur 3V3_SW (1206, 1 W, 1 %, 50 ppm/°C).

| Rail / shunt | Moniteur | Pleine échelle | Résolution |
|---|---|---|---|
| 5V_SW, 50 mΩ | INA226 | 1.638 A | 50 µA |
| 5V_SW, 50 mΩ | INA228 (ADCRANGE=0 / 1) | 3.277 A / 819 mA | 6.25 µA / 1.56 µA |
| 3V3_SW, 100 mΩ | INA226 | 819 mA | 25 µA |
| 3V3_SW, 100 mΩ | INA228 (ADCRANGE=0 / 1) | 1.638 A / 410 mA | 3.1 µA / 0.78 µA |

- Dissipation : 5V_SW 1.1² × 0.05 = 61 mW ; 3V3_SW 0.55² × 0.1 = 30 mW (shunts 1 W : large marge). Chute : 50–55 mV.
- Adresses I2C : 0x40 et 0x41 (A1/A0), pas de conflit avec l'écran (0x3C).

### Bus I2C interne (moniteurs + écran)
- Cb estimée 100 pF, 400 kHz : Rmax = 300 ns / (0.8473 × 100 pF) = 3.54 kΩ ; Rmin = (3.3 − 0.4) / 3 mA = 967 Ω.
- **2.2 kΩ**. Le module OLED a déjà 4.7 kΩ de pull-up : équivalent 1.5 kΩ, 1.9 mA au niveau bas (≤ 3 mA).

### Écran : module HS91L02W2C01 (LCSC C5248081)
- 0.91" 128 × 32, SSD1306, I2C 0x3C, 38 × 12 × 2.6 mm, brochage **1 GND, 2 VCC, 3 SCL, 4 SDA** (datasheet p.6–7). Régulateur, pompe de charge et pull-ups 4.7 kΩ intégrés : aucun composant externe.
- Monté sur un support femelle 1×4 2.54 mm (remplaçable). Alimenté en 3.3 V (VCC max illisible dans la datasheet).

### VIO
- **Mux TPS2116** : VIN1 = 5V_SYS (choix 5 V), VIN2 = sortie du LDO AP2127K-ADJ (1.8 ou 3.3 V), VOUT = VIO.
  - Table de vérité (§7.3.1) : MODE haut + PR1 haut → VIN1 ; MODE haut + PR1 bas → VIN2 ; **MODE bas + PR1 haut → arrêt, VOUT haute impédance = mode VIO externe**. MODE bas + PR1 bas = priorité à la tension la plus haute (5 V), **à éviter** : PR1 pull-up 10 kΩ, MODE pull-down 100 kΩ → VIO coupé au reset.
  - Blocage du courant inverse si VOUT − VIN > 42 mV typ : en mode externe, le DUT ne réalimente ni 5V_SYS ni le LDO.
  - Commutation sans chevauchement : passer par l'arrêt avant de descendre de 5 V à 1.8 V (firmware).
- **LDO AP2127K-ADJ** : Vout = 0.8 × (1 + R1/R2), R2 entre 5 et 200 kΩ.
  - R1 = 30 kΩ, R2 = 24 kΩ → **1.800 V** (par défaut).
  - R2b = 16 kΩ commuté en parallèle par un 2N7002 (gate pull-down 100 kΩ) : R2 ∥ R2b = 9.6 kΩ → **3.300 V**.
  - Cff = 1 nF (1/(2π·R1·Cff) = 5.3 kHz, dans la plage 0.7–15 kHz). RDS(on) du 2N7002 à VGS = 3.3 V non spécifié : quelques dizaines d'Ω → erreur < 0.3 %, à vérifier.
  - Chute 170 mV à 300 mA, marge de 1.7 V.
- **VIO_MON** : diviseur 100 k / 100 k vers l'ADC (5.5 V → 2.75 V). Le firmware mesure le VTref externe avant d'activer une source interne.
- Broches MCU supplémentaires : PR1, MODE, VSEL, LS_OE, I2C_EN, VIO_MON (ADC) → budget ≈ 46 broches sur 52 disponibles.

### Level shifters
- 2 × SN74LVC8T245 : un en sortie seule (DIR = VCCA : OUT1–4, TX, SCK, MOSI, CS), un en entrée seule (DIR = GND : IN1–4, RX, MISO, SWO, 1 libre). /OE commun avec pull-up 10 kΩ → haute impédance jusqu'à ce que le firmware active.
- 2 × SN74LVC1T45 pour SWCLK et SWDIO (DIR piloté par GPIO, pull-down 100 kΩ = côté DUT en haute impédance au reset).
- Ioff / isolation VCC (datasheets) : si VIO est absent, les deux ports passent en haute impédance.
- **I2C DUT : TCA9517** (VCCA 0.9–5.5 V côté DUT, VCCB 2.7–5.5 V côté MCU). Le **PCA9306 prévu dans la spec ne convient pas** : il impose VREF1 ≤ VREF2 − 0.6 V, impossible avec un MCU fixe à 3.3 V et un VIO qui passe de 1.8 à 5 V.
- RESET / BOOT : 2N7002 en open-drain (gate pull-down 100 kΩ), tient 60 V, compatible pull-ups DUT jusqu'à 5 V.

### Entrées analogiques
- Diviseur 100 kΩ / 100 kΩ (Basic, évite une référence Extended) : impédance 200 kΩ, gain 0.5 → 5.0 V → 2.50 V, 5.5 V → 2.75 V (550 mV de marge). Résolution 12 bits : 1.61 mV à l'entrée.
- Filtre 10 nF : fc = 1/(2π × 50 kΩ × 10 nF) = 318 Hz. Erreur de partage de charge avec le condensateur d'échantillonnage ≈ 0.05 %.
- Protection : la TVS TPD4E05U06 est sur la broche du header, **avant** le 100 kΩ (VRWM 5.5 V, VBR 6.5–8.5 V) : la plage d'entrée est donc **0–5.5 V**, une tension plus élevée détruirait la TVS. (Correction de la revue du schéma : la tenue « 24 V » annoncée en Phase 1 était fausse.) Pas de BAT54S (fuite 2 µA → erreur de plusieurs dizaines de mV).

### Sortie DAC
- TLV9001IDBVR en suiveur, RRIO, 1.8–5.5 V, ±40 mA en court-circuit ; 100 Ω en série en sortie. Brochage DBV : 1 OUT, 2 V−, 3 IN+, 4 IN−, 5 V+ (attention : la version TLV9001**U** a un brochage différent).

### ESD et résistances série
- TPD4E05U06 (4 voies, VRWM 5.5 V, ≈ 0.5 pF) : 7 boîtiers pour ≈ 26 signaux + 1 boîtier pour les broches d'alimentation des headers (5V, 5V_SW, 3V3, 3V3_SW).
- Ordre : connecteur → TVS → résistance série → circuit.
- 100 Ω en série sur les signaux (les 22 Ω et 33 Ω Basic sont en rupture chez LCSC). Pas de résistance série sur l'I2C DUT (TCA9517 + TVS suffisent).

### LED
- Alim OK : XL-1608SYGC-06 (jaune-vert, Vf ≈ 2 V) + 1 kΩ → ≈ 1.3 mA. Les LED vert « émeraude » (Vf ≈ 3.1 V) sont exclues : pas assez de marge sous 3.3 V.
- Heartbeat : KT-0603R rouge (Basic) + 1 kΩ.

### Assemblage JLCPCB
- **Economic PCBA** compatible : 2/4/6 couches, ≤ 1.6 mm, stack-up standard, une seule face. Frais : setup 8.18 $, pochoir 1.53 $, **3.07 $ par référence Extended** (Basic gratuites).
- Traversant (headers, support écran) : soudé par JLCPCB, 3.58 $ par commande + 0.0164 $/point (≈ 42 points ≈ 0.7 $). Moins cher que de souder à la main.
- Sources : https://jlcpcb.com/help/article/pcb-assembly-price, https://jlcpcb.com/help/article/pcb-assembly-faqs, https://jlcpcb.com/capabilities/pcb-assembly-capabilities

### Décisions du checkpoint BOM (2026-10-19)
L'utilisateur a demandé d'avancer ; les recommandations de la revue sont retenues :
1. **INA226** monté ; passage à l'INA228 possible plus tard sans modifier le PCB (même brochage), seul le firmware change.
2. **STM32G431RBT6** confirmé (portage CMSIS-DAP à prévoir côté firmware).
3. **TCA9517A** pour l'I2C DUT, à la place du PCA9306.
4. **J_UART et J_ANA regroupés** en un header 1×7 `J_UART_ANA` (TX, RX, GND, AIN1, AIN2, AOUT, GND) : −2 références Extended.
5. **Pull-ups 10 kΩ externes** sur les 4 FAULT des AP22653 et l'ALERT des INA226 (définies pendant le boot, sans dépendre de la configuration GPIO).
- **Fabricant** : décision reportée à la Phase 6 sur devis réels JLCPCB et PCBWay. PCBWay ne facture pas de frais par référence mais revend les composants avec une marge (≈ ×2 rapporté) et a un PCB plus cher ; pour une petite série avec beaucoup de références, il peut être moins cher. Sources : https://www.pcbway.com/, https://forum.contextualelectronics.com/t/pcbway-assembly-service-my-experience/2541, https://www.anypcba.com/decoding-pcbway-assembly-cost-a-comprehensive-guide.html

### Estimation de coût JLCPCB (5 cartes, `python scripts/bom_draft.py`)

| Poste | Montant |
|---|---|
| Composants (14.51 $/carte × 5) | ≈ 73 $ |
| Frais de chargement Extended (28 références × 3.07 $) | ≈ 86 $ |
| Setup + pochoir Economic PCBA | ≈ 10 $ |
| Soudure traversant (3.58 $ + ≈ 0.7 $/carte) | ≈ 7 $ |
| PCB 4 couches ≈ 70 × 50 mm × 5 (non devisé) | ≈ 10–20 $ |
| **Total hors port** | **≈ 185–195 $, soit ≈ 38 $/carte** (≈ 28 $ à 10 cartes, ≈ 22 $ à 20) |

- Premier poste de coût : les **frais Extended**. Ils sont fixes par commande et pèsent beaucoup sur 5 cartes, beaucoup moins sur 20+.
- Pistes pour les réduire :
  - utiliser le même header 1×7 pour J_UART et J_ANA (−2 références) ;
  - remplacer les résistances ILIM/VIO Extended par des valeurs Basic proches (au prix de limites de courant moins précises) ;
  - ne passer en Basic que là où ça ne dégrade pas la fonction.
- Le STM32G431 (5.14 $) représente un tiers du coût composants.

### Points à valider au checkpoint
1. **Moniteur de courant** : INA226 en stock (résolution 50 µA / 25 µA) **ou** INA228 envoyé à JLCPCB par nos soins (résolution ≈ 6 µA / 3 µA, mesure de veille au µA). Les deux ont le **même brochage** : on peut monter l'INA226 maintenant et passer à l'INA228 plus tard sans refaire le PCB (le firmware change).
2. **MCU STM32G431RBT6** : seul STM32 adapté en stock ; pas de firmware CMSIS-DAP open-source existant sur cette famille (portage à faire).
3. **TCA9517A au lieu du PCA9306** pour l'I2C DUT (le PCA9306 ne couvre pas VIO 1.8 → 5 V).
4. **Frais Extended** (≈ 92 $ par commande) : accepter, ou regrouper les headers J_UART et J_ANA en un seul 1×7.
5. **Écran** : module enfiché à la main sur un support (non posé par JLCPCB).

## Phase 2 — Schéma (TASK-005)

### Méthode de génération
- `kiutils` ne gère pas le format KiCad 10 : le schéma est produit par un générateur maison.
  - `scripts/sexpr.py` : lecture/écriture S-expression.
  - `scripts/symlib.py` : lecture des symboles des librairies KiCad 10 (aplatissement des `extends`, géométrie des broches, fonctions alternatives des broches STM32).
  - `scripts/schgen.py` : placement automatique par blocs, fil court + label sur chaque broche, symboles power pour GND / +3V3 / +5V / VBUS, labels globaux pour les nets partagés entre feuilles. Écrit au format KiCad 8, puis `kicad-cli sch upgrade` convertit au format KiCad 10.
  - `scripts/build_schematic.py` : **description du design** (broche → net), une fonction par feuille. Les champs Footprint / MPN / Manufacturer / Datasheet / LCSC viennent de `scripts/bom_draft.py` via le code LCSC (source unique).
  - `scripts/build_symbols.py` : symboles absents des librairies officielles (`lib/OOTY.kicad_sym`).
- **Vérifications automatiques** :
  - `scripts/verify_netlist.py` : exporte la netlist KiCad et compare chaque net à la description → **159 nets, 0 écart**.
  - `scripts/check_bom.py` : quantités par code LCSC schéma vs BOM → **156 composants, 0 écart** (le module OLED, enfiché à la main, est hors schéma).
  - `scripts/run_checks.py --erc-only` → **0 erreur, 1 warning justifié** (ci-dessous).
  - `scripts/render_schematic.py` : PDF `out/OOTY_schematic.pdf` + PNG par feuille dans `out/renders/`.

### Feuilles
| Feuille | Contenu |
|---|---|
| power | USB-C, ESD USB, TVS + PTC VBUS, buck 3V3, 4 × AP22653, LED alim, points de test |
| mcu | STM32G431RBT6, découplage, BOOT0, connecteur SWD HIL, LED heartbeat |
| sensing | 2 × INA226 + shunts, I2C interne, connecteur OLED, entrées ADC, moniteur VIO, buffer DAC |
| vio | Mux TPS2116, LDO AP2127K-ADJ et sélection 1.8 / 3.3 V |
| translators | 2 × SN74LVC8T245, 2 × SN74LVC1T45 (SWD), TCA9517A, RESET/BOOT open-drain |
| connectors | Résistances série, 8 × TPD4E05U06, 5 headers DUT, trous M3 |

### Symboles projet (`lib/OOTY.kicad_sym`)
- `AP22653W6` : brochage SOT26 de la datasheet DS41186 Rev. 5-2 (« Pin Descriptions ») : 1 IN, 2 GND, 3 EN (actif haut), 4 FAULT, 5 ILIM, 6 OUT.
- `TLV9001IDBV` : graphique du symbole officiel OPA333xxDBV, même brochage DBV (1 OUT, 2 V−, 3 IN+, 4 IN−, 5 V+), vérifié contre la datasheet TLV9001.

### Affectation des broches du STM32G431RBT6
Fonctions alternatives vérifiées dans le symbole KiCad (`MCU_ST_STM32G4:STM32G431RBTx`, champs `alternate`) :

| Fonction | Broches |
|---|---|
| USB FS | PA11 DM, PA12 DP |
| SWD carte HIL | PA13 SWDIO, PA14 SWCLK, PB3 SWO, PG10 NRST, PB8 BOOT0 |
| I2C interne (I2C1) | PA15 SCL, PB7 SDA |
| I2C DUT (I2C3) | PC8 SCL, PC9 SDA |
| SPI DUT (SPI1) | PA5 SCK, PA6 MISO, PA7 MOSI, PA8 CS (GPIO) |
| UART DUT (USART3) | PB10 TX, PB11 RX |
| SWO DUT (USART2_RX) | PA3 |
| Sonde SWD DUT | PB13 SWCLK (SPI2_SCK), PB15 SWDIO (SPI2_MOSI), PB2 SWCLK_DIR, PB12 SWDIO_DIR |
| OUT1–4 | PA0, PA1, PA2 (TIM2_CH1–3, PWM possible), PB0 |
| IN1–4 | PC10, PC11, PC12, PD2 |
| ADC | PC0 AIN1, PC1 AIN2, PC2 CC1, PC3 CC2, PB1 VIO_MON |
| DAC | PA4 (DAC1_OUT1) |
| Rails | PC13 EN_5VSW, PC14 EN_3V3SW, PC15 / PF0 / PF1 / PB5 FAULT, PB9 INA_ALERT |
| VIO / translateurs | PC4 PR1, PC5 MODE, PB14 VSEL, PA9 LS_OE_N, PB6 I2C_DUT_EN |
| Divers | PA10 LED heartbeat, PC6 RESET DUT, PC7 BOOT DUT, PB4 libre |

- PB4 et PB6 portent les pull-downs « dead battery » de l'UCPD au reset : PB4 n'est pas utilisée, PB6 commande I2C_DUT_EN (bas = buffer désactivé, état sûr). À confirmer dans le RM0440 avant le firmware.
- PC13–PC15 ont une sortance limitée (3 mA, 2 MHz) : utilisées seulement pour EN et FAULT (signaux lents).

### Warning ERC justifié
- `pin_to_pin` (warning) sur la feuille translators : la broche B8 (bidirectionnelle) du SN74LVC8T245 d'entrée est reliée à GND. C'est voulu : avec DIR = B→A, B8 est une entrée inutilisée, à tirer à un niveau fixe pour ne pas la laisser flotter (recommandation habituelle pour les entrées CMOS).

### Revue électrique indépendante du schéma (2026-10-19) et corrections
Relecture par un agent séparé, contre les datasheets TI / Diodes (le site ST n'était pas accessible : points STM32 vérifiés via les fonctions alternatives du symbole KiCad).

| # | Gravité | Constat | Correction |
|---|---|---|---|
| 1 | MAJEUR | TPS2116 : avec MODE bas et PR1 bas, le mux passe la tension la plus haute (5 V). PR1 tiré à +3V3 → pendant la montée du buck (soft-start 800 µs) ou si le 3V3 tombe, **5 V sur VIO** possible. | PR1 tiré depuis **+5V** par un diviseur 10k / 22k (3.44 V, > VREF dès que VIN1 > ≈ 1.6 V). PC4 tire PR1 au niveau bas. Règle firmware : jamais PR1 bas avec MODE bas. |
| 2 | MAJEUR | BOOT en open-drain (2N7002) ne peut pas mettre un BOOT0 STM32 (actif haut) au niveau haut. | BOOT via un **SN74LVC1T45** : sortie push-pull à VIO (DIR haut) ou haute impédance (DIR bas, état au reset). RESET reste open-drain (NRST / EN). |
| 3 | mineur | TCA9517A : EN a un pull-up interne vers VCCB → buffer actif au reset. | Pull-down 10 kΩ sur I2C_DUT_EN. |
| 4 | mineur | Entrées CMOS flottantes côté DUT des translateurs (« unused data inputs must be held high or low »). | 10 × 1 MΩ : pull-down sur IN1–4, MISO, SWCLK, BOOT ; pull-up à VIO sur RX, SWO, SWDIO (pratique SWD/UART). 1 MΩ pour ne pas perturber le DUT (ex. pull-up interne ESP32 IO0 ≈ 45 kΩ). |
| 5 | mineur | Tenue « 24 V » des AIN fausse (TVS avant la résistance). | Note corrigée : 0–5.5 V. |
| 6 | mineur | Capacité sur VBUS/+5V > 10 µF (limite USB 2.0). | 10 µF/25 V sur +5V retiré : reste buck Cin 10 µF + 2 × 1 µF + 100 nF (≈ 7 µF après derating). |
| 7 | mineur | CC1/CC2 sans ESD. | TPD4E05U06 dédié près de l'USB-C (2 voies utilisées). |
| 8 | mineur | Cff du buck absent du schéma. | 6.8 pF 0402 **non monté** (DNP) en parallèle sur le 100 kΩ. |
| 9 | mineur | SMAJ5.0A : Vc 9.2 V > 6 V abs. max de TLV62569 / AP22653 / TPS2116. | Accepté et documenté : protection partielle contre les surtensions lentes ; le PTC + TVS absorbent les transitoires ESD/hot-plug usuels. Une TVS à clamp plus bas (ex. 5 V, Vc ≈ 7 V) pourra être évaluée en rev B. |
| 10 | question | DFU USB sans quartz (AN2606) non vérifié. | SWD reste le chemin de programmation principal. |
| 11 | question | 10 µF sur VIO à charger par le VTref du DUT en mode externe. | Réduit à 1 µF (+ 100 nF par translateur ≈ 1.6 µF). |

Après corrections : ERC 0 erreur (1 warning justifié), 165 nets 0 écart, 170 composants schéma = BOM.

### Réévaluation MCU et mesure de courant (2026-10-19, demande de l'utilisateur)

**MCU : STM32G431RBT6 conservé.**
| Candidat (LQFP64) | Stock / prix (JLC) | Verdict |
|---|---|---|
| STM32G431RBT6 | 2659 / 5.76 $ | Retenu : USB FS sans quartz, DAC, 170 MHz, 128K/32K, stock solide |
| STM32H503RBT6 | 242 / 5.96 $ | Équivalent (250 MHz) mais stock faible, aucun gain réel |
| STM32H562RGT6 | 709 / 8.40 $ | Seule évolution crédible si RAM/flash manquent (640K RAM) ; ré-affectation complète des broches |
| STM32G474RET6, U535/U545 | 15 / 0–21 | Stock insuffisant |
| STM32G0B1RET6, F072RBT6 | 0 | Rupture |
| STM32C071RBT6 | 960 / 5.12 $ | Pas de DAC, 24K RAM |

- **Vitesse de la sonde SWD** : limitée par la latence des transactions USB (trames 1 ms) et la qualité du firmware, pas par l'horloge MCU ni par le débit FS. Mesures publiées (cible STM32H743) : CMSIS-DAP v2 FS ≈ 54 kB/s, ST-Link V2 (FS) ≈ 160–180 kB/s, sondes HS ≈ 0.3–1.1 MB/s. Un firmware v2 qui regroupe les transferts peut viser la classe ST-Link V2 → quelques secondes pour 64–256 Ko. Aucun STM32 LQFP64 en stock n'a de PHY USB HS intégré ; le HS n'est pas justifié ici.
- SWCLK/SWDIO du DUT sont sur SPI2 (PB13/PB15) : SWD cadencé par le SPI possible (plusieurs MHz), sinon bit-bang à 170 MHz.
- Aucun firmware de sonde open-source n'existe pour G4 (ni H5) : le portage passe par les sources CMSIS-DAP d'Arm (`DAP.c`, `SW_DP.c`) + TinyUSB (driver `stm32_fsdev`, 1 Ko de PMA suffisant : ≈ 610–740 o pour EP0 + DAP v2 + 2 CDC).
- Source benchmark : https://9names.github.io/embedded/rust/debug/2022/04/07/cmsisdap-probe-performance.html

**Mesure de courant : INA226 monté, INA228 recommandé dès disponibilité (même empreinte).**
- INA228 : 0 en stock chez LCSC/JLC et DigiKey (réassort annoncé janvier 2027), seulement chez des brokers (risque de contrefaçon). Le global sourcing JLC ne peut rien tant que DigiKey est à 0 ; reste la consignation (l'utilisateur envoie les pièces).
- Performances attendues (shunt 100 mΩ sur 3V3_SW, 50 mΩ sur 5V_SW, après calibration du zéro rail coupé) :

| Courant | INA226 (monté) | INA228 (évolution) |
|---|---|---|
| 10 µA | non mesurable (LSB 25–50 µA) | résolution 0.8–1.6 µA, ±2–3 µA |
| 1 mA | ≈ ±5–10 % | ≈ ±1.2 % |
| 100 mA – 1 A | ≈ ±1.1 % | ≈ ±1.05 % (≈ 0.2 % avec calibration de gain) |

- Shunt 5V_SW gardé à **50 mΩ** (et pas 100 mΩ) : avec l'INA226 la pleine échelle serait sinon 819 mA, sous la limite de 1.1 A du rail.
- **Correction** : la broche Vbus des INA est maintenant reliée **en amont** du shunt (`*_PRE`) ; son impédance d'entrée (≈ 0.8–1 MΩ) faisait passer ≈ 3–5 µA dans le shunt, invisibles à la calibration du zéro. Le firmware corrige V_charge = V_bus − I·R.
- Firmware : auto-range ADCRANGE (INA228), calibration du zéro quand le rail est coupé.
- Un vrai 10 µA ±1 % demanderait une architecture double gamme (shunt commuté type Nordic PPK2 / Joulescope) : commutation rapide de MOSFET, creux d'alimentation sur le DUT, layout critique → **hors rev A** (risque élevé), à étudier pour une rev B.

## Rapports ERC / DRC justifiés

### TASK-002 — projet vide
- **ERC** : 0 violation.
- **DRC** : 1 erreur `invalid_outline` (« Board has malformed outline (no edges found on Edge.Cuts layer) »). Attendue : le contour de carte n'est dessiné qu'en Phase 3. Ne bloque pas les phases 0 à 2.

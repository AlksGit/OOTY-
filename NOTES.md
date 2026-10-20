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

### MCU : STM32G431RBT6 (LQFP-64) — remplacé par le STM32G431MBT6 (LQFP-80) le 2026-10-20
> Même puce en boîtier 80 broches : les 64 broches étaient toutes utilisées. Voir « Revue des checkpoints Phases 2–4 ».
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
- Rails commutés : EN piloté par le MCU avec pull-down 100 kΩ (OFF pendant le boot ; VIH min 1.5 V).
- Rails fixes (depuis le 2026-10-20) : EN piloté par le MCU avec **pull-up 100 kΩ vers IN** → allumés au démarrage comme avant, mais le firmware peut les couper (budget USB insuffisant, FAULT persistant).

### Protection d'entrée VBUS
- PTC 1812 SMD1812P260TF (8 V, Ihold 2.6 A, Itrip 5 A) : dernier recours pour un défaut sur 5V_SYS lui-même ; la limitation fine est faite par les 4 AP22653. Chute : 10 mΩ typ. (≈ 22 mV à 2.2 A) mais **R1max 50 mΩ après déclenchement → jusqu'à 110 mV** (correction de la revue du 2026-10-20).
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
- **Mux TPS2116** : VIN1 = **5V_DUT** depuis le 2026-10-20 (sortie limitée du rail 5 V fixe ; avant : 5V_SYS non limité), VIN2 = sortie du LDO AP2127K-ADJ (1.8 ou 3.3 V), VOUT = VIO.
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
| power | USB-C, ESD USB, PTC puis TVS, buck 3V3, 4 × AP22653, LED alim, points de test VBUS / +5V / +3V3 / GND |
| mcu | STM32G431MBT6, découplage, BOOT0 (pont de soudure), connecteur SWD HIL, LED heartbeat, 2 boutons |
| sensing | 2 × INA226 + shunts, I2C interne, connecteur OLED, entrées ADC, moniteur VIO, buffer DAC |
| vio | Mux TPS2116, LDO AP2127K-ADJ et sélection 1.8 / 3.3 V |
| translators | 2 × SN74LVC8T245, 2 × SN74LVC1T45 (SWD), TCA9517A, RESET/BOOT open-drain |
| connectors | Résistances série, 8 × TPD4E05U06, 5 headers DUT, trous M3 |

### Symboles projet (`lib/OOTY.kicad_sym`)
- `AP22653W6` : brochage SOT26 de la datasheet DS41186 Rev. 5-2 (« Pin Descriptions ») : 1 IN, 2 GND, 3 EN (actif haut), 4 FAULT, 5 ILIM, 6 OUT.
- `TLV9001IDBV` : graphique du symbole officiel OPA333xxDBV, même brochage DBV (1 OUT, 2 V−, 3 IN+, 4 IN−, 5 V+), vérifié contre la datasheet TLV9001.

### Affectation des broches du STM32G431MBT6 (LQFP-80, mise à jour du 2026-10-20)
> Table mise à jour en TASK-011 avec l'affectation de TASK-010 (double calibre, relecture des rails fixes).

Brochage du symbole KiCad `MCU_ST_STM32G4:STM32G431MBTx` vérifié broche par broche contre DS12589 Rev 1 Figure 11 (LQFP80). Fonctions alternatives vérifiées dans le symbole (champs `alternate`) :

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
| OUT1–4 | PA0, PA1, PA2 (TIM2_CH1–3, PWM possible), PE9 |
| IN1–4 | PC10, PC11, PC12, PD2 |
| ADC | PC0 AIN1, PC1 AIN2, PC2 CC1, PC3 CC2, PB1 VIO_MON |
| Double calibre (ADC1 / ADC2) | PB14 I_5VSW_LO, PC4 I_5VSW_HI (IN5) ; PF0 I_3V3SW_LO, PF1 I_3V3SW_HI (IN10) |
| Relecture rails fixes | PB0 V_5V_DUT (ADC1_IN15), PC5 V_3V3_DUT (ADC2_IN11) |
| Bascules de calibre | PA10 RANGE_CLK_5VSW, PB4 RANGE_CLK_3V3SW, PD0 RANGE_5VSW, PD1 RANGE_3V3SW |
| DAC | PA4 (DAC1_OUT1) |
| Rails | PC13 EN_5VSW, PC14 EN_3V3SW, PD8 EN_5V, PD9 EN_3V3, FAULT : PC15 5V_SW, PE8 3V3_SW, PE7 5V, PB5 3V3 ; PB9 INA_ALERT |
| VIO / translateurs | PE14 PR1, PE15 MODE, PE13 VSEL, PA9 LS_OE_N, PB6 I2C_DUT_EN |
| RESET / BOOT DUT | PC6 RESET, PC7 BOOT (donnée), PD10 BOOT_DIR |
| Interface locale | PE12 LED heartbeat, PE11 BTN1, PE10 BTN2 |
| Libres | aucune |

- **BOOT_DIR n'est plus sur PB4** : après reset, PB4 = NJTRST avec pull-up interne 25–55 kΩ (DS12589 Table 12, note 4), plus fort que le pull-down 100 kΩ → DIR haut et broche BOOT du DUT pilotée pendant chaque reset de la carte HIL. PD10 n'a pas de pull au reset.
- Le choix des broches suit le plan de placement (MCU tourné de 180°) : EN / BOOT_DIR sur le côté tourné vers l'alimentation et le debug, boutons et LED sur le côté tourné vers le coin haut-droit.
- PB6 (I2C_DUT_EN) peut porter le pull-down « dead battery » de l'UCPD1 au reset (PA9 = DBCC1 tiré haut par le pull-up de LS_OE_N) : sans danger (bas = buffer désactivé). Le firmware écrit `PWR_CR3.UCPD1_DBDIS = 1` en tout premier. À confirmer dans le RM0440.
- PC13–PC15 ont une sortance limitée (3 mA, 2 MHz) : utilisées seulement pour EN et FAULT (signaux lents).

### Warnings ERC justifiés
- 2 × `pin_to_pin` (warning) sur la feuille translators : les broches A8 et B8 (bidirectionnelles) du SN74LVC8T245 d'entrée sont reliées à GND. C'est voulu : le canal 8 n'est pas utilisé et la datasheet impose un niveau fixe sur toutes les entrées (« must have a logic HIGH or LOW level applied »). A8 à GND ne crée pas de conflit une fois le buffer activé : avec DIR = B→A, A8 recopie B8, c'est-à-dire un niveau bas.

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
- **Mise à jour du 2026-10-20** : l'utilisateur demande la double gamme en rev A → voir « Mesure double calibre et relecture des rails fixes (TASK-010) ».

## Revue des checkpoints Phases 2–4 (2026-10-20)

L'utilisateur ne relit pas le hardware : les trois checkpoints (schéma, setup PCB, placement) ont été relus par trois agents indépendants, contre les datasheets (rapports complets conservés hors dépôt). Bilan : aucun bloquant sur le schéma, setup PCB sain à quelques règles près, **placement à refaire avant routage** (cellule buck, découplage du MCU, organisation des blocs).

### Décisions de l'utilisateur
| # | Sujet | Décision |
|---|---|---|
| D1 | Rails fixes 5 V / 3V3 toujours actifs (le firmware ne pouvait pas respecter le budget USB ni couper un court-circuit franc qui fait cycler l'AP22653 à ≈ 3.2 W) | EN sur GPIO + pull-up 100 kΩ vers IN : **allumés par défaut, coupables par le firmware** |
| D2 | VIO 5 V pris sur +5V sans limitation (un court sur VIO faisait tomber la carte HIL) | TPS2116 VIN1 sur **5V_DUT** (limité ≈ 0.64 A, FAULT relu) |
| D3 | INA226 / INA228 | **INA226 monté**, INA228 en évolution (même empreinte) |
| D4 | Références des 0402 sur le plan de montage seulement | Accepté, à condition que tous les CI / connecteurs / LED / TP / Q / D soient en sérigraphie, TP marqués par leur net, aucune référence ambiguë |
| D5 | Nouveau besoin | **2 boutons poussoirs** sur la carte, lus par le STM32 |
| D6 | Plus aucune broche libre sur le LQFP-64 (il en fallait 4) | **STM32G431MBT6 (LQFP-80)**, même puce, 14 GPIO de plus |

### MCU LQFP-80 : approvisionnement
- STM32G431MBT6, LCSC C730099 : **0 en stock chez JLC** le 2026-10-20 (API JLC), ≈ 6.13 $. En stock chez Mouser et Farnell (vérifié par l'utilisateur sur Octopart) → **global sourcing JLC** (ou consignation). Délai et frais à prévoir en Phase 6.
- Empreinte `Package_QFP:LQFP-80_12x12mm_P0.5mm`. 5 broches VDD (16, 41, 51, 62, 80) → 5 × 100 nF + 4.7 µF.

### Corrections du schéma
| Gravité | Constat | Correction |
|---|---|---|
| MAJEUR | BOOT_DIR sur PB4 : pull-up NJTRST au reset → BOOT du DUT piloté pendant les resets HIL | BOOT_DIR sur PD10 (pas de pull au reset) |
| MAJEUR | D1, D2 (ci-dessus) | Appliqué |
| mineur | TVS avant le PTC : une surtension durable chauffe la TVS sans faire déclencher le PTC | SMAJ5.0A **après** le PTC (sur +5V) |
| mineur | Cin du buck 10 µF/10 V 0603 : ≈ 4–5 µF effectifs sous 5 V | 10 µF/25 V 0805 (C15850, déjà en BOM) |
| mineur | Entrées CMOS flottantes : U15 A8, port B de U14 quand /OE est haut | A8 à GND ; 8 × 1 MΩ sur le port B de U14 (TX et CS vers VIO, les autres vers GND) |
| mineur | TP BOOT0 « à court-circuiter » sans pastille 3V3 voisine | Pont de soudure BOOT0 ↔ 3V3 (JP1) |
| mineur | Voies ESD mal réparties (TVS des entrées analogiques à 38 mm de J7) | Voies regroupées par header : chaque TPD4E05U06 dessert un seul connecteur (ou deux connecteurs voisins) |
| mineur | Champ Datasheet vide sur les passifs | Lien vers la fiche LCSC par défaut |
| mineur | Points de test des rails DUT et de VIO redondants avec J_PWR / J_DBG | Supprimés (VBUS, +5V, +3V3, GND conservés) |
| ajout | D5 | SW1 / SW2 TS-1187A-B-A-B (LCSC C318884, Basic, 278 750 en stock), actifs bas, pull-up 10 kΩ + 100 nF ; empreinte officielle `SW_Push_1P1T_XKB_TS-1187A` vérifiée contre la datasheet (pastilles 1.0 × 0.75 mm à ±3.0 / ±1.875 mm) |

Résultat : ERC 0 erreur (2 warnings justifiés), 178 nets 0 écart, 187 composants schéma = BOM.

### Points documentés sans changement de schéma
- **Rails 5 V non régulés** : au pire cas, VBUS 4.75 V − 110 mV (PTC) − 135 mV (AP22653, 1 A) − 50 mV (shunt) ≈ **4.45 V** sur 5V_SW, avant la chute du câble USB.
- **Sortie DAC** : R33 (100 Ω) est hors de la boucle du suiveur → erreur = I × 100 Ω (0.5 V à 5 mA) ; 0–3.3 V à vide, la sortie n'atteint pas le rail en charge.
- **TPS2116** : le blocage du courant inverse se déclenche si l'on passe d'une tension VIO à une plus basse sans arrêt. Règle firmware : passer par l'arrêt (MODE = 0, PR1 = 1), attendre la décharge (VIO_MON, ≈ 0.3 s via le diviseur 200 kΩ), puis changer VSEL / PR1.
- **Capacité de sortie du buck** ≈ 52 µF nominaux (≈ 35–40 µF effectifs) pour une plage validée de 10–47 µF : à vérifier au banc par un échelon de charge.
- **Court franc sur un rail 3V3** : creux estimé ≈ 0.5 V pendant les 5 µs de réaction de l'AP22653, au-dessus de l'UVLO et du BOR : à vérifier au banc (exigence n°8 de la SPEC).
- **Module OLED** : brochage (1 GND, 2 VCC, 3 SCL, 4 SDA) à confirmer sur un échantillon avant commande (inversion GND/VCC destructrice).

## Phase 3 — Setup PCB (TASK-006)

Généré par `scripts/build_pcb.py` (Python de KiCad) à partir de la netlist du schéma ; positions dans `scripts/placement.py`.

### Carte
- **85 × 55 mm**, coins arrondis R2, 4 trous M3 (Ø 3.2 mm) à 3.5 mm des bords.
- Les headers DUT imposent la taille : J_PWR + J_DBG + J_IO = 61 mm sur le grand côté (entre les trous : 85 − 2 × 7 = 71 mm), J_BUS + J_UART_ANA = 34 mm sur le petit côté droit (55 − 14 = 41 mm). Une carte plus petite ne laisse pas la place aux 5 headers 2.54 mm hors des trous.
- Disposition : USB-C sur le bord gauche (façade **au ras du bord** depuis le 2026-10-20 ; elle était 0.55 mm en retrait), J_PWR / J_DBG / J_IO en bas, J_BUS / J_UART_ANA à droite, support OLED en haut (le module 38 × 12 mm couvre la bande x ≈ 20–58 mm, des CMS bas passent dessous), LED et boutons en haut à droite (visibles par webcam, hors du module).
- **Zone sans cuivre Ø 7 mm** (pistes, vias, remplissage) autour de chaque trou M3 : tête de vis M3 Ø 5.6 mm + marge.

### Empilement (JLC04161H-7628, 1.6 mm)
| Couche | Rôle | Épaisseur |
|---|---|---|
| F.Cu | Signaux + composants | 35 µm |
| prepreg 7628 | | 0.2104 mm |
| In1.Cu | **Plan GND continu** | 15.2 µm |
| core | | 1.065 mm |
| In2.Cu | Plans d'alimentation (+5V, +3V3) | 15.2 µm |
| prepreg 7628 | | 0.2104 mm |
| B.Cu | Signaux | 35 µm |

L'empilement est écrit dans le fichier par script (non exposé par l'API pcbnew).

### Règles et classes de nets
- Défaut : piste 0.2 mm (min 0.15), isolement 0.15 mm, via 0.6 / 0.3 mm (plus petit via autorisé 0.5 / 0.2), cuivre–bord 0.3 mm, trou–trou 0.5 mm, **anneau min 0.15 mm**, **texte sérigraphie min 1.0 mm / trait 0.15 mm**. Au niveau ou au-dessus des minima JLCPCB (piste/isolement 0.09, anneau 0.15, texte 1.0 / 0.15). Les minima anneau (0.13) et texte (0.8 / 0.08) de la première version étaient sous les capacités JLC : corrigés le 2026-10-20.
- Largeurs IPC-2221 (ΔT = 10 °C) :

| Courant | Externe 1 oz | Interne 0.5 oz |
|---|---|---|
| 0.5 A | 0.12 mm | 0.60 mm |
| 1.2 A | 0.39 mm | 2.0 mm |
| 2.5 A | 1.06 mm | 5.5 mm |

- **Power** (0.5 mm, isolement 0.15, via 0.8 / 0.4) : +3V3, 5V_SW*, 5V_DUT, 3V3_SW*, 3V3_DUT, VIO, VIO_LDO, GND, nœud SW du buck — jusqu'à ≈ 1.45 A en externe. Le motif `VIO*` captait des signaux logiques (VIO_PR1, VIO_MODE, VIO_VSEL, VIO_MON) : remplacé par les deux nets de puissance.
- **HighCurrent** (**1.5 mm**, isolement 0.2) : VBUS, +5V — ≈ 3.2 A en externe 1 oz à ΔT 10 °C (source USB-C 3 A) ; au moins 3 vias 0.4 mm par changement de couche ; en interne, +5V et +3V3 passent par des zones larges sur In2.
- **USB** (0.25 mm, paire différentielle écart 0.2 mm) : USB_DP / USB_DM. Sur ce prépreg (0.2104 mm, εr 4.4) cette géométrie donne **≈ 105 Ω différentiel** (microstrip), pas 90 Ω : sans conséquence en Full Speed (12 Mbit/s, fronts ≥ 4 ns) sur ≈ 25 mm ; paire symétrique au-dessus du plan GND In1.
- L'isolement de la classe Power a été ramené de 0.2 à 0.15 mm : 0.2 mm était incompatible avec les boîtiers au pas de 0.5 mm (INA226, TCA9517A).

### Vérification
- DRC `--schematic-parity` : **0 erreur, 0 écart de parité** ; nets non routés attendus à ce stade ; 5 warnings de sérigraphie (références de headers) traités au placement.

## Phase 4 — Placement (TASK-007) — refait le 2026-10-20 après la revue

### Méthode
- `scripts/placement.py` : connecteurs, trous et **ancres** placés à la main : tous les CI, les pièces de puissance, la cellule buck complète, les ESD, les points de test, LED et boutons.
- `scripts/autoplace.py` : placement glouton du reste, en trois passes :
  1. les condensateurs de découplage, chacun visé sur **la broche qu'il découple** (déclarée dans le schéma, `near=` dans `build_schematic.py`, et vérifiée contre les nets) ;
  2. la sérigraphie des pièces déjà placées est réservée (`silk.reserve`) ;
  3. les autres pièces visent le pad du net le plus spécifique (résistance série → translateur / ESD, pull-up → broche, etc.).

  Recherche en spirale sur une grille de 0.25 mm, sans chevauchement de courtyards.
- `scripts/silk.py` : références en 1.0 mm / 0.15 mm. Une référence ne peut chevaucher ni un pad, ni le courtyard d'une autre pièce, ni un autre texte : aucune référence ne peut être lue comme celle d'un voisin. Les références des headers sont placées entre les rangées d'étiquettes de broches, celles des points de test sont remplacées par le nom du net.
- `scripts/check_placement.py` : distance de chaque condensateur déclaré à **sa** broche (limite 3 mm, 6 mm pour le bulk ≥ 1 µF), et longueur du ratsnest des signaux (arbre couvrant minimal, plans exclus).
- `scripts/plot_placement.py` : vue courtyards + références + ratsnest (`out/renders/pcb_placement_ratsnest.png`), pour comparer les itérations.
- `scripts/render_pcb.py` : rendus 3D dessus / dessous / isométrique, SVG du placement, plan de montage PDF (F.Fab).

### Problèmes du premier placement (revue)
- **Buck** : nœud SW du côté opposé à l'inductance, Cin loin de VIN, 100 nF sur EN au lieu de VIN, Cout à 9–11 mm.
- **Découplage du MCU** : condensateurs visant le centre de la carte (groupe schéma sans CI), VDD pin 48 à 9.9 mm ; le contrôle ne couvrait que 37 condensateurs sur 54 et rattachait certains au mauvais CI.
- **Blocs dispersés** : USB à 46 mm à travers les limiteurs, chaîne de debug à 44–48 mm de J_DBG, TVS analogique à 38 mm de J_UART_ANA, rails DUT à 45–55 mm de J_PWR.

### Plan de placement
| Zone | Contenu |
|---|---|
| Bord gauche | USB-C au ras du bord, USBLC6 dans l'axe de D+/D−, ESD CC + Rd 5.1 kΩ, PTC puis TVS sous le connecteur |
| Haut-gauche | Buck TLV62569 : Cin (10 µF + 100 nF) contre VIN, inductance directement sur SW, 2 × 22 µF à la sortie de l'inductance, diviseur FB du côté FB ; points de test +3V3 / GND |
| Gauche, sous le buck | 2 × INA226 (lignes de mesure Kelvin vers les shunts) |
| Bas-gauche, au-dessus de J_PWR | 4 × AP22653 dans l'ordre des broches de J_PWR, shunts dans l'axe de leurs broches, ESD des rails entre les shunts |
| Centre | STM32G431MBT6 **tourné de 180°** : USB face à l'USB-C, sonde SWD / RESET / BOOT face à J_DBG, SPI / DAC / ADC face à J_BUS et J_UART_ANA ; découplage sur chaque broche d'alimentation |
| À gauche du MCU | Connecteur SWD de la carte HIL |
| Haut, sous le module OLED | Mux VIO TPS2116 + LDO AP2127 + sélection 1.8 / 3.3 V (CMS bas) |
| Au-dessus de J_DBG | 2 × SN74LVC1T45 (SWCLK, SWDIO), 2N7002 (RESET), SN74LVC1T45 (BOOT), ESD |
| Au-dessus de J_IO | 2 × SN74LVC8T245 (côté A vers le MCU, côté B vers le header), résistances série et de polarisation, ESD |
| Bord droit | ESD contre J_BUS / J_UART_ANA, TCA9517A, buffer DAC |
| Coin haut-droit | LED PWR / HB, boutons SW1 / SW2, marquage « OOTY HIL rev A / 2026-10 » |

### Résultats
- DRC `--schematic-parity` : **0 erreur, 0 écart de parité**. 2 warnings `silk_edge_clearance` : le contour sérigraphié de l'empreinte USB-C est coupé par le bord de carte, conséquence directe de la façade au ras du bord ; JLC rogne la sérigraphie hors carte, sans impact.
- Découplage : **50 condensateurs sur 50 dans leur limite** (le plus loin : 2.8 mm pour le 100 nF découplant le PTC, 4.1 mm pour le 4.7 µF de bulk du MCU).
- Ratsnest des signaux : 2583 mm sur 117 nets (2481 mm sur 108 nets avant la revue). La longueur totale baisse peu, mais les liaisons critiques sont courtes : USB ≈ 25 mm en ligne droite, chaque ESD à côté de son header, résistances série groupées. Les plus longues restent des signaux lents (5V_DUT vers le mux VIO, I2C interne, CC1/CC2 vers l'ADC, FAULT/EN).
- Sérigraphie : toutes les pièces clés (CI, connecteurs, LED, Q, D, boutons, TP, pont de soudure) ont leur référence ; 91 références de passifs sont sur le plan de montage seulement (`out/renders/pcb_placement_assembly_top.pdf`). La BOM interactive (iBOM HTML) sera générée avec les fichiers de fabrication (Phase 6).
- Modèles 3D absents dans la librairie KiCad pour le TPD4E05U06 (USON-10) : sans incidence sur la fabrication.

## Mesure double calibre et relecture des rails fixes (TASK-010, 2026-10-20)

Demande de l'utilisateur : mesurer la veille du DUT à partir de **~1 µA** (résolution ~0.1 µA) sur **3V3_SW et 5V_SW**, avec une bascule de calibre **matérielle et rapide**, et relire la tension des rails fixes 5V_DUT / 3V3_DUT par l'ADC. Cette section remplace la conclusion « double gamme hors rev A » de la réévaluation du 2026-10-19. Composants vérifiés le 2026-10-20 (datasheets + API JLC ; stocks à revérifier avant commande). Conception relue par un agent indépendant ; ses corrections (M1–M4, m5–m11) sont intégrées ci-dessous.

### Architecture (par rail commuté)

```
AP22653 OUT (*_PRE) -- R_low (50 / 100 mOhm, existant) -- *_MID -- R_high 100 Ohm 0.1 % -- 5V_SW / 3V3_SW -- ESD -- J_PWR
                         | INA226 (I2C, existant)            |  M7 (diode silicium 1 A), anode cote MID
                         | INA190A2 "HI" -> ADC2              |  AO3401A (S = MID, D = sortie) : bypass
                                                             |  INA190A2 "LO" -> ADC1
                                                             |  TLV7021 : IN+ = sortie (via 1 kOhm), IN- = seuil
```

- **Calibre fin (LO)** : courant à travers R_high = 100 Ω, lu par un INA190A2 (gain 50) → 5 mV/µA, sur ADC1.
- **Calibre fort (HI)** : le P-MOSFET AO3401A court-circuite R_high ; le courant est lu sur le shunt existant par un second INA190A2 (ADC2, rapide) et par l'INA226 (I2C, lent et précis), inchangé. **Les entrées IN− de l'INA226 et de l'INA190 HI vont sur `*_MID`** (et plus sur la sortie) : sinon le courant de polarisation de l'INA226 traverserait R_high.
- **Bascule vers HI (matérielle)** : le comparateur TLV7021 (sortie open-drain) compare la sortie au seuil ; quand la chute sur R_high dépasse le seuil, il tire PRE̅ d'une bascule SN74LVC1G74 → Q = 1 → 2N7002 passant → grille de l'AO3401A à GND → bypass fermé. La bascule mémorise l'état : une fois le bypass fermé, la chute sur R_high disparaît mais Q reste à 1. PRE̅ domine CLK (table 8-1 du SN74LVC1G74) : aucune commande du firmware ne peut rouvrir le bypass tant que le courant dépasse le seuil.
- **Commande firmware (bascule en T)** : **D relié à Q̅**, CLR̅ à +3V3. Chaque front montant de CLK inverse l'état ; le firmware lit Q (RANGE_*) avant et après. Il peut donc **forcer HI** (par exemple avant d'activer un rail, ou en permanence pour un DUT sensible à la chute) et **revenir en LO**. Un retour automatique en matériel est impossible : en HI, le seuil de retour (~0.3 mA) correspond à 15–30 µV sur le shunt fort, sous l'offset de tout comparateur.
- **Diode M7** (redresseur silicium 1 A, SMA) en parallèle sur R_high : limite la chute pendant le temps de bascule et à la mise sous tension en HI (tant que V_MID est sous le V_th de l'AO3401A, l'appel de courant passe par elle). I_FSM 30 A (8.3 ms), V_F 1.1 V max à 1 A. Silicium et pas Schottky : à ~50 mV en direct, le courant détourné suit le courant de saturation (Is ≈ 7 nA pour une 1N4007 → ≈ 7 MΩ en parallèle sur 100 Ω, 15 ppm, ≈ 20 nA à 64 mV ; une Schottky avec Is ≈ 1 µA ferait 0.4 % d'erreur). La 1N4148W initialement prévue (150 mA, 0.5 A sur 1 s) ne tenait pas le court-circuit franc en HI (voir ci-dessous).
- **Seuil** : diviseur pris sur `*_PRE` (en amont des deux shunts, côté pastille de R_low) pour que son courant ne traverse aucun shunt. **5V_SW : 1 kΩ / 150 kΩ** (0.662 %) ; **3V3_SW : 1 kΩ / 100 kΩ** (0.990 %). Pile de tolérances (V_PRE 4.45–5.5 V / 3.25–3.36 V, rapport ±2 %, offset TLV7021 ±8 mV, demi-hystérésis 0.6–7 mV) : déclenchement **21.5–52.1 mV** (5V_SW) et **24.5–48.9 mV** (3V3_SW), soit 0.22–0.52 mA, typiquement 0.33 mA. La pleine échelle du calibre LO est de **62 mV** (sortie INA190 max VS − 40 mV, moins REF à 0.1 V, gain 50 ± 0.3 %) : 10 mV de marge, le calibre LO ne sature jamais avant la bascule.
- **Pilotage du bypass** : grille de l'AO3401A tirée vers `*_PRE` par 100 kΩ (V_GS ≥ 0 à l'arrêt, courant hors des shunts), tirée à GND par le 2N7002 (commande sur Q, 3.3 V). Fermeture rapide (décharge de ~1.5 nC pour passer sous V_th : 100–200 ns) ; ouverture lente (≈ 100 kΩ × 0.9 nF ≈ 0.1–0.2 ms). Conséquence utile : lors d'un retour en LO alors que le courant est encore haut, la chute monte progressivement jusqu'au seuil et le comparateur referme le bypass, **sans impulsion dans la diode**.
- **Référence des INA190** : REF des 4 INA190 polarisé à **≈ 0.1 V** par un diviseur 30 kΩ / 1 kΩ depuis +3V3 (106 mV, ratiométrique avec VREF+), 100 nF, et un **TLV9001 en suiveur** (même référence que le tampon DAC) découplé par 100 nF. Raison (INA190 §6.5 et §7.4) : avec REF à GND, la sortie à courant nul peut rester à +3 mV (V_ZL) et le gain n'est spécifié qu'au-dessus de 0.1 V ; le zéro ne serait ni linéaire ni calibrable (0.6 µA d'erreur en LO, 1.2 mA en HI sur 5V_SW). Avec REF à 0.1 V, la calibration rail coupé mesure REF + offset en zone linéaire (CMRR 132 dB : < 0.013 µA d'écart entre V_CM = 0 et 5 V).
- **Alimentations** : INA190 sur +3V3 (sortie ≤ 3.26 V, compatible ADC). TLV7021 sur **+5V** : mode commun jusqu'à VCC + 0.1 V, les nœuds de 5V_SW restent ≤ +5V ; entrées « fault tolerant » 5.5 V même sans VCC (retour d'alimentation par le DUT sans danger) ; POR qui garde la sortie haute impédance pendant la montée de VCC. Sortie open-drain tirée à +3V3 par 10 kΩ (tenue 6 V indépendante de VCC). **1 kΩ en série sur IN+** (côté sortie, exposé au connecteur : le résidu de l'ESD dépasse les 6 V du comparateur ; retard ≈ 5 ns). Bascule sur +3V3.
- Sorties INA190 vers l'ADC par 100 Ω + 1 nF (charge capacitive max de l'INA190 : 1 nF ; réservoir pour l'échantillonneur).

### Temps de bascule
TLV7021 : t_PHL 260 ns à 100 mV d'overdrive (plus lent près du seuil, ~0.5–1 µs pour un front lent) ; SN74LVC1G74 PRE̅ → Q ≈ 5 ns ; 2N7002 + grille de l'AO3401A 100–200 ns. **Total ≈ 0.4–1.2 µs.** Un DUT avec 10 µF de découplage et un appel de 100 mA perd 0.1 A × 1 µs / 10 µF = 10 mV pendant ce temps ; la diode borne la chute (≈ 1–1.1 V) si le DUT a peu de capacité.

### Performances attendues

| Calibre | Rail | Sensibilité | Plage | Pas ADC 12 bits | Suréchantillonnage ×16 |
|---|---|---|---|---|---|
| LO (100 Ω, ×50) | les deux | 5 mV/µA | 0 → bascule (≥ 0.22 mA garanti, 0.33 mA typ) | 0.16 µA | ≈ 0.04 µA |
| HI rapide (×50) | 3V3_SW, 100 mΩ | 5 mV/mA | 0.63 A | 161 µA | ≈ 40 µA |
| HI rapide (×50) | 5V_SW, 50 mΩ | 2.5 mV/mA | 1.26 A | 322 µA | ≈ 80 µA |
| HI précis (INA226) | 3V3_SW / 5V_SW | — | 0.82 / 1.64 A | 25 / 50 µA (≥ 140 µs par conversion) | — |

- **Calibre LO** : après calibration du zéro (REF polarisé), erreur ≈ ±(0.05 µA + 0.4 %) : offset INA190 ±15 µV max retiré par la calibration, dérive 80 nV/°C max (< 0.01 µA sur 10 °C), gain ±0.3 %, R_high ±0.1 %. Bruit 75 nV/√Hz → 0.18 µA rms sur toute la bande (37 kHz), ≈ 0.02 µA rms moyenné à 1 kS/s. **Visé : 1 µA ± 0.05 µA ; 100 µA ± 0.4 %**, à confirmer au banc.
- Courants parasites dans le calibre LO, comptés comme courant du DUT : fuite de l'ESD TPD4E05U06 du rail (≤ 10 nA à 2.5 V, non spécifiée à 5 V), polarisation de IN− de l'INA190 LO (≤ 3 nA), comparateur (pA). Total ≈ 15–20 nA au pire, < 2 % à 1 µA. Diode et AO3401A bloqué : erreurs de gain de quelques ppm.
- **Zone grossière** : en mesure rapide, entre la bascule (~0.3 mA) et ~20 mA, le calibre HI n'a que quelques pas d'ADC (±0.2–0.3 mA brut). L'INA226 couvre cette zone en moyenné (pas de 25 / 50 µA, conversion ≥ 140 µs). Un troisième calibre comblerait ce trou mais n'est pas demandé.
- **Échantillonnage** : chaque paire LO/HI arrive sur le même numéro de voie des deux ADC (IN5 pour 5V_SW, IN10 pour 3V3_SW) → mode double ADC simultané : les deux calibres d'un rail sont pris au même instant. Les deux signaux RANGE (Q) sont sur le port D (PD0, PD1) : un seul transfert DMA de GPIOD→IDR, déclenché par le même timer. Bande passante de l'INA190A2 : 37 kHz ; établissement 30 µs à 1 % après une bascule.
- **Contraintes ADC** (retour de charge de l'échantillonneur, ~5 pF sur 1 nF : 16 mV pour un saut de 3.3 V, soit 3 µA en LO) : dédier les rangs de séquence aux voies LO/HI sans voie très différente juste avant, ou espacer les échantillons d'une même voie de ≥ 30 µs ; ≥ 47.5 cycles d'échantillonnage, identiques sur les deux ADC (IN10 est une voie lente). Ne pas convertir en même temps sur les deux ADC une voie partagée ADC12_INx (PC0–PC3). Relecture des rails fixes (source 50 kΩ + 100 nF) : ≤ 1 kS/s.

### Chute de tension vue par le DUT

| Situation | 3V3_SW | 5V_SW |
|---|---|---|
| Calibre LO (sous le seuil) | ≤ 52 mV (+ R_low, négligeable) | ≤ 52 mV |
| Bascule (≤ ~1 µs) | ≤ ≈ 1.1 V (diode), filtrée par le découplage du DUT | idem |
| Calibre HI, typique (0.5 A / 1 A, 25 °C) | 50 mV (R_low) + 0.5 A × ≈ 60 mΩ = **80 mV** | 50 mV + 1 A × ≈ 50 mΩ = **100 mV** |
| Calibre HI, pire cas (ILIM max, R_DS(on) max à chaud) | 0.72 A × (100 + ~95 mΩ) ≈ **140 mV** | 1.1 A × (50 + ~80 mΩ) ≈ **145 mV** |

- Par rapport au seul shunt, l'AO3401A ajoute 30–95 mV selon le courant et la température (R_DS(on) max 85 mΩ à −2.5 V, 60 mΩ à −4.5 V, ×1.3–1.5 à chaud). Le 5V_SW au pire cas (VBUS 4.75 V) passe d'environ 4.45 V à environ **4.30 V**, avant la chute du câble.
- La tension DUT estimée en HI (V_bus de l'INA226 sur PRE moins I·R) devient incertaine de ±I·ΔR_DS(on) (≈ ±25 mV à 1 A). Le firmware peut estimer R_DS(on) en ligne : en HI, le calibre LO lit I·R_DS(on).

### Court-circuit du DUT
- **En HI** (Q = 1) : grille et drain à 0 V, l'AO3401A est monté en diode et ne conduit que si V_MID > |V_th| (0.5–1.3 V). À l'ILIM de 5V_SW (1.16 A typ), V_MID ≈ 1.15–1.55 V : l'AO3401A dissipe **1.3–1.8 W** et la diode M7 prend 0.15–0.4 A. L'AO3401A tient ≈ 10–100 ms (Zth transitoire), pas le régime établi (R_θJA 125 °C/W). D'où la règle firmware : **sur FAULT d'un rail commuté, EN bas immédiatement** (le FAULT de l'AP22653 a déjà un filtre de 6 ms), et du cuivre de dissipation sur le drain et la source.
- **En LO** : la chute monte au seuil, le comparateur ferme le bypass → cas précédent.
- **Bascule bloquée en LO (panne)** : la M7 tient 1 A en continu (≈ 1.1 W en SMA, à la limite) ; le firmware coupe le rail (règle ci-dessous).
- À vérifier au banc : le seuil de repli de courant (foldback) de l'AP22653, dont la sortie reste maintenant à 1.2–1.5 V en court-circuit au lieu de 0 V ; court-circuit franc en HI et en LO ; DUT avec 1000 µF.

### Règles firmware
- Au démarrage : lire Q ; si Q = 0, un front de CLK pour forcer HI **avant** d'activer un rail commuté (l'appel de courant passe par le bypass, pas par la diode).
- Retour en LO : tentative périodique (toutes les 1–10 ms) quand l'INA226 moyenné ou le HI calibré indique < ~2 mA ; données invalides pendant 1 ms après chaque front de CLK. Pas de risque pour la diode (ouverture lente du bypass, voir plus haut).
- **Bascule défaillante** seulement si les trois conditions sont vraies : calibre LO saturé, Q = 0, et calibre HI (INA190 HI ou INA226) > 1.5 mA pendant > 100 µs ; règle ignorée pendant 1 ms après chaque front de CLK. Action : couper le rail (EN) et signaler l'erreur.
- **FAULT d'un rail commuté → EN bas immédiatement.**
- Mode « sans chute » : forcer HI et ne jamais revenir en LO.
- Calibration du zéro rail coupé (REF + offset des INA190), puis soustraction. Point de bascule réel de chaque carte mesuré au banc (rampe de charge) et stocké en calibration.
- `PWR_CR3.UCPD1_DBDIS = 1` en premier (voir PA10 / PB4 ci-dessous), puis PB4 en sortie (CLK).

### Solutions de repli (rev A, bloc expérimental)
- **Pont de soudure ouvert en parallèle sur R_high** (empreinte seule) : le fermer ramène au comportement d'avant TASK-010 (shunt fort seul).
- **Empreinte de condensateur non montée côté sortie** (1 µF X7R, fuite ≤ 10 nA à 5 V) pour les DUT très peu découplés : atténue le creux de bascule, au prix d'un filtrage du calibre LO (τ = 100 µs).
- **Points de test** par rail : `*_MID`, RANGE (Q), sorties des deux INA190.

### Relecture de tension des rails fixes
- 5V_DUT et 3V3_DUT : diviseur 100 kΩ / 100 kΩ (×0.5) + 100 nF sur l'entrée ADC. Pleine échelle 6.6 V ; 5.5 V → 2.75 V. Courant 25 / 17 µA pris sur le rail fixe (non mesuré). Constante de temps 5 ms : surveillance lente (rail effondré par un court-circuit ou coupé sur FAULT).

### Composants ajoutés

| Fonction | MPN | LCSC | Type JLC | Qté | Prix unitaire |
|---|---|---|---|---|---|
| Ampli de shunt ×50 | INA190A2IDCKR (SC-70-6 : 1 REF, 2 GND, 3 VS, 4 IN+, 5 IN−, 6 OUT) | C2870223 | Extended | 4 | 1.54 $ |
| Comparateur open-drain | TLV7021DBVR (SOT-23-5 : 1 OUT, 2 VEE, 3 IN+, 4 IN−, 5 VCC) | C2860939 | Extended | 2 | 0.37 $ |
| Bascule D | SN74LVC1G74DCUR (VSSOP-8 : 1 CLK, 2 D, 3 Q̅, 4 GND, 5 Q, 6 CLR̅, 7 PRE̅, 8 VCC) | C70285 | Extended | 2 | 0.30 $ |
| MOSFET P de bypass | AO3401A (SOT-23 : 1 G, 2 S, 3 D) | C15127 | Basic | 2 | 0.10 $ |
| Diode de limitation | M7 (1 A, 1000 V, SMA) | C95872 | Basic | 2 | 0.01 $ |
| Shunt fin 100 Ω 0.1 % 25 ppm | RT0603BRD07100RL (0603, 100 mW) | C122970 | Extended | 2 | 0.03 $ |
| Seuil 5V_SW | 150 kΩ 1 % 0402 (0402WGF1503TCE) | C25755 | Extended (préféré) | 2 | 0.001 $ |
| Tampon de REF | TLV9001IDBVR (existant) | C398363 | Extended (déjà dans la BOM) | +1 | 0.09 $ |
| Commande du bypass | 2N7002 (existant) | C8545 | Basic | +2 | 0.02 $ |
| Passifs existants | 1 k, 30 k, 100 k, 10 k, 100 Ω, 1 nF, 100 nF | — | — | voir BOM | — |

- Surcoût ≈ **8 $ par carte** + 4 nouvelles références Extended (INA190, TLV7021, SN74LVC1G74, résistance 0.1 %) : ≈ 12 $ de frais de chargement par commande. L'INA190A1 (gain 25) n'a que 427 pièces : le gain 50 (3732 pièces) est retenu. Le TLV7021 en SC-70 est en rupture : boîtier SOT-23-5. Option non retenue : TLV3201 (offset ±5 mV, push-pull), la marge du seuil suffit avec le TLV7021.
- Aucun composant validé n'est remplacé (INA226, shunts et AP22653 conservés).

### Nouvelle affectation des broches du MCU (appliquée au schéma en TASK-011)

| Signal | Avant | Après | Raison |
|---|---|---|---|
| I_5VSW_LO (ADC1_IN5) | — | **PB14** | côté gauche, proche du bloc |
| I_5VSW_HI (ADC2_IN5) | — | **PC4** | même voie que LO (double ADC simultané) |
| I_3V3SW_LO (ADC1_IN10) | — | **PF0** | |
| I_3V3SW_HI (ADC2_IN10) | — | **PF1** | même voie que LO |
| V_5V_DUT (ADC1_IN15) | — | **PB0** | |
| V_3V3_DUT (ADC2_IN11) | — | **PC5** | |
| FAULT_3V3SW | PF0 | PE8 | libère l'ADC |
| FAULT_5V | PF1 | PE7 | libère l'ADC |
| VIO_VSEL | PB14 | PE13 | côté haut-gauche, vers le mux VIO |
| VIO_PR1 | PC4 | PE14 | idem ; PE14 est FT (3.44 V du diviseur depuis +5V) |
| VIO_MODE | PC5 | PE15 | idem |
| OUT4_MCU | PB0 | PE9 | sortie simple (pas de PWM sur PB0) |
| RANGE_CLK_5VSW | — | PA10 | bas-gauche, vers le bloc 5V_SW |
| RANGE_CLK_3V3SW | — | PB4 | côté bas |
| RANGE_5VSW (Q) | — | PD0 | les deux Q sur le même port (une lecture DMA) |
| RANGE_3V3SW (Q) | — | PD1 | |

- Vérifié dans le symbole KiCad et DS12589 Table 12 : canaux ADC exacts ; aucune de ces broches n'a de pull au reset sauf PB4 (pull-up NJTRST 25–55 kΩ) ; PE7 est TT_a (FAULT tiré à +3V3, sans problème).
- Toutes les nouvelles entrées ADC restent ≤ 3.3 V par construction (INA190 alimentés en 3V3, diviseurs ×0.5) : la question de la tolérance 5 V d'une broche FT_a en mode analogique ne se pose pas pour elles.
- CLK tirés à GND par 100 kΩ. Sur PB4, le pull-up NJTRST l'emporte au reset (≈ 2.2–2.6 V) : un front CLK possible au reset, inoffensif (rail coupé, le firmware relit Q avant d'activer le rail).
- PA10 est DBCC2 de l'UCPD1 : maintenu bas par le 100 kΩ, il n'active pas le Rd « dead battery » sur PB4 (CC2) ; le firmware désactive de toute façon ce mode en premier.
- Après ce changement, **plus aucune broche libre** sur le LQFP-80.

### Décisions de l'utilisateur (checkpoint TASK-010, 2026-10-20)
Recommandations de la revue acceptées : calibre fin garanti jusqu'à ≥ 0.22 mA ; chute en calibre fort (pire cas ≈ 145 mV) et creux de ≈ 1 µs à chaque bascule acceptés ; plus aucune broche MCU libre ; diode M7 en SMA et solutions de repli (pont, condensateur non monté, points de test).

### Schéma (TASK-011)
- Trois feuilles ajoutées **en fin de hiérarchie** (pour ne pas renuméroter les composants déjà placés) : `range_5v_sw`, `range_3v3_sw` (shunt 100 Ω, pont de repli, M7, AO3401A + 2N7002, comparateur, bascule, 2 INA190, filtres ADC, points de test) et `readback` (référence 0.1 V des INA190, diviseurs des rails fixes).
- Feuille `sensing` : shunts R22 / R23 entre `*_PRE` et `*_MID` ; Vin− des INA226 sur `*_MID`.
- Symboles projet ajoutés (`scripts/build_symbols.py`) : `INA190A2xDCK`, `TLV7021DBV`, `74LVC1G74DCU`, copies des symboles officiels INA199xxDCK, TLV7041DBV et 74AUP1G74 au brochage identique (vérifié contre SBOS863D, SLVSDM5F, SCES794G).
- ERC : 0 erreur, les 2 warnings justifiés habituels (U15 A8/B8). Netlist : 196 nets, 0 écart. BOM : 242 = 242.
- **Placement à reprendre (TASK-012)** : les nets `5V_SW_MID` / `3V3_SW_MID` doivent rejoindre la classe HighCurrent / Power (courant DUT complet).

### Contraintes de layout (pour TASK-012)
1. **Boucle de bypass compacte** : R_low → MID → (R_high ∥ AO3401A ∥ M7) → sortie, pièces accolées, nœud MID réduit à un point.
2. **Kelvin** : R_low vers l'INA226 et l'INA190 HI en paires prises sur les pastilles du shunt ; R_high vers l'INA190 LO idem ; le diviseur de seuil prend PRE côté pastille de R_low.
3. **Nœud de sortie (µA)** : pistes vers IN− de l'INA190 LO et la résistance d'entrée du comparateur courtes, ≥ 0.3 mm des autres nets, loin du nœud SW du buck, de l'USB et de SPI / SWCLK, plan GND continu dessous.
4. **Chaîne rapide** comparateur → bascule → 2N7002 → grille adjacents ; PRE̅ très court (un parasite force HI).
5. **Cuivre de dissipation** sur drain et source de l'AO3401A.
6. **Découplage** 100 nF au plus près de VS de chaque INA190, VCC du TLV7021, VCC du SN74LVC1G74, V+ du TLV9001 de REF.
7. **100 Ω + 1 nF** des sorties INA190 près des broches ADC du MCU.
8. Le bloc ajoute ≈ 45 composants : nouveau checkpoint de placement.

## Placement des blocs double calibre (TASK-012, 2026-10-20)

### Méthode
- **Chaîne de puissance placée à la main** entre chaque limiteur et sa broche de J_PWR : shunt fort horizontal sous la rangée des limiteurs (pastille `*_PRE` côté sortie du limiteur), puis 100 Ω, M7 et AO3401A en parallèle de `*_MID` vers la sortie, résistance de grille 100 kΩ contre le MOSFET. L'ESD des rails (U27) est déplacée à gauche de la broche 1.
- **Comparateurs** (U28, U32) dans la rangée entre le couloir USB et les limiteurs, avec leur diviseur de seuil, la résistance d'entrée et le pull-up de PRE̅ sur le côté libre (broches VCC / IN−). **Bascule U29 juste à côté de U28** (PRE̅ ≈ 10 mm), U33 sous le MCU au plus près de U32 (PRE̅ ≈ 15 mm) : PRE̅ est le net dont un parasite forcerait le calibre HI.
- **2N7002 Q4 / Q6 sous le MCU** : la liaison 2N7002 → grille de l'AO3401A est longue (≈ 36 / 29 mm en Manhattan) mais peu sensible (grille chargée par Ciss ≈ 650 pF : un couplage de 2 pF depuis un front de 3.3 V ne fait que ≈ 10 mV).
- **Amplis INA190** (U30, U31, U34, U35) en rangée sous le MCU près des entrées ADC, au pas de 4 mm (canaux de 1 mm pour les paires Kelvin), tournés de 180° pour que leur 100 nF de VS soit au-dessus ; **tampon de REF U36 juste à côté** (ISENSE_REF 3–15 mm au lieu de ≈ 50 mm). Condensateurs de 1 nF de PF0 / PF1 contre les broches.
- Lignes Kelvin des INA190 : 21–33 mm, à router en **paires serrées, de préférence en B.Cu** (pas de chemin en F.Cu qui évite les translateurs SWD U16 / U17). **Écart accepté** à la contrainte 3 de TASK-010 (« plan GND continu dessous ») : en B.Cu, la référence est le plan d'alimentation In2, découplé ; le nœud µA (sortie du rail vers IN− de l'INA190 LO, 12–17 mm) et les paires Kelvin restent en paires serrées, et l'INA190 rejette le mode commun (CMRR ≥ 132 dB). À tenter d'abord en F.Cu au routage.
- ESD des rails U27 sous l'étiquette de J4, à gauche de la broche 1 (liaisons 8–14 mm en Manhattan, à router en B.Cu depuis les pastilles traversantes).
- R60 (1 MΩ de SWDIO_B) ancré près des résistances série de J_DBG (l'autoplace l'avait poussé dans le front-end du comparateur) ; zone libre réservée entre les deux chaînes (x 20–23, y 38.9–41.8) pour le routage de `*_PRE` / Kelvin ; bas du keepout du couloir USB ramené à y = 28.6 (couloir de 3.3 mm).
- **Face arrière, sans assemblage** : tous les points de test (TP1–TP12, étiquetés par leur net), les ponts de repli JP2 / JP3 (sous les 100 Ω) et les condensateurs non montés C58 / C65. Rien n'est monté par JLC en face arrière : pas de surcoût d'assemblage double face.
- `autoplace.py` ignore les pièces de la face arrière (sans trou métallisé) comme obstacles ; marge autour des résistances ramenée de 0.8 à 0.4 mm (leurs références sont sur le plan de montage).
- Classe de nets Power : les nets de puissance des rails double calibre sont listés explicitement (`*_PRE`, `*_MID`, sortie) ; les nets locaux (seuil, entrée du comparateur, grille) restent en Default.
- Correction de `build_pcb.py` : l'empreinte est ajoutée à la carte avant `Flip()` (plantage sinon) ; les pièces DNP sont exclues de la BOM et du fichier de position (parité avec le schéma).

### Sérigraphie
- Chaque pièce clé (CI, connecteur, D, Q, F, L, SW, TP, JP) a sa référence. Quand la face avant n'a plus de place, la référence est imprimée **en face arrière, à l'aplomb de la pièce** (même position vue à travers la carte, donc sans ambiguïté avec un voisin) : U1, U4, U6, U16, U17, U19, U20, U22, U25–U28, U30, U31, U33–U36, Q2–Q5, D3–D5 (25 pièces). Plans de montage : `out/renders/pcb_placement_assembly_top.pdf` et `out/renders/pcb_placement_assembly_bottom.pdf`.
- 164 références de passifs sur le plan de montage seulement (décision D4).

### Décisions de l'utilisateur (checkpoint TASK-012, 2026-10-20)
- Face arrière non assemblée (points de test, ponts JP2 / JP3, C58 / C65 non montés, références sous les pièces) : **acceptée**.
- Paires Kelvin et nœud µA des INA190 : routage d'abord en F.Cu, **B.Cu accepté** à défaut.
- Go pour merger la pile (TASK-005 à 007, 010 à 012) dans `devape`.

### Revue indépendante du placement (2026-10-20)
5 points majeurs (aucun bloquant) appliqués : chaîne rapide raccourcie (PRE̅), rangée d'amplis élargie, R60 réancré, ESD des rails rapprochée de J4, référence des INA190 à côté des amplis ; mineurs : condensateurs ADC, points de test hors du corps du MCU, C65 écarté de la référence de D5, R17 hors de la zone entre les chaînes. Contre-revue : prêt pour le routage ; corrections suivantes appliquées : diviseur de REF (R106 / R107 / C72) contre U36, résistances série de OUT1–4 et SPI (R69–R72, R75, R76) ramenées entre U14 / U15 et J8. Restent acceptés : tirages statiques R49 / R56 / R57 / R103 à 9–19 mm de leur CI (signaux lents, effet sur la longueur de ratsnest seulement) ; liaisons PRE̅ de 3V3_SW à router à y ≥ 30 (couloir USB à 1.3 mm).

### Résultats
- DRC `--schematic-parity` : **0 erreur, 0 écart de parité**, 2 warnings `silk_edge_clearance` sur J1 (justifiés plus haut). 499 connexions non routées : attendu avant le routage.
- Découplage : **59 / 59** dans leur limite.
- Ratsnest des signaux : 3029 mm sur 145 nets (2469 mm sur 117 nets avant TASK-010 : +45 composants, +28 nets). Les plus longs restent les rails (5V_DUT, 3V3_DUT vers le mux VIO et la relecture ADC) et les nets `*_MID` / `*_PRE` qui rejoignent les amplis sous le MCU (lignes Kelvin, à router en paires).

## Rapports ERC / DRC justifiés

### TASK-002 — projet vide
- **ERC** : 0 violation.
- **DRC** : 1 erreur `invalid_outline` (« Board has malformed outline (no edges found on Edge.Cuts layer) »). Attendue : le contour de carte n'est dessiné qu'en Phase 3. Ne bloque pas les phases 0 à 2.

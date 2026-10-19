"""Generate the preliminary BOM (bom/bom_draft.csv) and print a cost summary.

Data was researched on 2026-10-19 (LCSC product pages and JLCPCB part API).
References are functional groups; final designators are assigned in the schematic (Phase 2).

Usage: python scripts/bom_draft.py
"""

import csv
from collections import namedtuple

from kicad_env import PROJECT_DIR

BOM_FILE = PROJECT_DIR / "bom" / "bom_draft.csv"

# Parts fitted by hand, not placed by JLCPCB (no loading fee).
NOT_ASSEMBLED = {"C5248081"}

Part = namedtuple(
    "Part",
    "ref value qty mpn manufacturer package footprint lcsc jlc_type unit_usd stock datasheet notes",
)

LCSC = "https://www.lcsc.com/product-detail/{}.html"

# Shared passives (JLC Basic unless stated otherwise).
R_0402 = ("UNI-ROYAL", "0402", "Resistor_SMD:R_0402_1005Metric")
C_0402 = "Capacitor_SMD:C_0402_1005Metric"
C_0603 = "Capacitor_SMD:C_0603_1608Metric"
C_0805 = "Capacitor_SMD:C_0805_2012Metric"

PARTS = [
    # --- Power path -------------------------------------------------------
    Part("J_USB", "USB-C 16P USB2.0", 1, "TYPE-C-31-M-12", "Korean Hroparts", "SMD",
         "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948", "Extended", 0.1733,
         "337745 (LCSC)", "https://www.lcsc.com/datasheet/C165948.pdf", ""),
    Part("R_CC", "5.1k 1%", 2, "0402WGF5101TCE", *R_0402, "C25905", "Basic", 0.0023,
         "1913600 (LCSC)", "", "Rd sink on CC1/CC2, CC voltage read by ADC"),
    Part("U_USB_ESD", "USBLC6-2SC6", 1, "USBLC6-2SC6", "STMicroelectronics", "SOT-23-6",
         "Package_TO_SOT_SMD:SOT-23-6", "C7519", "Extended", 0.1786, "32520 (LCSC)",
         "https://www.lcsc.com/datasheet/C7519.pdf", "ESD on D+/D-"),
    Part("D_VBUS", "SMAJ5.0A", 1, "SMAJ5.0A", "Littelfuse", "SMA", "Diode_SMD:D_SMA",
         "C83329", "Extended", 0.1153, "26760 (LCSC)",
         "https://www.lcsc.com/datasheet/C83329.pdf", "VBUS TVS, VBR 6.4 V, Vc 9.2 V"),
    Part("F_VBUS", "PTC 2.6A/5A 8V", 1, "SMD1812P260TF", "RUILON", "1812",
         "Fuse:Fuse_1812_4532Metric", "C21003", "Extended", 0.1206, "580 (LCSC)",
         "https://www.lcsc.com/datasheet/C21003.pdf",
         "Low stock; fallback Bourns MF-MSMF260-2 C89651 (6 V)"),
    Part("U_BUCK", "TLV62569 2A buck", 1, "TLV62569DBVR", "Texas Instruments", "SOT-23-5",
         "Package_TO_SOT_SMD:SOT-23-5", "C141836", "Extended", 0.0712, "450130 (LCSC)",
         "https://www.ti.com/lit/ds/symlink/tlv62569.pdf", "5V_SYS -> 3V3"),
    Part("L_BUCK", "2.2uH Isat 5A", 1, "FXL0420-2R2-M", "cjiang", "4.4x4.2 mm",
         "Inductor_SMD:L_Changjiang_FXL0420", "C167206", "Extended", 0.2076, "81135 (LCSC)",
         "https://www.lcsc.com/datasheet/C167206.pdf", ""),
    Part("R_BUCK_FB_TOP", "100k 1%", 1, "0402WGF1003TCE", *R_0402, "C25741", "Basic", 0.0015,
         "2505000 (LCSC)", "", "Vout = 0.6 x (1 + 100k/22k) = 3.327 V"),
    Part("R_BUCK_FB_BOT, R_ILIM_5VSW", "22k 1%", 2, "0402WGF2202TCE", *R_0402, "C25768",
         "Basic", 0.0012, "792000 (LCSC)", "", "Buck FB bottom + ILIM 5V_SW (~1.16 A typ)"),
    Part("U_SW", "AP22653 current-limited switch", 4, "AP22653W6-7", "Diodes Incorporated",
         "SOT-26", "Package_TO_SOT_SMD:SOT-23-6", "C2158037", "Extended", 0.2645,
         "13850 (LCSC)", "https://www.diodes.com/assets/Datasheets/AP22652_53_52A_53A.pdf",
         "5V_SW, 5V fixed, 3V3_SW, 3V3 fixed; FAULT, output discharge, reverse blocking"),
    Part("R_ILIM_5V, R_ILIM_3V3SW", "39k 1%", 2, "0402WGF3902TCE", *R_0402, "C25783",
         "Extended", 0.0024, "717600 (LCSC)", "", "ILIM ~636 mA typ"),
    Part("R_ILIM_3V3", "68k 1%", 1, "0402WGF6802TCE", *R_0402, "C36871", "Extended", 0.0020,
         "125791 (JLC)", "", "ILIM ~354 mA typ"),
    Part("D_PWR", "LED yellow-green", 1, "XL-1608SYGC-06", "XINGLIGHT", "0603",
         "LED_SMD:LED_0603_1608Metric", "C965805", "Extended", 0.0066, "743900 (LCSC)",
         "https://www.lcsc.com/datasheet/C965805.pdf", "Power OK, Vf ~2 V"),
    Part("D_HB", "LED red", 1, "KT-0603R", "Hubei KENTO", "0603", "LED_SMD:LED_0603_1608Metric",
         "C2286", "Basic", 0.0077, "6011600 (LCSC)", "", "Heartbeat"),
    Part("R_LED", "1k 1%", 2, "0402WGF1001TCE", *R_0402, "C11702", "Basic", 0.0013,
         "9195500 (LCSC)", "", "~1.3 mA per LED"),

    # --- MCU --------------------------------------------------------------
    Part("U_MCU", "STM32G431RBT6", 1, "STM32G431RBT6", "STMicroelectronics", "LQFP-64",
         "Package_QFP:LQFP-64_10x10mm_P0.5mm", "C431633", "Extended", 5.14, "2666 (JLC)",
         "https://www.st.com/resource/en/datasheet/stm32g431rb.pdf",
         "Crystal-less USB FS (HSI48+CRS); G0B1RET6/F072RBT6 out of stock"),
    Part("J_SWD_HIL", "ARM 10-pin 1.27mm SMD", 1, "DZ127S-22-10-55", "DEALON", "2x5 1.27 mm SMD",
         "Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD", "C5160761",
         "Extended", 0.1235, "9575 (JLC)", "https://www.lcsc.com/datasheet/C5160761.pdf",
         "Unshrouded; standard odd/even numbering"),

    # --- Current sensing, analog, display --------------------------------
    Part("U_INA", "INA226 V/I monitor", 2, "INA226AIDGSR", "Texas Instruments", "VSSOP-10",
         "Package_SO:MSOP-10_3x3mm_P0.5mm", "C49851", "Extended", 0.61, "36418 (JLC)",
         "https://www.ti.com/lit/ds/symlink/ina226.pdf",
         "Validated; INA228 is pin-compatible (drop-in upgrade, firmware change); I2C 0x40/0x41"),
    Part("R_SHUNT_5VSW", "50mR 1% 1W", 1, "SMF12M1FR050T", "SART", "1206",
         "Resistor_SMD:R_1206_3216Metric", "C845298", "Extended", 0.062, "3566 (JLC)",
         "", "Kelvin routing; Vishay WSL1206R0500FEA18 C2073508 as alternative"),
    Part("R_SHUNT_3V3SW", "100mR 1% 1W", 1, "STE1206M1W0R100F", "Walter", "1206",
         "Resistor_SMD:R_1206_3216Metric", "C201308", "Extended", 0.055, "28651 (JLC)",
         "", "Kelvin routing; Vishay WSL1206R1000FEA18 C843879 as alternative"),
    Part("R_I2C_INT", "2.2k 1%", 2, "0402WGF2201TCE", *R_0402, "C25879", "Basic", 0.0012,
         "2528400 (LCSC)", "", "Internal I2C pull-ups (INA + OLED)"),
    Part("U_DAC_BUF", "TLV9001 RRIO op-amp", 1, "TLV9001IDBVR", "Texas Instruments",
         "SOT-23-5", "Package_TO_SOT_SMD:SOT-23-5", "C398363", "Extended", 0.088,
         "52521 (JLC)", "https://www.ti.com/lit/ds/symlink/tlv9001.pdf",
         "Unity follower; DBV pinout 1 OUT 2 V- 3 IN+ 4 IN- 5 V+"),
    Part("DS_OLED", "OLED 0.91in 128x32 SSD1306 I2C", 1, "HS91L02W2C01",
         "Shenzhen Hansheng", "Module 38x12 mm, 4-pin 2.54",
         "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical", "C5248081", "Extended",
         1.94, "3114 (JLC)",
         "https://datasheet.lcsc.com/datasheet/pdf/8953314a04a56b0774ba6ab8fe698503.pdf",
         "Pinout 1 GND 2 VCC 3 SCL 4 SDA; plugged by hand into J_OLED"),
    Part("J_OLED", "Female header 1x4 2.54", 1, "2.54-1*4P", "BOOMELE", "THT",
         "Connector_PinSocket_2.54mm:PinSocket_1x04_P2.54mm_Vertical", "C2718488", "Extended",
         0.0832, "131610 (LCSC)", "", "OLED socket"),

    # --- VIO and level translation ---------------------------------------
    Part("U_VIO_MUX", "TPS2116 power mux", 1, "TPS2116DRLR", "Texas Instruments", "SOT-583-8",
         "Package_TO_SOT_SMD:SOT-583-8", "C3235557", "Extended", 0.3099, "61293 (LCSC)",
         "https://www.ti.com/lit/ds/symlink/tps2116.pdf",
         "VIN1 5V_SYS, VIN2 LDO, shutdown = external VIO"),
    Part("U_VIO_LDO", "AP2127K-ADJ LDO", 1, "AP2127K-ADJTRG1", "Diodes Incorporated",
         "SOT-23-5", "Package_TO_SOT_SMD:SOT-23-5", "C96343", "Extended", 0.1204,
         "27955 (LCSC)", "https://www.diodes.com/assets/Datasheets/AP2127.pdf", "1.8/3.3 V"),
    Part("R_VIO_R1", "30k 1%", 1, "0402WGF3002TCE", *R_0402, "C25776", "Extended", 0.0016,
         "1531611 (JLC)", "", "LDO top resistor"),
    Part("R_VIO_R2", "24k 1%", 1, "0402WGF2402TCE", *R_0402, "C25769", "Extended", 0.0012,
         "364590 (JLC)", "", "LDO bottom -> 1.800 V"),
    Part("R_VIO_R2B", "16k 1%", 1, "0402WGF1602TCE", *R_0402, "C25759", "Extended", 0.0127,
         "223924 (JLC)", "", "Switched in parallel -> 3.300 V"),
    Part("C_VIO_FF", "1nF X7R 50V", 1, "0402B102K500NT", "FH", "0402", C_0402, "C1523",
         "Basic", 0.0038, "2822982 (JLC)", "", "LDO feed-forward"),
    Part("Q_VSEL, Q_RESET, Q_BOOT", "2N7002", 3, "2N7002", "CJ", "SOT-23",
         "Package_TO_SOT_SMD:SOT-23", "C8545", "Basic", 0.0175, "2544313 (JLC)",
         "https://www.lcsc.com/datasheet/C8545.pdf", "VIO select + open-drain RESET/BOOT"),
    Part("U_LS_OUT, U_LS_IN", "SN74LVC8T245", 2, "SN74LVC8T245PWR", "Texas Instruments",
         "TSSOP-24", "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm", "C27643", "Extended", 0.3395,
         "38675 (LCSC)", "https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf",
         "One output-only (DIR=VCCA), one input-only (DIR=GND)"),
    Part("U_LS_SWCLK, U_LS_SWDIO", "SN74LVC1T45", 2, "SN74LVC1T45DBVR", "Texas Instruments",
         "SOT-23-6", "Package_TO_SOT_SMD:SOT-23-6", "C7843", "Extended", 0.0842,
         "333175 (LCSC)", "https://www.ti.com/lit/ds/symlink/sn74lvc1t45.pdf",
         "DIR driven by MCU"),
    Part("U_I2C_DUT", "TCA9517A I2C buffer", 1, "TCA9517ADGKR", "Texas Instruments",
         "VSSOP-8", "Package_SO:VSSOP-8_3x3mm_P0.65mm", "C201698", "Extended", 0.3821,
         "17253 (JLC)", "https://www.ti.com/lit/ds/symlink/tca9517a.pdf",
         "A side = DUT (VIO), B side = MCU (3V3); replaces PCA9306"),
    Part("U_ESD", "TPD4E05U06 4-ch ESD", 8, "TPD4E05U06DQAR", "Texas Instruments", "USON-10",
         "Package_SON:USON-10_2.5x1.0mm_P0.5mm", "C138714", "Extended", 0.0837,
         "212835 (LCSC)", "https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf",
         "7 for ~26 signals + 1 for header power pins"),
    Part("R_SER", "100R 1%", 20, "0402WGF1000TCE", *R_0402, "C25076", "Basic", 0.0013,
         "3162300 (LCSC)", "", "Series R on exposed signals + DAC output"),
    Part("R_PU_TCA", "4.7k 1%", 4, "0402WGF4701TCE", *R_0402, "C25900", "Basic", 0.0021,
         "8743200 (LCSC)", "", "TCA9517A pull-ups, both sides"),

    # --- DUT headers ------------------------------------------------------
    Part("J_PWR, J_DBG, J_BUS, J_UART_ANA", "Pin header 1x7 2.54", 4, "PZ254V-11-07P", "XFCN", "THT",
         "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical", "C492406", "Extended",
         0.0441, "51740 (LCSC)", "", "THT, soldered by JLC"),
    Part("J_IO", "Pin header 1x10 2.54", 1, "PZ254V-11-10P", "XFCN", "THT",
         "Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical", "C492409", "Extended",
         0.0582, "44180 (LCSC)", "", "JLC type to confirm"),

    # --- Shared passives --------------------------------------------------
    Part("C_100N", "100nF X7R 50V", 31, "CL05B104KB54PNC", "Samsung", "0402", C_0402,
         "C307331", "Basic", 0.0095, "3067200 (LCSC)", "",
         "Decoupling: MCU 7, buck 1, switches 8, VBUS 1, INA 2, op-amp 1, shifters 8, TCA 2, USB ESD 1"),
    Part("C_10N", "10nF X7R 50V", 4, "CL05B103KB5NNNC", "Samsung", "0402", C_0402, "C15195",
         "Basic", 0.0041, "5993469 (JLC)", "", "VDDA, AIN filters x2, VIO_MON filter"),
    Part("C_1U", "1uF X5R 25V", 6, "CL05A105KA5NQNC", "Samsung", "0402", C_0402, "C52923",
         "Basic", 0.0068, "8329458 (JLC)", "", "VDDA, VREF+, TPS2116 VIN x2, LDO in/out"),
    Part("C_4U7", "4.7uF X5R 16V", 1, "CL10A475KO8NNNC", "Samsung", "0603", C_0603, "C19666",
         "Basic", 0.022, "649370 (LCSC)", "", "MCU VDD bulk"),
    Part("C_10U_10V", "10uF X5R 10V", 4, "CL10A106KP8NNNC", "Samsung", "0603", C_0603,
         "C19702", "Basic", 0.0273, "6358860 (LCSC)", "", "Buck Cin, 3V3 switch outputs x2, VIO"),
    Part("C_10U_25V", "10uF X5R 25V", 3, "CL21A106KAYNNNE", "Samsung", "0805", C_0805,
         "C15850", "Basic", 0.0882, "3110200 (LCSC)", "", "VBUS bulk, 5V switch outputs x2"),
    Part("C_22U", "22uF X5R 25V", 2, "CL21A226MAQNNNE", "Samsung", "0805", C_0805, "C45783",
         "Basic", 0.1959, "229400 (LCSC)", "", "Buck Cout"),
    Part("R_10K", "10k 1%", 8, "0402WGF1002TCE", *R_0402, "C25744", "Basic", 0.0015,
         "19469071 (JLC)", "", "BOOT0 pull-down, TPS2116 PR1 pull-up, LS /OE pull-up, FAULT x4 + INA ALERT pull-ups"),
    Part("R_100K", "100k 1%", 14, "0402WGF1003TCE", *R_0402, "C25741", "Basic", 0.0015,
         "2505000 (LCSC)", "",
         "EN pull-downs x2, AIN dividers x4, VIO_MON x2, MODE/VSEL/RESET/BOOT/SWCLK-DIR/SWDIO-DIR pull-downs x6"),
]


def main():
    BOM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with BOM_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Ref", "Value", "Qty", "MPN", "Manufacturer", "Package",
                         "Footprint", "LCSC", "JLC_Type", "Unit_USD", "Stock",
                         "Datasheet", "Source", "Notes"])
        for p in PARTS:
            writer.writerow([p.ref, p.value, p.qty, p.mpn, p.manufacturer, p.package,
                             p.footprint, p.lcsc, p.jlc_type, f"{p.unit_usd:.4f}", p.stock,
                             p.datasheet, LCSC.format(p.lcsc), p.notes])

    total = sum(p.qty * p.unit_usd for p in PARTS)
    extended = sorted({p.lcsc for p in PARTS
                       if p.jlc_type == "Extended" and p.lcsc not in NOT_ASSEMBLED})
    placements = sum(p.qty for p in PARTS)
    print(f"{len(PARTS)} lines, {placements} parts -> {BOM_FILE.relative_to(PROJECT_DIR)}")
    print(f"Components per board: {total:.2f} USD")
    print(f"Unique Extended parts: {len(extended)} -> loading fee {len(extended) * 3.07:.2f} USD per order")


if __name__ == "__main__":
    main()

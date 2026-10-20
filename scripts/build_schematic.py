"""Generate the OOTY hierarchical schematic from the design description below.

Every connection is declared as pin -> net. Part data (footprint, MPN, LCSC, datasheet) comes
from scripts/bom_draft.py through the LCSC code, so the BOM stays the single source of truth.

Usage: python scripts/build_schematic.py
"""

import datetime

import bom_draft
import schgen
from schgen import Sheet

REV = "A"
TITLE = "OOTY - USB Hardware-in-the-Loop board"

BOM = {p.lcsc: p for p in bom_draft.PARTS}

# LCSC codes of the parts used below.
R100 = "C25076"
R1K = "C11702"
R2K2 = "C25879"
R4K7 = "C25900"
R5K1 = "C25905"
R10K = "C25744"
R22K = "C25768"
R30K = "C25776"
R24K = "C25769"
R16K = "C25759"
R39K = "C25783"
R68K = "C36871"
R100K = "C25741"
R1M = "C26083"
C1N = "C1523"
C10N = "C15195"
C100N = "C307331"
C1U = "C52923"
C4U7 = "C19666"
C10U = "C19702"
C10U25 = "C15850"
C22U = "C45783"

TP_FOOTPRINT = "TestPoint:TestPoint_Pad_D1.5mm"
JUMPER_FOOTPRINT = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
LCSC_PAGE = "https://www.lcsc.com/product-detail/{}.html"
HOLE_FOOTPRINT = "MountingHole:MountingHole_3.2mm_M3"


def bom_fields(part):
    lcsc = part.fields.get("LCSC")
    if not lcsc:
        return {}
    p = BOM[lcsc]
    return {"Footprint": p.footprint, "Datasheet": p.datasheet or LCSC_PAGE.format(lcsc),
            "MPN": p.mpn,
            "Manufacturer": p.manufacturer}


def value_of(lcsc):
    """Short value for the schematic: '100nF X7R 50V' -> '100nF/50V', '10k 1%' -> '10k'."""
    tokens = BOM[lcsc].value.split()
    volts = [t for t in tokens[1:] if t.endswith("V")]
    return tokens[0] + (f"/{volts[0]}" if volts else "")


# --- Small helpers -------------------------------------------------------------


def res(sh, lcsc, a, b, value=None):
    return sh.add("R", "Device:R", value or value_of(lcsc), {"1": a, "2": b}, rot=90,
                  fields={"LCSC": lcsc})


def cap(sh, lcsc, a, b="GND", near=None):
    """Capacitor between nets a and b. `near` = (part, pin name or number) it decouples: used by
    the placer and by scripts/check_placement.py."""
    c = sh.add("C", "Device:C", value_of(lcsc), {"1": a, "2": b}, rot=90,
               fields={"LCSC": lcsc})
    c.near = near
    return c


def pwr_flag(sh, net):
    return sh.add("#FLG", "power:PWR_FLAG", "PWR_FLAG", {"1": net}, in_bom=False)


def test_point(sh, net):
    return sh.add("TP", "Connector:TestPoint", net, {"1": net}, in_bom=False,
                  fields={"Footprint": TP_FOOTPRINT}, hide_value=True)


def part(sh, ref, lib_id, lcsc, nets, value=None, rot=0):
    return sh.add(ref, lib_id, value or BOM[lcsc].mpn, nets, rot=rot, fields={"LCSC": lcsc})


# --- Sheets ----------------------------------------------------------------------


def power_sheet():
    sh = Sheet("power", "Power: USB-C, 3V3 buck, DUT rails")

    sh.group("USB-C input")
    part(sh, "J", "Connector:USB_C_Receptacle_USB2.0_16P", "C165948", {
        "VBUS": "VBUS", "GND": "GND", "SHIELD": "GND", "CC1": "CC1", "CC2": "CC2",
        "D+": "USB_DP", "D-": "USB_DM", "SBU1": None, "SBU2": None})
    res(sh, R5K1, "CC1", "GND")
    res(sh, R5K1, "CC2", "GND")
    part(sh, "U", "Power_Protection:TPD4E05U06DQA", "C138714", {
        "D1+": "CC1", "D1-": "CC2", "D2+": None, "D2-": None, "GND": "GND", "NC": None})
    esd_usb = part(sh, "U", "Power_Protection:USBLC6-2SC6", "C7519", {
        "I/O1": "USB_DP", "I/O2": "USB_DM", "VBUS": "VBUS", "GND": "GND"})
    cap(sh, C100N, "VBUS", near=(esd_usb, "VBUS"))

    sh.group("VBUS protection")
    ptc = part(sh, "F", "Device:Polyfuse", "C21003", {"1": "VBUS", "2": "+5V"},
               value="PTC 2.6A", rot=90)
    # TVS after the PTC: a sustained overvoltage trips the PTC instead of cooking the TVS.
    part(sh, "D", "Device:D_Zener", "C83329", {"1": "+5V", "2": "GND"})
    cap(sh, C100N, "+5V", near=(ptc, "2"))
    pwr_flag(sh, "VBUS")
    pwr_flag(sh, "+5V")
    pwr_flag(sh, "GND")

    sh.group("Rail test points")
    for net in ("VBUS", "+5V", "+3V3", "GND"):
        test_point(sh, net)

    sh.group("3V3 buck (TLV62569)", column_break=True)
    buck = part(sh, "U", "Regulator_Switching:TLV62569DBV", "C141836", {
        "VIN": "+5V", "EN": "+5V", "GND": "GND", "SW": "SW_3V3", "FB": "FB_3V3"})
    cap(sh, C10U25, "+5V", near=(buck, "VIN"))
    cap(sh, C100N, "+5V", near=(buck, "VIN"))
    ind = part(sh, "L", "Device:L", "C167206", {"1": "SW_3V3", "2": "+3V3"}, value="2.2uH",
               rot=90)
    res(sh, R100K, "+3V3", "FB_3V3")
    sh.add("C", "Device:C", "6.8pF DNP", {"1": "+3V3", "2": "FB_3V3"}, rot=90, in_bom=False,
           dnp=True, fields={"Footprint": "Capacitor_SMD:C_0402_1005Metric"})
    res(sh, R22K, "FB_3V3", "GND")
    cout = cap(sh, C22U, "+3V3", near=(ind, "2"))
    cap(sh, C22U, "+3V3", near=(cout, "1"))
    pwr_flag(sh, "+3V3")

    sh.group("Power OK LED")
    res(sh, R1K, "+3V3", "LED_PWR_A")
    part(sh, "D", "Device:LED", "C965805", {"A": "LED_PWR_A", "K": "GND"}, value="PWR", rot=180)

    # Switched rails start off (EN pulled down). Fixed rails start on (EN pulled up to IN), but the
    # firmware can still cut them (USB power budget, persistent fault).
    switches = [
        ("5V_SW (switched, 1 A)", "+5V", "EN_5VSW", "5V_SW_PRE", "FAULT_5VSW", R22K, C10U25, "GND"),
        ("5V fixed (0.5 A)", "+5V", "EN_5V", "5V_DUT", "FAULT_5V", R39K, C10U25, "+5V"),
        ("3V3_SW (switched, 0.5 A)", "+3V3", "EN_3V3SW", "3V3_SW_PRE", "FAULT_3V3SW", R39K, C10U,
         "GND"),
        ("3V3 fixed (0.3 A)", "+3V3", "EN_3V3", "3V3_DUT", "FAULT_3V3", R68K, C10U, "+3V3"),
    ]
    for i, (title, vin, en, vout, fault, rlim, cbulk, en_bias) in enumerate(switches):
        sh.group(f"Switch {title}", column_break=(i % 2 == 0))
        ilim = f"ILIM_{fault[6:]}"
        sw = part(sh, "U", "OOTY:AP22653W6", "C2158037", {
            "IN": vin, "EN": en, "OUT": vout, "~{FAULT}": fault, "GND": "GND", "ILIM": ilim})
        res(sh, rlim, ilim, "GND")
        cap(sh, C100N, vin, near=(sw, "IN"))
        cap(sh, C100N, vout, near=(sw, "OUT"))
        cap(sh, cbulk, vout, near=(sw, "OUT"))
        res(sh, R10K, fault, "+3V3")
        res(sh, R100K, en, en_bias)

    sh.note("AP22653 ILIM (DS41186 p.10, VIN = 5 V): 22k -> 1.16 A typ, 39k -> 0.64 A typ, "
            "68k -> 0.35 A typ. See NOTES.md.")
    sh.note("Buck: Vout = 0.6 V x (1 + 100k/22k) = 3.327 V.")
    return sh


MCU_PINS = {
    "VBAT": "+3V3", "VDD": "+3V3", "VDDA": "+3V3", "VREF+": "+3V3",
    "VSS": "GND", "VSSA": "GND",
    "PG10": "NRST", "PB8": "BOOT0",
    "PA11": "USB_DM", "PA12": "USB_DP",
    "PA13": "SWDIO_HIL", "PA14": "SWCLK_HIL", "PB3": "SWO_HIL",
    # Rail control and status
    "PC13": "EN_5VSW", "PC14": "EN_3V3SW",
    "PC15": "FAULT_5VSW", "PF0": "FAULT_3V3SW", "PF1": "FAULT_5V", "PB5": "FAULT_3V3",
    "PB9": "INA_ALERT",
    # Internal I2C1 (current monitors + OLED)
    "PA15": "I2C_INT_SCL", "PB7": "I2C_INT_SDA",
    # Analog
    "PA4": "DAC_OUT", "PC0": "AIN1_ADC", "PC1": "AIN2_ADC", "PC2": "CC1", "PC3": "CC2",
    "PB1": "VIO_MON",
    # VIO selection and translators
    "PC4": "VIO_PR1", "PC5": "VIO_MODE", "PB14": "VIO_VSEL", "PA9": "LS_OE_N",
    "PB6": "I2C_DUT_EN",
    # DUT digital I/O
    "PA0": "OUT1_MCU", "PA1": "OUT2_MCU", "PA2": "OUT3_MCU", "PB0": "OUT4_MCU",
    "PC10": "IN1_MCU", "PC11": "IN2_MCU", "PC12": "IN3_MCU", "PD2": "IN4_MCU",
    # DUT UART (USART3), SPI (SPI1), I2C (I2C3)
    "PB10": "UART_TX_MCU", "PB11": "UART_RX_MCU",
    "PA5": "SPI_SCK_MCU", "PA6": "SPI_MISO_MCU", "PA7": "SPI_MOSI_MCU", "PA8": "SPI_CS_MCU",
    "PC8": "I2C_DUT_SCL_MCU", "PC9": "I2C_DUT_SDA_MCU",
    # DUT SWD probe (SWO captured by USART2_RX)
    "PB13": "SWCLK_MCU", "PB15": "SWDIO_MCU", "PB2": "SWCLK_DIR", "PB12": "SWDIO_DIR",
    "PA3": "SWO_DUT_MCU",
    # DUT RESET / BOOT open-drain drivers
    "PC6": "RESET_DUT_CTL", "PC7": "BOOT_DUT_CTL",
    "PA10": None,
    # BOOT_DIR is not on PB4: PB4 is NJTRST with a 25-55k pull-up after reset (DS12589 Table 12,
    # note 4), which beat the 100k pull-down and drove the DUT BOOT pin during HIL resets.
    "PD10": "BOOT_DIR", "PB4": None,
    # Fixed DUT rails enable (pulled up: on by default)
    "PD8": "EN_5V", "PD9": "EN_3V3",
    # User buttons (active low) and heartbeat LED: pins on the side facing the top-right corner
    "PE11": "BTN1", "PE10": "BTN2", "PE12": "LED_HB",
    # Spare LQFP-80 GPIO
    "PE7": None, "PE8": None, "PE9": None, "PE13": None, "PE14": None, "PE15": None,
    "PD0": None, "PD1": None,
}

# VDD pins of the LQFP-80 (DS12589 Figure 11): one 100 nF each.
MCU_VDD_PINS = ("16", "41", "51", "62", "80")


def mcu_sheet():
    sh = Sheet("mcu", "MCU STM32G431MBT6")

    sh.group("STM32G431MBT6")
    mcu = part(sh, "U", "MCU_ST_STM32G4:STM32G431MBTx", "C730099", MCU_PINS)

    sh.group("Decoupling (DS12589 5.1.6)", column_break=True)
    for pin in MCU_VDD_PINS:
        cap(sh, C100N, "+3V3", near=(mcu, pin))
    cap(sh, C4U7, "+3V3", near=(mcu, "51"))
    cap(sh, C100N, "+3V3", near=(mcu, "VBAT"))
    cap(sh, C10N, "+3V3", near=(mcu, "VDDA"))
    cap(sh, C1U, "+3V3", near=(mcu, "VDDA"))
    cap(sh, C100N, "+3V3", near=(mcu, "VREF+"))
    cap(sh, C1U, "+3V3", near=(mcu, "VREF+"))
    cap(sh, C100N, "NRST", near=(mcu, "PG10"))

    sh.group("Boot / HIL debug (SWD)")
    res(sh, R10K, "BOOT0", "GND")
    sh.add("JP", "Jumper:SolderJumper_2_Open", "BOOT0", {"1": "BOOT0", "2": "+3V3"},
           in_bom=False, fields={"Footprint": JUMPER_FOOTPRINT})
    sh.add("J", "Connector:Conn_ARM_JTAG_SWD_10", "SWD_HIL", {
        "VTref": "+3V3", "SWDIO/TMS": "SWDIO_HIL", "SWCLK/TCK": "SWCLK_HIL",
        "SWO/TDO": "SWO_HIL", "~{RESET}": "NRST", "GND": "GND", "GNDDetect": "GND",
        "KEY": None, "NC/TDI": None}, fields={"LCSC": "C5160761"})

    sh.group("Heartbeat LED")
    res(sh, R1K, "LED_HB", "LED_HB_A")
    part(sh, "D", "Device:LED", "C2286", {"A": "LED_HB_A", "K": "GND"}, value="HB", rot=180)

    sh.group("User buttons")
    for n in ("1", "2"):
        sh.add("SW", "Switch:SW_Push", f"BTN{n}", {"1": f"BTN{n}", "2": "GND"},
               fields={"LCSC": "C318884"})
        res(sh, R10K, f"BTN{n}", "+3V3")
        cap(sh, C100N, f"BTN{n}")

    sh.note("USB FS runs crystal-less (HSI48 + CRS). BOOT0 solder jumper: bridge it to force the "
            "system bootloader.")
    sh.note("PB6 may carry a UCPD dead-battery pull-down at reset (PA9 = DBCC1 is pulled high); "
            "I2C_DUT_EN has an external pull-down anyway. Firmware sets PWR_CR3.UCPD1_DBDIS first.")
    sh.note("Pin choice follows the PCB floor plan (MCU rotated 180 deg): see NOTES.md.")
    return sh


def sensing_sheet():
    sh = Sheet("sensing", "Current sensing, OLED, analog I/O")

    monitors = [("5V_SW", "5V_SW_PRE", "GND", "C845298"), ("3V3_SW", "3V3_SW_PRE", "+3V3", "C201308")]
    for rail, pre, a0, shunt in monitors:
        sh.group(f"Current monitor {rail}")
        part(sh, "R", "Device:R", shunt, {"1": pre, "2": rail}, value=BOM[shunt].value, rot=90)
        ina = part(sh, "U", "Sensor_Energy:INA226", "C49851", {
            # Vbus upstream of the shunt: its ~1 MOhm input would otherwise add ~5 uA through it.
            "Vin+": pre, "Vin-": rail, "Vbus": pre, "VS": "+3V3", "GND": "GND",
            "A1": "GND", "A0": a0, "SDA": "I2C_INT_SDA", "SCL": "I2C_INT_SCL",
            "~{Alert}": "INA_ALERT"})
        cap(sh, C100N, "+3V3", near=(ina, "VS"))

    sh.group("Internal I2C + OLED", column_break=True)
    res(sh, R2K2, "I2C_INT_SDA", "+3V3")
    res(sh, R2K2, "I2C_INT_SCL", "+3V3")
    res(sh, R10K, "INA_ALERT", "+3V3")
    sh.add("J", "Connector_Generic:Conn_01x04", "OLED 0.91in", {
        "1": "GND", "2": "+3V3", "3": "I2C_INT_SCL", "4": "I2C_INT_SDA"},
        fields={"LCSC": "C2718488"})

    sh.group("Analog inputs (0-5.5 V)")
    for n in ("1", "2"):
        res(sh, R100K, f"AIN{n}", f"AIN{n}_ADC")
        res(sh, R100K, f"AIN{n}_ADC", "GND")
        cap(sh, C10N, f"AIN{n}_ADC")

    sh.group("VIO monitor")
    res(sh, R100K, "VIO", "VIO_MON")
    res(sh, R100K, "VIO_MON", "GND")
    cap(sh, C10N, "VIO_MON")

    sh.group("DAC output buffer", column_break=True)
    buf = part(sh, "U", "OOTY:TLV9001IDBV", "C398363", {
        "+": "DAC_OUT", "-": "AOUT_BUF", "1": "AOUT_BUF", "V+": "+3V3", "V-": "GND"})
    cap(sh, C100N, "+3V3", near=(buf, "V+"))
    res(sh, R100, "AOUT_BUF", "AOUT")

    sh.note("INA226 addresses: 5V_SW 0x40 (A1=A0=GND), 3V3_SW 0x41 (A0=VS). OLED 0x3C. "
            "INA228 is a drop-in replacement (same pinout).")
    sh.note("Shunts: Kelvin connection to IN+/IN- required at layout.")
    return sh


def vio_sheet():
    sh = Sheet("vio", "VIO: 1.8 / 3.3 / 5 V or external")

    sh.group("VIO selection (TPS2116 mux)")
    # VIN1 from the current-limited fixed 5 V rail: a short on VIO in 5 V mode trips that limiter
    # instead of collapsing +5V (and the HIL 3V3 behind it).
    mux = part(sh, "U", "Power_Management:TPS2116DRL", "C3235557", {
        "VIN1": "5V_DUT", "VIN2": "VIO_LDO", "VOUT": "VIO", "PR1": "VIO_PR1", "MODE": "VIO_MODE",
        "ST": None, "GND": "GND"})
    cap(sh, C1U, "5V_DUT", near=(mux, "VIN1"))
    cap(sh, C1U, "VIO_LDO", near=(mux, "VIN2"))
    cap(sh, C1U, "VIO", near=(mux, "2"))
    # PR1 pulled up from +5V (not +3V3): MODE=0/PR1=0 would select 5 V while 3V3 ramps up.
    res(sh, R10K, "+5V", "VIO_PR1")
    res(sh, R22K, "VIO_PR1", "GND")
    res(sh, R100K, "VIO_MODE", "GND")

    sh.group("VIO LDO 1.8 / 3.3 V (AP2127K-ADJ)")
    ldo = part(sh, "U", "Regulator_Linear:AP2127K-ADJ", "C96343", {
        "VIN": "+5V", "EN": "+5V", "GND": "GND", "ADJ": "VIO_ADJ", "VOUT": "VIO_LDO"})
    cap(sh, C1U, "+5V", near=(ldo, "VIN"))
    cap(sh, C1U, "VIO_LDO", near=(ldo, "VOUT"))
    res(sh, R30K, "VIO_LDO", "VIO_ADJ")
    sh.add("C", "Device:C", value_of(C1N), {"1": "VIO_LDO", "2": "VIO_ADJ"}, rot=90,
           fields={"LCSC": C1N})
    res(sh, R24K, "VIO_ADJ", "GND")
    res(sh, R16K, "VIO_ADJ", "VSEL_D")
    part(sh, "Q", "Transistor_FET:2N7002", "C8545", {"G": "VIO_VSEL", "S": "GND", "D": "VSEL_D"})
    res(sh, R100K, "VIO_VSEL", "GND")

    sh.note("TPS2116: MODE=1 PR1=1 -> 5V_DUT ; MODE=1 PR1=0 -> LDO ; MODE=0 PR1=1 -> off "
            "(external VIO from J_PWR/J_DBG). MODE=0 PR1=0 is forbidden (selects 5 V).")
    sh.note("LDO: Vout = 0.8 x (1 + 30k/24k) = 1.80 V ; VIO_VSEL high adds 16k in parallel -> 3.30 V.")
    return sh


def translators_sheet():
    sh = Sheet("translators", "Level translators 3V3 <-> VIO")

    sh.group("Outputs 3V3 -> VIO (DIR = A to B)")
    outs = ["OUT1", "OUT2", "OUT3", "OUT4", "UART_TX", "SPI_SCK", "SPI_MOSI", "SPI_CS"]
    nets = {"V_{CCA}": "+3V3", "V_{CCB}": "VIO", "GND": "GND", "DIR": "+3V3", "~{OE}": "LS_OE_N"}
    for i, name in enumerate(outs, 1):
        nets[f"A{i}"] = f"{name}_MCU"
        nets[f"B{i}"] = f"{name}_B"
    ls = part(sh, "U", "Logic_LevelTranslator:SN74LVC8T245", "C27643", nets)
    cap(sh, C100N, "+3V3", near=(ls, "1"))
    cap(sh, C100N, "VIO", near=(ls, "23"))
    res(sh, R10K, "LS_OE_N", "+3V3")

    sh.group("Inputs VIO -> 3V3 (DIR = B to A)", column_break=True)
    ins = ["IN1", "IN2", "IN3", "IN4", "UART_RX", "SPI_MISO", "SWO_DUT"]
    # Unused channel 8: B8 and A8 tied low (no floating CMOS input while /OE is high, and no
    # conflict once enabled: A8 then drives the B8 level, i.e. low).
    nets = {"V_{CCA}": "+3V3", "V_{CCB}": "VIO", "GND": "GND", "DIR": "GND", "~{OE}": "LS_OE_N",
            "A8": "GND", "B8": "GND"}
    for i, name in enumerate(ins, 1):
        nets[f"A{i}"] = f"{name}_MCU"
        nets[f"B{i}"] = f"{name}_B"
    ls = part(sh, "U", "Logic_LevelTranslator:SN74LVC8T245", "C27643", nets)
    cap(sh, C100N, "+3V3", near=(ls, "1"))
    cap(sh, C100N, "VIO", near=(ls, "23"))

    sh.group("SWD probe")
    for sig in ("SWCLK", "SWDIO"):
        ls = part(sh, "U", "Logic_LevelTranslator:SN74LVC1T45DBV", "C7843", {
            "VCCA": "+3V3", "VCCB": "VIO", "GND": "GND", "A": f"{sig}_MCU", "B": f"{sig}_B",
            "DIR": f"{sig}_DIR"})
        cap(sh, C100N, "+3V3", near=(ls, "VCCA"))
        cap(sh, C100N, "VIO", near=(ls, "VCCB"))
        res(sh, R100K, f"{sig}_DIR", "GND")

    sh.group("DUT I2C (A = DUT)")
    tca = part(sh, "U", "Logic_LevelTranslator:TCA9517ADGK", "C201698", {
        "VCCA": "VIO", "SCLA": "I2C_SCL", "SDAA": "I2C_SDA", "GND": "GND", "EN": "I2C_DUT_EN",
        "SDAB": "I2C_DUT_SDA_MCU", "SCLB": "I2C_DUT_SCL_MCU", "VCCB": "+3V3"})
    cap(sh, C100N, "VIO", near=(tca, "VCCA"))
    cap(sh, C100N, "+3V3", near=(tca, "VCCB"))
    res(sh, R4K7, "I2C_SCL", "VIO")
    res(sh, R4K7, "I2C_SDA", "VIO")
    res(sh, R4K7, "I2C_DUT_SCL_MCU", "+3V3")
    res(sh, R4K7, "I2C_DUT_SDA_MCU", "+3V3")
    res(sh, R10K, "I2C_DUT_EN", "GND")

    sh.group("RESET (OD) / BOOT (3-state)")
    part(sh, "Q", "Transistor_FET:2N7002", "C8545", {
        "G": "RESET_DUT_CTL", "S": "GND", "D": "RESET_OD"})
    res(sh, R100K, "RESET_DUT_CTL", "GND")
    ls = part(sh, "U", "Logic_LevelTranslator:SN74LVC1T45DBV", "C7843", {
        "VCCA": "+3V3", "VCCB": "VIO", "GND": "GND", "A": "BOOT_DUT_CTL", "B": "BOOT_B",
        "DIR": "BOOT_DIR"})
    cap(sh, C100N, "+3V3", near=(ls, "VCCA"))
    cap(sh, C100N, "VIO", near=(ls, "VCCB"))
    res(sh, R100K, "BOOT_DIR", "GND")

    sh.group("Input bias 1M")
    for net in ("IN1_B", "IN2_B", "IN3_B", "IN4_B", "SPI_MISO_B", "SWCLK_B", "BOOT_B"):
        res(sh, R1M, net, "GND")
    for net in ("UART_RX_B", "SWO_DUT_B", "SWDIO_B"):
        res(sh, R1M, net, "VIO")
    # The output translator B side floats while /OE is high: bias it to each signal's idle level.
    for net in ("OUT1_B", "OUT2_B", "OUT3_B", "OUT4_B", "SPI_SCK_B", "SPI_MOSI_B"):
        res(sh, R1M, net, "GND")
    for net in ("UART_TX_B", "SPI_CS_B"):
        res(sh, R1M, net, "VIO")

    sh.note("All translators are Hi-Z until firmware drives LS_OE_N low / DIR high / I2C_DUT_EN high.")
    return sh


def connectors_sheet():
    sh = Sheet("connectors", "DUT connectors and ESD")

    series = [
        ("OUT1_B", "OUT1"), ("OUT2_B", "OUT2"), ("OUT3_B", "OUT3"), ("OUT4_B", "OUT4"),
        ("UART_TX_B", "TX"), ("SPI_SCK_B", "SPI_SCK"), ("SPI_MOSI_B", "SPI_MOSI"),
        ("SPI_CS_B", "SPI_CS"),
        ("IN1_B", "IN1"), ("IN2_B", "IN2"), ("IN3_B", "IN3"), ("IN4_B", "IN4"),
        ("UART_RX_B", "RX"), ("SPI_MISO_B", "SPI_MISO"), ("SWO_DUT_B", "SWO"),
        ("SWCLK_B", "SWCLK"), ("SWDIO_B", "SWDIO"), ("RESET_OD", "RESET"), ("BOOT_B", "BOOT"),
    ]
    sh.group("Series resistors")
    for i, (inner, outer) in enumerate(series):
        if i == 10:
            sh.group("Series resistors (cont.)", column_break=True)
        res(sh, R100, inner, outer)

    # Channels grouped per header so that each TVS sits next to its connector.
    esd = ["OUT1", "OUT2", "OUT3", "OUT4",              # J_IO
           "IN1", "IN2", "IN3", "IN4",                  # J_IO
           "I2C_SDA", "I2C_SCL", "SPI_SCK", "SPI_MOSI",  # J_BUS
           "SPI_MISO", "SPI_CS", "TX", "RX",            # J_BUS / J_UART_ANA
           "AIN1", "AIN2", "AOUT", None,                # J_UART_ANA
           "SWDIO", "SWCLK", "SWO", "RESET",            # J_DBG
           "BOOT", "VIO", None, None,                   # J_DBG / J_PWR
           "5V_DUT", "5V_SW", "3V3_DUT", "3V3_SW"]      # J_PWR
    channels = ["D1+", "D1-", "D2+", "D2-"]
    sh.group("ESD (TPD4E05U06)", column_break=True)
    for i in range(0, len(esd), 4):
        if i == 16:
            sh.group("ESD (cont.)", column_break=True)
        nets = {"GND": "GND", "NC": None}
        nets.update({ch: net for ch, net in zip(channels, esd[i:i + 4])})
        part(sh, "U", "Power_Protection:TPD4E05U06DQA", "C138714", nets)

    sh.group("DUT headers (2.54 mm)", column_break=True)
    headers = [
        ("J_PWR", "Connector_Generic:Conn_01x07", "C492406",
         ["5V_DUT", "5V_SW", "3V3_DUT", "3V3_SW", "VIO", "GND", "GND"]),
        ("J_DBG", "Connector_Generic:Conn_01x07", "C492406",
         ["VIO", "SWDIO", "SWCLK", "SWO", "RESET", "BOOT", "GND"]),
        ("J_BUS", "Connector_Generic:Conn_01x07", "C492406",
         ["I2C_SDA", "I2C_SCL", "SPI_SCK", "SPI_MOSI", "SPI_MISO", "SPI_CS", "GND"]),
        ("J_UART_ANA", "Connector_Generic:Conn_01x07", "C492406",
         ["TX", "RX", "GND", "AIN1", "AIN2", "AOUT", "GND"]),
        ("J_IO", "Connector_Generic:Conn_01x10", "C492409",
         ["OUT1", "OUT2", "OUT3", "OUT4", "GND", "IN1", "IN2", "IN3", "IN4", "GND"]),
    ]
    for name, lib_id, lcsc, pins in headers:
        if name == "J_UART_ANA":
            sh.group("DUT headers (cont.)", column_break=True)
        sh.add("J", lib_id, name, {str(i): n for i, n in enumerate(pins, 1)},
               fields={"LCSC": lcsc})

    sh.group("Mounting holes")
    for _ in range(4):
        sh.add("H", "Mechanical:MountingHole", "M3", {}, in_bom=False,
               fields={"Footprint": HOLE_FOOTPRINT})

    sh.note("Signal path: header -> TVS -> 100R series -> translator / circuit.")
    sh.note("DUT rails and VIO are probed on J_PWR / J_DBG pins (no separate test points).")
    return sh


def decoupling(sheets):
    """Map capacitor ref -> (part ref, pad number) for each capacitor declared with `near`.

    Fails if the capacitor does not share a net with that pin.
    """
    result = {}
    for sheet in sheets:
        for c in sheet.parts:
            near = getattr(c, "near", None)
            if not near:
                continue
            target, key = near
            pins = [(pin, net) for pin, net in schgen.resolve_pins(target)
                    if key in (pin.number, pin.name)]
            if not pins:
                raise KeyError(f"{c.ref}: pin {key} not found on {target.ref}")
            pin, net = pins[0]
            if net not in c.nets.values():
                raise ValueError(f"{c.ref} does not decouple {target.ref} pin {pin.number} ({net})")
            result[c.ref] = (target.ref, pin.number)
    return result


def annotate(sheets):
    counters = {}
    for sheet in sheets:
        for p in sheet.parts:
            counters[p.ref] = counters.get(p.ref, 0) + 1
            if p.ref.startswith("#"):
                p.ref = f"{p.ref}{counters[p.ref]:02d}"
            else:
                p.ref = f"{p.ref}{counters[p.ref]}"


def build():
    sheets = [power_sheet(), mcu_sheet(), sensing_sheet(), vio_sheet(), translators_sheet(),
              connectors_sheet()]
    annotate(sheets)
    return sheets


def main():
    sheets = build()
    date = datetime.date.today().isoformat()
    files = schgen.write_project(sheets, bom_fields, TITLE, REV, date, root_notes=[
        "OOTY rev A - hierarchical schematic generated by scripts/build_schematic.py",
        "Specification: SPEC.md - design notes and calculations: NOTES.md",
    ])
    for f in files:
        print(f"wrote {f.name}")


if __name__ == "__main__":
    main()

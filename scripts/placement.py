"""Footprint placement for OOTY.kicad_pcb, in board coordinates (mm, origin = top-left corner).

Each entry: ref -> (expected value, x, y, rotation in degrees, side). The expected value guards
against annotation changes in the schematic.

Floor plan (see NOTES.md, Phase 4):
- left edge: USB-C; power path below it (PTC, TVS, DUT rail switches, shunts, INA226) next to
  J_PWR; 3V3 buck in the top-left corner
- centre: MCU rotated 180 deg (USB pins face the USB-C, SWD probe pins face J_DBG, SPI and analog
  pins face J_BUS / J_UART_ANA)
- above J_DBG: SWD/RESET/BOOT drivers; above J_IO: the two 8-bit translators
- right edge: ESD next to J_BUS / J_UART_ANA, I2C buffer, DAC buffer, VIO mux + LDO
- top-right corner: LEDs and user buttons (outside the OLED module footprint)
"""

ORIGIN = (100.0, 100.0)

# Board 85 x 55 mm. M3 holes 3.5 mm from each edge.
# Bottom edge: J_PWR, J_DBG, J_IO (pins along x, pin 1 on the left, rotation 90).
# Right edge: J_BUS, J_UART_ANA (pins along y, pin 1 on top, rotation 0).
# Left edge: USB-C (receptacle front flush with the board edge, rotation 270).
PLACEMENT = {
    "H1": ("M3", 3.5, 3.5, 0, "F"),
    "H2": ("M3", 81.5, 3.5, 0, "F"),
    "H3": ("M3", 3.5, 51.5, 0, "F"),
    "H4": ("M3", 81.5, 51.5, 0, "F"),
    "J1": ("TYPE-C-31-M-12", 3.65, 27.5, 270, "F"),
    "J3": ("OLED 0.91in", 22.0, 3.5, 0, "F"),
    "J4": ("J_PWR", 12.0, 52.0, 90, "F"),
    "J5": ("J_DBG", 31.05, 52.0, 90, "F"),
    "J8": ("J_IO", 50.1, 52.0, 90, "F"),
    "J6": ("J_BUS", 82.0, 9.4, 0, "F"),
    "J7": ("J_UART_ANA", 82.0, 28.45, 0, "F"),
    # MCU and HIL debug header
    "U8": ("STM32G431MBT6", 44.0, 21.5, 180, "F"),
    "J2": ("SWD_HIL", 28.0, 19.5, 0, "F"),
    # USB input, PTC, TVS, internal rail test points
    "U2": ("USBLC6-2SC6", 12.0, 27.5, 0, "F"),
    "C1": ("100nF/50V", 14.7, 24.6, 90, "F"),
    "U1": ("TPD4E05U06DQAR", 10.6, 32.4, 0, "F"),
    "R1": ("5.1k", 12.6, 31.6, 0, "F"),
    "R2": ("5.1k", 12.6, 33.2, 0, "F"),
    "F1": ("PTC 2.6A", 4.6, 37.5, 270, "F"),
    "D1": ("SMAJ5.0A", 4.8, 43.0, 0, "F"),
    "TP1": ("VBUS", 16.8, 30.8, 0, "F"),
    "TP2": ("+5V", 9.7, 41.8, 0, "F"),
    "TP3": ("+3V3", 9.5, 8.6, 0, "F"),
    "TP4": ("GND", 13.5, 8.6, 0, "F"),
    # 3V3 buck (TLV62569, SLVSDG1C section 10): Cin on VIN with its ground via next to the GND pin,
    # inductor straight off SW, Cout at the inductor output, feedback divider on the FB side.
    "U3": ("TLV62569DBVR", 14.0, 13.0, 0, "F"),
    "C4": ("100nF/50V", 16.7, 14.45, 270, "F"),
    "C3": ("10uF/25V", 18.45, 14.6, 270, "F"),
    "L1": ("2.2uH", 8.9, 13.95, 180, "F"),
    "C6": ("22uF/25V", 4.95, 14.0, 270, "F"),
    "C7": ("22uF/25V", 2.85, 14.0, 270, "F"),
    "R4": ("22k", 17.2, 12.0, 0, "F"),
    "R3": ("100k", 17.2, 10.8, 180, "F"),
    "C5": ("6.8pF DNP", 17.2, 9.6, 180, "F"),
    # Current monitors (Kelvin sense lines down to the shunts)
    "U9": ("INA226AIDGSR", 13.5, 21.8, 0, "F"),
    "U10": ("INA226AIDGSR", 20.5, 21.8, 0, "F"),
    # VIO mux + LDO: low parts under the OLED module
    "U12": ("TPS2116DRLR", 27.0, 5.5, 0, "F"),
    "U13": ("AP2127K-ADJTRG1", 32.0, 5.5, 0, "F"),
    "Q1": ("2N7002", 32.0, 10.0, 0, "F"),
    # DUT rail switches above J_PWR (pin 1 5V_DUT, 2 5V_SW, 3 3V3_DUT, 4 3V3_SW), shunts in line
    # with their header pins, rail ESD between the shunts
    "U5": ("AP22653W6-7", 12.0, 37.5, 0, "F"),
    "U4": ("AP22653W6-7", 18.6, 37.5, 0, "F"),
    "U7": ("AP22653W6-7", 25.2, 37.5, 0, "F"),
    "U6": ("AP22653W6-7", 31.8, 37.5, 0, "F"),
    # ILIM resistors next to pin 5 of their switch
    "R9": ("39k", 14.65, 37.5, 90, "F"),
    "R6": ("22k", 21.25, 37.5, 90, "F"),
    "R15": ("68k", 27.85, 37.5, 90, "F"),
    "R12": ("39k", 34.45, 37.5, 90, "F"),
    # Shunts: switch side (pad 1, *_PRE) up, header side down
    "R22": ("50mR 1% 1W", 14.54, 43.2, 270, "F"),
    "R23": ("100mR 1% 1W", 19.62, 43.2, 270, "F"),
    "U27": ("TPD4E05U06DQAR", 17.08, 44.6, 0, "F"),
    # SWD probe, RESET and BOOT drivers above J_DBG
    "U17": ("SN74LVC1T45DBVR", 34.5, 41.8, 0, "F"),
    "U16": ("SN74LVC1T45DBVR", 39.2, 41.8, 0, "F"),
    "Q2": ("2N7002", 43.4, 41.8, 0, "F"),
    "U19": ("SN74LVC1T45DBVR", 47.6, 41.8, 0, "F"),
    "U25": ("TPD4E05U06DQAR", 37.4, 45.4, 90, "F"),
    "U26": ("TPD4E05U06DQAR", 44.4, 45.4, 90, "F"),
    # Series resistors between the drivers and the ESD of J_DBG
    "R85": ("100R", 33.6, 45.4, 90, "F"),
    "R83": ("100R", 35.0, 45.4, 90, "F"),
    "R84": ("100R", 39.8, 45.4, 90, "F"),
    "R86": ("100R", 41.2, 45.4, 90, "F"),
    "R87": ("100R", 47.0, 45.4, 90, "F"),
    # Translators above J_IO: A side (pins 1-12) up towards the MCU, B side down to the header
    "U14": ("SN74LVC8T245PWR", 57.0, 34.5, 270, "F"),
    "U15": ("SN74LVC8T245PWR", 68.0, 34.5, 270, "F"),
    "U20": ("TPD4E05U06DQAR", 53.9, 45.4, 90, "F"),
    "U21": ("TPD4E05U06DQAR", 66.6, 45.4, 90, "F"),
    # Right edge: ESD next to J_BUS / J_UART_ANA, I2C buffer, DAC buffer
    "U22": ("TPD4E05U06DQAR", 74.6, 13.2, 0, "F"),
    "U23": ("TPD4E05U06DQAR", 74.6, 25.6, 0, "F"),
    "U24": ("TPD4E05U06DQAR", 74.6, 38.6, 0, "F"),
    "U18": ("TCA9517ADGKR", 69.0, 16.5, 0, "F"),
    "U11": ("TLV9001IDBVR", 70.0, 41.5, 0, "F"),
    # Top-right corner: LEDs and user buttons
    "D2": ("PWR", 59.0, 3.8, 90, "F"),
    "D3": ("HB", 60.6, 3.8, 90, "F"),
    "SW1": ("BTN1", 66.5, 4.2, 0, "F"),
    "SW2": ("BTN2", 74.15, 4.2, 0, "F"),
}

# Board area available to the auto-placer (board coordinates, 0.5 mm inside the outline).
AREA = (1.2, 1.2, 83.8, 53.8)

# Areas kept free of parts (board coordinates).
KEEPOUTS = [
    (10.0, 47.0, 74.5, 50.6),   # labels above J_PWR / J_DBG / J_IO
    (76.4, 7.5, 80.2, 45.5),    # labels left of J_BUS / J_UART_ANA
    (58.5, 9.4, 75.5, 14.1),    # board marking
    (58.6, 6.0, 63.5, 7.9),     # LED labels
    (0.0, 0.0, 7.0, 7.0),       # M3 screw heads (see MOUNTING_KEEPOUT_D)
    (78.0, 0.0, 85.0, 7.0),
    (0.0, 48.0, 7.0, 55.0),
    (78.0, 48.0, 85.0, 55.0),
    (14.2, 25.3, 36.3, 28.9),   # USB D+/D- corridor from the USBLC6 to the MCU
]

# Copper keepout around the mounting holes (M3 pan head, DIN 7985: 5.6 mm, plus margin).
MOUNTING_KEEPOUT_D = 7.0

HEADERS_BOTTOM = ("J_PWR", "J_DBG", "J_IO")
HEADERS_RIGHT = ("J_BUS", "J_UART_ANA")

# Board marking (text, x, y, height).
MARKING = [
    ("OOTY HIL rev A", 67.0, 10.7, 1.5),
    ("2026-10", 67.0, 12.9, 1.0),
    ("PWR HB", 59.8, 6.9, 1.0),
]


def refs_with_value(values):
    return {ref for ref, entry in PLACEMENT.items() if entry[0] in values}


def absolute(box):
    return (ORIGIN[0] + box[0], ORIGIN[1] + box[1], ORIGIN[0] + box[2], ORIGIN[1] + box[3])


def position(ref, value=None):
    """Absolute (x, y, rotation, side) for `ref`, or None if not placed yet."""
    entry = PLACEMENT.get(ref)
    if entry is None:
        return None
    expected, x, y, rot, side = entry
    if value is not None and value != expected:
        raise ValueError(f"placement: {ref} is '{value}', expected '{expected}'")
    return ORIGIN[0] + x, ORIGIN[1] + y, rot, side

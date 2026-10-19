"""Footprint placement for OOTY.kicad_pcb, in board coordinates (mm, origin = top-left corner).

Each entry: ref -> (expected value, x, y, rotation in degrees, side). The expected value guards
against annotation changes in the schematic.
"""

ORIGIN = (100.0, 100.0)

# Board 85 x 55 mm. M3 holes 3.5 mm from each edge.
# Bottom edge: J_PWR, J_DBG, J_IO (pins along x, pin 1 on the left, rotation 90).
# Right edge: J_BUS, J_UART_ANA (pins along y, pin 1 on top, rotation 0).
# Left edge: USB-C (mouth flush with the edge, rotation 270).
PLACEMENT = {
    "H1": ("M3", 3.5, 3.5, 0, "F"),
    "H2": ("M3", 81.5, 3.5, 0, "F"),
    "H3": ("M3", 3.5, 51.5, 0, "F"),
    "H4": ("M3", 81.5, 51.5, 0, "F"),
    "J1": ("TYPE-C-31-M-12", 4.2, 27.5, 270, "F"),
    "J2": ("SWD_HIL", 12.0, 10.5, 0, "F"),
    "J3": ("OLED 0.91in", 22.0, 3.5, 0, "F"),
    "J4": ("J_PWR", 12.0, 52.0, 90, "F"),
    "J5": ("J_DBG", 31.05, 52.0, 90, "F"),
    "J8": ("J_IO", 50.1, 52.0, 90, "F"),
    "J6": ("J_BUS", 82.0, 9.4, 0, "F"),
    "J7": ("J_UART_ANA", 82.0, 28.45, 0, "F"),
    # Anchors (Phase 4): the other parts are placed around them by scripts/autoplace.py.
    "U8": ("STM32G431RBT6", 34.0, 23.0, 0, "F"),
    "U2": ("USBLC6-2SC6", 12.5, 24.0, 0, "F"),
    "U1": ("TPD4E05U06DQAR", 12.5, 31.0, 90, "F"),
    "D1": ("SMAJ5.0A", 9.5, 18.0, 0, "F"),
    "F1": ("PTC 2.6A", 12.5, 36.5, 0, "F"),
    "U3": ("TLV62569DBVR", 17.5, 39.0, 0, "F"),
    "L1": ("2.2uH", 23.5, 39.0, 0, "F"),
    "U9": ("INA226AIDGSR", 6.0, 39.5, 0, "F"),
    "U10": ("INA226AIDGSR", 27.5, 34.0, 0, "F"),
    "U4": ("AP22653W6-7", 9.0, 44.5, 0, "F"),
    "U5": ("AP22653W6-7", 15.0, 44.5, 0, "F"),
    "U6": ("AP22653W6-7", 21.0, 44.5, 0, "F"),
    "U7": ("AP22653W6-7", 27.0, 44.5, 0, "F"),
    "U12": ("TPS2116DRLR", 49.0, 30.0, 0, "F"),
    "U14": ("SN74LVC8T245PWR", 58.0, 39.0, 0, "F"),
    "U15": ("SN74LVC8T245PWR", 68.0, 39.0, 0, "F"),
    "D2": ("PWR", 64.0, 3.5, 0, "F"),
    "D3": ("HB", 68.0, 3.5, 0, "F"),
}

# Board area available to the auto-placer (board coordinates, 0.5 mm inside the outline).
AREA = (1.2, 1.2, 83.8, 53.8)


def position(ref, value=None):
    """Absolute (x, y, rotation, side) for `ref`, or None if not placed yet."""
    entry = PLACEMENT.get(ref)
    if entry is None:
        return None
    expected, x, y, rot, side = entry
    if value is not None and value != expected:
        raise ValueError(f"placement: {ref} is '{value}', expected '{expected}'")
    return ORIGIN[0] + x, ORIGIN[1] + y, rot, side

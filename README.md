# RFID Panel Box (RPB-001) — project pack

Dock-door panel boxes for Gielow Pickles, G5 Croswell. One box per dock door. Each box holds a UHF RFID
reader, a Waveshare relay/input board, a PoE switch, two DIN supplies, a stack light, a truck-present
sensor and a safety beam. The relay board runs the firmware in this pack and talks MQTT to a C# service
(the rebuilt "MERP RFID" Windows service) that decides what the stack light shows.

## Contents
| Path | What |
|---|---|
| `CLAUDE.md` | Task list for Claude Code |
| `firmware/rfid_panel_box/rfid_panel_box.ino` | Arduino sketch for the Waveshare ESP32-S3-POE-ETH-8DI-8RO (fw 1.1.0) |
| `firmware/rfid_panel_box/config.h` | Per-door settings: door id, broker, static IP, input polarity |
| `docs/MQTT_CONTRACT.md` | Topics, payloads, server rules |
| `docs/drawings/RFID_Panel_Box_RPB-001_rev8.pdf / .dxf` | 2-sheet drawing: panel layout + wiring schematic (ANSI C, inches) |
| `docs/parts-list/RFID_Panel_Box_Parts_List_rev5.pdf` | BOM per box, compatibility checks, layout |
| `docs/schematic/RFID_Panel_Box_Illustrated_Schematic_rev8.png / .pdf` | One-page illustrated schematic with wire numbers |
| `docs/wiring/RFID_Panel_Box_Wiring_rev9.pdf` | **Wiring diagram rev 9 (proposed), 5 sheets ANSI B**: W1 power, W2 relay outputs, W3 inputs, W4 network/RF, W5 wire/terminal/gland schedules. PNGs in `docs/wiring/png/` |
| `docs/wiring/generate_wiring.py` + `render.js` | Source for the wiring sheets. `python3 generate_wiring.py && node render.js` |
| `docs/controls/png/` | Control concept images: dock-door view, CS1 operator station, light storyboard, dashboard mockup (`controls_concept.html` + `render.js`) |
| `docs/SESSION_NOTES.md` | Decisions made in the design sessions and open items |

## Hardware in the box (rev 8)
| Ref | Part | Notes |
|---|---|---|
| K1 | Waveshare **ESP32-S3-POE-ETH-8DI-8RO** | 8 relays, 8 opto DI, W5500 Ethernet, **PoE-powered from SW1 P2**. Runs the firmware. |
| U1 | WYUAN M-808EK UHF reader | TCP/IP, powered + data via SPL1. GPIO pin 12 GPI1+ = +12 V (TB1-6, F5); pin 11 GPI1− sinks to 0 V through TB3 diode D2 when B2 trips → reader triggers itself. Other GPIO pins empty. |
| SW1 | GoodTop PoE+ 5-port switch | P1→SPL1, P2→K1, P5=uplink to plant network (C4 via gland G4) |
| PSU1 | NDR-120-12 | 12 V → TB1 → stack lights, sensors, relay commons |
| PSU2 | 48 V DIN supply (ships with SW1) | SW1 only |
| SPL1 | REVODATA PS5712BG-25 PoE splitter | 12 V 3 A + data pigtail → U1 |
| TB1 | 12 V distribution terminals | 3× +12 V, 3× 0 V |
| B1 | DIHOOL M16 laser diffuse sensor, NPN NO, 3–80 cm | **truck present** → K1 DI1 (BN +12, BU 0 V, BK signal) |
| B2 | JUTAI IRR-7M retro-reflective beam, relay out | **forklift beam** → NO to TB3 diode node → D1 → K1 DI2 and D2 → U1 GPI1−; COM to K1 DGND / 0 V (RD +12, BK 0 V, WH COM, GN NO, YE NC) |
| HL1/HL2 | 12 V stack lights (R/A/G + buzzer), wired in parallel at TB2 | K1 CH1 red, CH2 amber, CH3 green, CH4 buzzer; relay commons jumpered to +12 V |
| CS1 | Operator station (rev 9 proposal): S1 LOAD COMPLETE (lit), S2 ACK/SILENCE, S3 MAINT key | K1 DI3 / DI4 / DI5, S1 lamp on CH5. Sheet W3 |
| TB0 / TB2 | AC entry terminals (L/N/PE) / lamp marshalling (rev 9 proposal) | Sheets W1 / W2 |

## Light logic (lives in the C# service, not the firmware)
- **Red** = no truck at the door. **Amber** = truck docked, reader idle. **Green** = beam broken → reader active.
- Beam breaks only count while the truck input is closed.
- Firmware fail-safe: red on power-up and whenever the broker is unreachable for 10 s.

## Bench test
Build: Arduino IDE 2.x or arduino-cli, `esp32` core **3.x** (compiled clean on 3.3.12), PubSubClient 2.8,
board "ESP32S3 Dev Module", USB CDC On Boot = Enabled. Edit `config.h` per door, then flash over USB-C.
The on-board RGB LED shows red = no Ethernet, blue = no MQTT, green = online, amber = online but fail-safe.

1. Flash, open Serial at 115200. You should see `ETH link up`, `ETH IP ...`, `MQTT connecting... ok`.
2. Put a hand in front of B1 → serial prints `DI1 -> 1` and `dock/doorXX/inputs` updates. If it reads
   backwards, flip `INPUT_ACTIVE_LOW`.
3. Block the beam → `DI2` toggles. Decide NO vs NC on the JUTAI so that "beam broken" = 1.
4. `mosquitto_pub -t dock/door04/light/set -m green` → CH3 clicks, CH1/CH2 off, `dock/door04/light` = green.
5. Kill the broker → after 10 s the box goes red on its own.
6. `mosquitto_pub -t dock/door04/buzzer/set -m beep` → CH4 pulses, stops by itself after 30 s.
   `-t dock/door04/pilot/set -m blink` → CH5 blinks. `-t dock/door04/light/set -m yellow_blink` → CH2 blinks.
7. `mosquitto_pub -r -t dock/server/status -m offline` → box goes red (clear it with `-m online`).
8. Press S1 / S2, turn S3 → `inputs` shows `release` / `ack` / `maint` true.
9. Reader GPI1: meter U1 pin 12 → TB1 0 V = 12 V. Block B2 → pin 11 drops to ~0.7 V, DI2 = 1, and the
   reader starts an inventory (set GPI1 trigger mode in the reader's config tool). Unblock → DI2 = 0,
   pin 11 floats up, reader stops. With B2 clear, DI2 must stay 0 (proves D1/D2 block the sneak path).

## Known unknowns (verify on the real board)
- Physical terminal order of DI1–DI8 and the input common (DGND). The drawing bonds DGND to 0 V so the
  PSU1-powered NPN sensor can sink into the input — confirm against Waveshare's DI wiring diagram.
- ETH reset pin (39 in the sketch) and whether the PoE module is 802.3af or at. GoodTop total PoE budget.
- B2 model: ordered IRR-7M; product photos show IRR-7R.

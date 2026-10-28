# MQTT contract - panel box <-> C# service  (firmware 1.1.0)

Broker: Mosquitto on the server (plain MQTT, port 1883). One client per box, client id `rfidbox-<DOOR_ID>`.
Base topic: `dock/<DOOR_ID>` e.g. `dock/door04`.

## Box -> server
| Topic | Retained | Payload |
|---|---|---|
| `dock/doorXX/status` | yes | `online` / `offline` (offline = Last Will, QoS 1) |
| `dock/doorXX/inputs` | yes | `{"truck":true,"beam":false,"release":false,"ack":false,"maint":false,"di":[1,0,0,0,0,0,0,0]}` - on change, debounced 50 ms |
| `dock/doorXX/light` | yes | `red` / `yellow` / `green` / `off`, or `red_blink` / `yellow_blink` / `green_blink` |
| `dock/doorXX/buzzer` | yes | `off` / `on` / `beep` / `chirp` |
| `dock/doorXX/pilot` | yes | `off` / `on` / `blink` (S1 LOAD COMPLETE button lamp, K1 CH5) |
| `dock/doorXX/info` | no | every 30 s, see below |

`info` example:
```json
{"fw":"1.1.0","mac":"AA:BB:CC:DD:EE:FF","ip":"10.0.0.44","uptime_s":123,
 "failsafe":false,"failsafe_reason":"none","light":"yellow","relay_ok":true,"relays":2}
```
`failsafe_reason` = `boot` / `broker` / `server` / `timeout` / `none`. `relays` = CH1-CH8 bit mask (CH1 = bit 0).
`relay_ok` false means the relay expander did not ACK on I2C - treat the door as faulted.

## Server -> box (never retained)
| Topic | Payload | Notes |
|---|---|---|
| `dock/doorXX/light/set` | `red` `yellow` (`amber` ok) `green` `off`, or `<color>_blink` | Clears fail-safe. Exactly one lamp, always. |
| `dock/doorXX/buzzer/set` | `off` `on` `beep` `chirp` | `on`/`beep` stop by themselves after 30 s. `chirp` = one 150 ms blip. Ignored in fail-safe (except `off`). |
| `dock/doorXX/pilot/set` | `off` `on` `blink` | S1 button lamp. Ignored in fail-safe (except `off`). |

## Server presence (new)
The C# service connects with Last Will `dock/server/status` = `offline` (retained, QoS 1) and publishes
`online` (retained) after connecting. Every box subscribes; on `offline` it drops to red fail-safe even
though the broker is still up. The topic is set in `config.h` (`SERVER_STATUS_TOPIC`).

Optional belt-and-braces: set `LIGHT_CMD_TIMEOUT_MS` (e.g. 60000) in `config.h` and have the server
re-send the current `light/set` every 20 s. Off by default.

## Server rules
1. When `status` goes `online`, immediately re-send `light/set` (and `pilot/set` if used).
2. Never publish any `/set` topic retained (a rebooted box would replay a stale green).
3. Treat `inputs.beam` as valid only while `inputs.truck` is true.
4. If `status` is `offline`, `info.failsafe` is true, or `info.relay_ok` is false, show the door as faulted.
5. `inputs.maint` true = door in maintenance: show it on the dashboard, don't drive green, ignore beam.
6. `release` / `ack` are momentary buttons - act on the false->true edge of the retained `inputs` message.

## Suggested light logic (server side)
| Condition | Light | Buzzer | Pilot (S1) |
|---|---|---|---|
| No truck | `red` | off | off |
| Truck docked, reader idle | `yellow` | `chirp` on arrival | `blink` once tags have been read |
| Truck + beam broken (reader active) | `green` | off | `on` |
| Unknown / wrong-load tag read | `red_blink` | `beep` until S2 ACK | off |
| Load complete pressed (S1) | `yellow_blink` 10 s, then `red` when truck leaves | `chirp` | off |
| Maintenance key (S3) | `yellow_blink` | off | off |
| Box fault (server side view) | n/a, the box shows red itself | n/a | n/a |

## Box rules (firmware)
- Exactly one lamp relay on at a time. Setting a light clears the other two; blink only toggles that one lamp.
- Boot state = red, failsafe = true. Failsafe clears on the first valid `light/set`.
- Broker unreachable >= 10 s, or `dock/server/status` = `offline` -> red, buzzer off, pilot off, failsafe = true.
- Relay expander re-written every 1 s so a glitch can't leave a stale relay on.
- Task watchdog reboots the board if the loop hangs for 20 s (it comes back red).

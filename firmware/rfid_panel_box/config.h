// Per-door settings. Edit this file only when flashing a new box.
#pragma once

// ---- Door ----
#define DOOR_ID        "door04"        // MQTT base = dock/<DOOR_ID>

// ---- Broker (Mosquitto on the server) ----
#define MQTT_HOST      "192.168.1.50"
#define MQTT_PORT      1883
#define MQTT_USER      ""
#define MQTT_PASS      ""

// C# service publishes "online" (retained) here and sets LWT "offline".
// If it goes "offline" the box drops to the fail-safe light even though the
// broker is still up. Set to "" to disable.
#define SERVER_STATUS_TOPIC  "dock/server/status"

// Optional: fail-safe if no light/set arrives for this long (ms).
// 0 = off. If you use it, have the server re-send light/set every ~20 s.
#define LIGHT_CMD_TIMEOUT_MS 0

// ---- Network ----
#define USE_STATIC_IP  false
#define STATIC_IP      192, 168, 1, 104
#define GATEWAY_IP     192, 168, 1, 1
#define SUBNET_MASK    255, 255, 255, 0
#define DNS_IP         192, 168, 1, 1

// ---- Inputs ----
// Opto inputs read LOW when the input is driven (NPN sinking / contact closed).
// Flip if a bench test reads backwards.
#define INPUT_ACTIVE_LOW true

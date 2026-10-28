/*
  RFID Panel Box firmware - Waveshare ESP32-S3-POE-ETH-8DI-8RO
  ---------------------------------------------------------------
  Board package : esp32 by Espressif Systems 3.x (W5500 Ethernet via ETH.h)
  Library       : PubSubClient 2.8
  Board         : ESP32S3 Dev Module, USB CDC On Boot = Enabled

  The box is "dumb": it reports inputs and shows whatever light the
  server tells it to. All door logic lives in the C# service.
  Per-door settings live in config.h. Full topic list: docs/MQTT_CONTRACT.md

  Relays (TCA9554)          Inputs (opto, GPIO 4-11)
    CH1 red lamp              DI1 B1 truck present
    CH2 amber lamp            DI2 B2 forklift beam
    CH3 green lamp            DI3 S1 LOAD COMPLETE pushbutton
    CH4 buzzer                DI4 S2 ACK / SILENCE pushbutton
    CH5 S1 button lamp        DI5 S3 MAINT keyswitch
    CH6-CH8 spare             DI6-DI8 spare

  Safety
    - Exactly one lamp relay on at a time (steady or blinking).
    - Red on boot; red when broker or C# service is gone for 10 s.
    - Buzzer and S1 lamp go off in fail-safe; buzzer self-stops after 30 s.
*/

#include <Arduino.h>
#include <WiFi.h>      // provides WiFiClient; runs over Ethernet in core 3.x
#include <ETH.h>
#include <SPI.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <esp_task_wdt.h>
#include "config.h"

#define FW_VERSION "1.1.0"

// ================= Board pins =================
// Waveshare ESP32-S3-ETH-8DI-8RO wiki pin map. ETH_RST 39 still to confirm.
#define ETH_CS    16
#define ETH_INT   12
#define ETH_RST   39
#define ETH_SCK   15
#define ETH_MISO  14
#define ETH_MOSI  13

#define I2C_SDA   42
#define I2C_SCL   41
#define TCA9554_ADDR 0x20          // relay I/O expander

#define STATUS_LED_PIN 38          // on-board WS2812, for the technician

const uint8_t DI_PINS[8] = {4, 5, 6, 7, 8, 9, 10, 11};

// ================= Wiring map (0-based) =================
#define RELAY_RED     0   // CH1
#define RELAY_AMBER   1   // CH2
#define RELAY_GREEN   2   // CH3
#define RELAY_BUZZER  3   // CH4
#define RELAY_PILOT   4   // CH5  S1 button lamp
#define DI_TRUCK      0   // DI1
#define DI_BEAM       1   // DI2
#define DI_RELEASE    2   // DI3  S1 load complete
#define DI_ACK        3   // DI4  S2 ack / silence
#define DI_MAINT      4   // DI5  S3 maintenance key

// ================= Timing / safety =================
const uint32_t DEBOUNCE_MS     = 50;
const uint32_t HEARTBEAT_MS    = 30000;
const uint32_t RECONNECT_MS    = 5000;
const uint32_t FAILSAFE_MS     = 10000;  // broker unreachable this long -> fail-safe
const uint32_t BLINK_MS        = 500;    // lamp / pilot blink half-period
const uint32_t BEEP_MS         = 250;    // buzzer beep half-period
const uint32_t CHIRP_MS        = 150;
const uint32_t BUZZER_MAX_MS   = 30000;  // buzzer never sounds longer than this per command
const uint32_t RELAY_REFRESH_MS = 1000;  // rewrite expander in case it reset
const uint32_t WDT_TIMEOUT_S   = 20;

enum Light  { L_OFF, L_RED, L_YELLOW, L_GREEN };
enum Mode   { M_OFF, M_ON, M_BLINK, M_BEEP, M_CHIRP };
const Light FAILSAFE_LIGHT = L_RED;      // never leave green on without the server

// ================= State =================
const String BASE = String("dock/") + DOOR_ID;
WiFiClient netClient;
PubSubClient mqtt(netClient);

uint8_t relayMask = 0, lastWrittenMask = 0xFF;
bool relayOk = false;

Light currentLight = L_OFF;
bool lightBlink = false;
Mode buzzerMode = M_OFF;
Mode pilotMode = M_OFF;
uint32_t buzzerStartMs = 0;

bool failsafe = false;
const char* failsafeReason = "boot";

bool diRaw[8], diStable[8];
uint32_t diChangeMs[8];

uint32_t lastLinkMs = 0, lastReconnectMs = 0, lastHeartbeatMs = 0;
uint32_t lastCmdMs = 0, lastRefreshMs = 0;

// ================= Relays (TCA9554) =================
bool tcaWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(TCA9554_ADDR);
  Wire.write(reg);
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

// Output register first, then direction, so pins never glitch on.
void writeRelays(bool force = false) {
  if (!force && relayMask == lastWrittenMask) return;
  bool ok = tcaWrite(0x01, relayMask) && tcaWrite(0x03, 0x00);
  if (ok != relayOk) Serial.printf("Relay expander %s\n", ok ? "ok" : "NOT RESPONDING");
  relayOk = ok;
  lastWrittenMask = ok ? relayMask : 0xFF;
}

inline void setBit(uint8_t ch, bool on) {
  if (on) relayMask |= (1 << ch); else relayMask &= ~(1 << ch);
}

// ================= Names =================
const char* colorName(Light l) {
  switch (l) {
    case L_RED:    return "red";
    case L_YELLOW: return "yellow";
    case L_GREEN:  return "green";
    default:       return "off";
  }
}

String lightState() {
  String s = colorName(currentLight);
  if (lightBlink && currentLight != L_OFF) s += "_blink";
  return s;
}

const char* modeName(Mode m) {
  switch (m) {
    case M_ON:    return "on";
    case M_BLINK: return "blink";
    case M_BEEP:  return "beep";
    case M_CHIRP: return "chirp";
    default:      return "off";
  }
}

// ================= Outputs =================
void publishLight() {
  if (mqtt.connected()) mqtt.publish((BASE + "/light").c_str(), lightState().c_str(), true);
}

void publishBuzzer() {
  if (mqtt.connected()) mqtt.publish((BASE + "/buzzer").c_str(), modeName(buzzerMode), true);
}

void publishPilot() {
  if (mqtt.connected()) mqtt.publish((BASE + "/pilot").c_str(), modeName(pilotMode), true);
}

// Interlock: the three lamp bits are only ever set here, one at a time.
void setLight(Light l, bool blink) {
  currentLight = l;
  lightBlink = blink && l != L_OFF;
  publishLight();
  Serial.printf("Light -> %s\n", lightState().c_str());
}

void setBuzzer(Mode m) {
  buzzerMode = m;
  buzzerStartMs = millis();
  publishBuzzer();
  Serial.printf("Buzzer -> %s\n", modeName(m));
}

void setPilot(Mode m) {
  pilotMode = m;
  publishPilot();
  Serial.printf("Pilot -> %s\n", modeName(m));
}

void enterFailsafe(const char* reason) {
  failsafe = true;
  failsafeReason = reason;
  Serial.printf("Fail-safe (%s)\n", reason);
  setLight(FAILSAFE_LIGHT, false);
  setBuzzer(M_OFF);
  setPilot(M_OFF);
}

// Turns modes into relay bits. Called every loop.
void updateOutputs(uint32_t now) {
  bool blinkPhase = (now / BLINK_MS) % 2 == 0;

  bool lampOn = !lightBlink || blinkPhase;
  uint8_t lampCh = 0xFF;
  if (currentLight == L_RED)    lampCh = RELAY_RED;
  if (currentLight == L_YELLOW) lampCh = RELAY_AMBER;
  if (currentLight == L_GREEN)  lampCh = RELAY_GREEN;
  setBit(RELAY_RED,   lampOn && lampCh == RELAY_RED);
  setBit(RELAY_AMBER, lampOn && lampCh == RELAY_AMBER);
  setBit(RELAY_GREEN, lampOn && lampCh == RELAY_GREEN);

  uint32_t bt = now - buzzerStartMs;
  if (buzzerMode == M_CHIRP && bt >= CHIRP_MS) setBuzzer(M_OFF);
  if ((buzzerMode == M_ON || buzzerMode == M_BEEP) && bt >= BUZZER_MAX_MS) setBuzzer(M_OFF);
  bool buzz = buzzerMode == M_ON || buzzerMode == M_CHIRP ||
              (buzzerMode == M_BEEP && (bt / BEEP_MS) % 2 == 0);
  setBit(RELAY_BUZZER, buzz);

  setBit(RELAY_PILOT, pilotMode == M_ON || (pilotMode == M_BLINK && blinkPhase));

  bool refresh = now - lastRefreshMs >= RELAY_REFRESH_MS;
  if (refresh) lastRefreshMs = now;
  writeRelays(refresh);
}

// On-board LED: red = no link, blue = link but no MQTT,
// green = online, amber = online but in fail-safe.
void updateStatusLed(bool netUp) {
  static uint8_t last = 0xFF;
  uint8_t s = !netUp ? 0 : !mqtt.connected() ? 1 : failsafe ? 3 : 2;
  if (s == last) return;
  last = s;
  switch (s) {
    case 0: rgbLedWrite(STATUS_LED_PIN, 24, 0, 0); break;
    case 1: rgbLedWrite(STATUS_LED_PIN, 0, 0, 24); break;
    case 2: rgbLedWrite(STATUS_LED_PIN, 0, 24, 0); break;
    case 3: rgbLedWrite(STATUS_LED_PIN, 24, 10, 0); break;
  }
}

// ================= Inputs =================
void publishInputs() {
  if (!mqtt.connected()) return;
  char buf[200];
  snprintf(buf, sizeof(buf),
           "{\"truck\":%s,\"beam\":%s,\"release\":%s,\"ack\":%s,\"maint\":%s,"
           "\"di\":[%d,%d,%d,%d,%d,%d,%d,%d]}",
           diStable[DI_TRUCK]   ? "true" : "false",
           diStable[DI_BEAM]    ? "true" : "false",
           diStable[DI_RELEASE] ? "true" : "false",
           diStable[DI_ACK]     ? "true" : "false",
           diStable[DI_MAINT]   ? "true" : "false",
           diStable[0], diStable[1], diStable[2], diStable[3],
           diStable[4], diStable[5], diStable[6], diStable[7]);
  mqtt.publish((BASE + "/inputs").c_str(), buf, true);
}

bool readActive(uint8_t pin) {
  bool level = digitalRead(pin);
  return INPUT_ACTIVE_LOW ? (level == LOW) : (level == HIGH);
}

void readInputs(uint32_t now) {
  bool changed = false;
  for (int i = 0; i < 8; i++) {
    bool a = readActive(DI_PINS[i]);
    if (a != diRaw[i]) {
      diRaw[i] = a;
      diChangeMs[i] = now;
    } else if (a != diStable[i] && now - diChangeMs[i] >= DEBOUNCE_MS) {
      diStable[i] = a;
      changed = true;
      Serial.printf("DI%d -> %d\n", i + 1, a);
    }
  }
  if (changed) publishInputs();
}

// ================= MQTT =================
bool parseMode(const String& s, Mode& m, bool allowBeep) {
  if      (s == "off")   m = M_OFF;
  else if (s == "on")    m = M_ON;
  else if (s == "blink" && !allowBeep) m = M_BLINK;
  else if (s == "beep"  && allowBeep)  m = M_BEEP;
  else if (s == "chirp" && allowBeep)  m = M_CHIRP;
  else return false;
  return true;
}

void onMessage(char* topic, byte* payload, unsigned int len) {
  String t(topic), msg;
  for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
  msg.trim();
  msg.toLowerCase();

  if (t == BASE + "/light/set") {
    bool blink = msg.endsWith("_blink");
    String c = blink ? msg.substring(0, msg.length() - 6) : msg;
    Light l;
    if      (c == "red")                     l = L_RED;
    else if (c == "yellow" || c == "amber")  l = L_YELLOW;
    else if (c == "green")                   l = L_GREEN;
    else if (c == "off" && !blink)           l = L_OFF;
    else { Serial.printf("Unknown light cmd: %s\n", msg.c_str()); return; }
    failsafe = false;
    failsafeReason = "none";
    lastCmdMs = millis();
    setLight(l, blink);
  }
  else if (t == BASE + "/buzzer/set") {
    Mode m;
    if (!parseMode(msg, m, true)) { Serial.printf("Unknown buzzer cmd: %s\n", msg.c_str()); return; }
    if (failsafe && m != M_OFF) return;   // no buzzer without the server
    setBuzzer(m);
  }
  else if (t == BASE + "/pilot/set") {
    Mode m;
    if (!parseMode(msg, m, false)) { Serial.printf("Unknown pilot cmd: %s\n", msg.c_str()); return; }
    if (failsafe && m != M_OFF) return;
    setPilot(m);
  }
  else if (strlen(SERVER_STATUS_TOPIC) && t == SERVER_STATUS_TOPIC) {
    if (msg == "offline" && !failsafe) enterFailsafe("server");
  }
}

void publishInfo() {
  if (!mqtt.connected()) return;
  char buf[256];
  snprintf(buf, sizeof(buf),
           "{\"fw\":\"%s\",\"mac\":\"%s\",\"ip\":\"%s\",\"uptime_s\":%lu,"
           "\"failsafe\":%s,\"failsafe_reason\":\"%s\",\"light\":\"%s\","
           "\"relay_ok\":%s,\"relays\":%u}",
           FW_VERSION, ETH.macAddress().c_str(), ETH.localIP().toString().c_str(),
           (unsigned long)(millis() / 1000), failsafe ? "true" : "false",
           failsafe ? failsafeReason : "none", lightState().c_str(),
           relayOk ? "true" : "false", relayMask);
  mqtt.publish((BASE + "/info").c_str(), buf);
}

void mqttConnect() {
  String clientId = String("rfidbox-") + DOOR_ID;
  String willTopic = BASE + "/status";
  Serial.print("MQTT connecting... ");
  bool ok = mqtt.connect(clientId.c_str(),
                         strlen(MQTT_USER) ? MQTT_USER : nullptr,
                         strlen(MQTT_PASS) ? MQTT_PASS : nullptr,
                         willTopic.c_str(), 1, true, "offline");
  if (!ok) { Serial.printf("failed rc=%d\n", mqtt.state()); return; }

  Serial.println("ok");
  mqtt.subscribe((BASE + "/light/set").c_str(), 1);
  mqtt.subscribe((BASE + "/buzzer/set").c_str(), 1);
  mqtt.subscribe((BASE + "/pilot/set").c_str(), 1);
  if (strlen(SERVER_STATUS_TOPIC)) mqtt.subscribe(SERVER_STATUS_TOPIC, 1);
  mqtt.publish(willTopic.c_str(), "online", true);
  publishInputs();
  publishLight();
  publishBuzzer();
  publishPilot();
  publishInfo();
  lastHeartbeatMs = millis();
}

void onNetEvent(arduino_event_id_t event) {
  switch (event) {
    case ARDUINO_EVENT_ETH_CONNECTED:    Serial.println("ETH link up"); break;
    case ARDUINO_EVENT_ETH_GOT_IP:       Serial.printf("ETH IP %s\n", ETH.localIP().toString().c_str()); break;
    case ARDUINO_EVENT_ETH_DISCONNECTED: Serial.println("ETH link down"); break;
    default: break;
  }
}

// ================= Setup / loop =================
void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.printf("\nRFID panel box %s fw %s\n", DOOR_ID, FW_VERSION);

  // Relays first, all off, so nothing lights at power-up
  Wire.begin(I2C_SDA, I2C_SCL);
  relayMask = 0;
  writeRelays(true);

  for (int i = 0; i < 8; i++) {
    pinMode(DI_PINS[i], INPUT_PULLUP);
    diRaw[i] = diStable[i] = readActive(DI_PINS[i]);
    diChangeMs[i] = 0;
  }

  enterFailsafe("boot");     // start in the safe state until the server speaks
  updateOutputs(millis());

  Network.onEvent(onNetEvent);
  ETH.begin(ETH_PHY_W5500, 1, ETH_CS, ETH_INT, ETH_RST, SPI2_HOST,
            ETH_SCK, ETH_MISO, ETH_MOSI);
  if (USE_STATIC_IP) {
    ETH.config(IPAddress(STATIC_IP), IPAddress(GATEWAY_IP),
               IPAddress(SUBNET_MASK), IPAddress(DNS_IP));
  }

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMessage);
  mqtt.setBufferSize(512);
  mqtt.setSocketTimeout(2);
  mqtt.setKeepAlive(15);

  // Reboot if the loop ever hangs
  esp_task_wdt_config_t wdt = {
    .timeout_ms = WDT_TIMEOUT_S * 1000,
    .idle_core_mask = 0,
    .trigger_panic = true,
  };
  esp_task_wdt_reconfigure(&wdt);
  esp_task_wdt_add(NULL);

  lastLinkMs = millis();
}

void loop() {
  esp_task_wdt_reset();
  uint32_t now = millis();
  readInputs(now);

  bool netUp = ETH.linkUp() && ETH.localIP() != IPAddress(0, 0, 0, 0);

  if (mqtt.connected()) {
    mqtt.loop();
    lastLinkMs = now;
    if (now - lastHeartbeatMs >= HEARTBEAT_MS) {
      lastHeartbeatMs = now;
      publishInfo();
    }
#if LIGHT_CMD_TIMEOUT_MS > 0
    if (!failsafe && now - lastCmdMs >= LIGHT_CMD_TIMEOUT_MS) enterFailsafe("timeout");
#endif
  } else {
    if (netUp && now - lastReconnectMs >= RECONNECT_MS) {
      lastReconnectMs = now;
      mqttConnect();
      now = millis();
    }
    if (!failsafe && now - lastLinkMs >= FAILSAFE_MS) enterFailsafe("broker");
  }

  updateOutputs(now);
  updateStatusLed(netUp);
}

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

#if __has_include("config.h")
#include "config.h"
#endif

#define DHTPIN 5
#define DHTTYPE DHT11
#define RELAY_PIN 26
#define RELAY_ON HIGH
#define RELAY_OFF LOW

#ifndef WIFI_SSID
#define WIFI_SSID "CONFIGURE_WIFI_SSID"
#endif

#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "CONFIGURE_WIFI_PASSWORD"
#endif

#ifndef MQTT_BROKER
#define MQTT_BROKER "broker.hivemq.com"
#endif

#ifndef MQTT_PORT
#define MQTT_PORT 1883
#endif

#ifndef MQTT_TOPIC
#define MQTT_TOPIC "granja/temperatura/esp32-granja-001"
#endif

constexpr float TEMPERATURA_LIGA = 30.0;
constexpr float TEMPERATURA_DESLIGA = 31.0;
constexpr unsigned long INTERVALO_LEITURA_MS = 60000;

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
bool lampadaLigada = false;
unsigned long ultimaLeitura = 0;

void aplicarEstadoLampada(bool ligada) {
  lampadaLigada = ligada;
  digitalWrite(RELAY_PIN, ligada ? RELAY_ON : RELAY_OFF);
}

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.printf("Conectando ao Wi-Fi %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long inicio = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nWi-Fi conectado. IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\nWi-Fi indisponível; nova tentativa em breve.");
  }
}

void reconnect() {
  if (WiFi.status() != WL_CONNECTED || client.connected()) {
    return;
  }

  String clientId = "ESP32-Granja-" + String((uint32_t)ESP.getEfuseMac(), HEX);
  if (client.connect(clientId.c_str())) {
      Serial.println("MQTT Conectado!");
  } else {
    Serial.printf("Falha MQTT, estado=%d.\n", client.state());
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  aplicarEstadoLampada(false);
  dht.begin();
  client.setServer(MQTT_BROKER, MQTT_PORT);
  conectarWiFi();
}

void loop() {
  conectarWiFi();
  reconnect();
  client.loop();

  if (millis() - ultimaLeitura < INTERVALO_LEITURA_MS) {
    delay(10);
    return;
  }
  ultimaLeitura = millis();

  float temperatura = dht.readTemperature();
  if (isnan(temperatura)) {
    Serial.println("Falha ao ler o DHT22; mantendo o último estado da lâmpada.");
    return;
  }

  if (temperatura <= TEMPERATURA_LIGA) {
    aplicarEstadoLampada(true);
  } else if (temperatura >= TEMPERATURA_DESLIGA) {
    aplicarEstadoLampada(false);
  }

  String payload = "{\"temperatura\":" + String(temperatura, 1) +
                   ",\"lampada\":" + (lampadaLigada ? "true" : "false") + "}";
  if (client.connected()) {
    client.publish(MQTT_TOPIC, payload.c_str());
  }

  Serial.printf("Temperatura: %.1f C | Lampada: %s\n", temperatura,
                lampadaLigada ? "LIGADA" : "DESLIGADA");
}
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

#define DHTPIN 15
#define DHTTYPE DHT22
#define RELAY_PIN 26

// Altere para os dados da sua rede Wi-Fi caso vá gravar em uma placa física
const char* ssid = "WIFI-IOT"; 
const char* password = "Ac5ce1ss0@IOT";
const char* mqtt_server = "broker.hivemq.com";

WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Granja_Client")) {
      Serial.println("MQTT Conectado!");
    } else {
      delay(2000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  dht.begin();
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado!");

  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float temp = dht.readTemperature();

  if (!isnan(temp)) {
    bool lampadaOn = temp < 30.0;
    digitalWrite(RELAY_PIN, lampadaOn ? HIGH : LOW);

    String payload = "{\"temperatura\":" + String(temp) + ",\"lampada\":" + (lampadaOn ? "true" : "false") + "}";
    client.publish("granja/temperatura", payload.c_str());

    Serial.print("Temperatura: "); Serial.print(temp);
    Serial.print(" °C | Lâmpada: "); Serial.println(lampadaOn ? "LIGADA" : "DESLIGADA");
  }

  delay(3000);
}
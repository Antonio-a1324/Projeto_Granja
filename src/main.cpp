// Este código é um exemplo de como usar o sensor DHT22 com um ESP32
// para monitorar a temperatura e controlar uma lâmpada (ou outro dispositivo)
// com base na temperatura lida. Ele também publica os dados de temperatura e o 
// estado da lâmpada em um broker MQTT.
#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"
// Definições de pinos e tipo do sensor DHT'
#define DHTPIN 15
#define DHTTYPE DHT22
#define RELAY_PIN 26

// Altere para os dados da sua rede Wi-Fi caso vá gravar em uma placa física
const char* ssid = "WIFI-IOT"; 
const char* password = "Ac5ce1ss0@IOT";
const char* mqtt_server = "broker.hivemq.com";
// Inicializa o cliente MQTT e o sensor DHT
WiFiClient espClient;
PubSubClient client(espClient);
DHT dht(DHTPIN, DHTTYPE);
// Função para reconectar ao broker MQTT
void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP32_Granja_Client")) {
      Serial.println("MQTT Conectado!");
    } else {
      delay(2000);
    }
  }
}
// Função de configuração inicial
void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  dht.begin();
  // Conecta-se à rede Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Conectado!");

  client.setServer(mqtt_server, 1883);
}
// Função principal do loop
void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  float temp = dht.readTemperature();
// Verifica se a leitura da temperatura foi bem-sucedida
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
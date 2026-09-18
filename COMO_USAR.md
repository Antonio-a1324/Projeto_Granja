# Controle da lampada pela temperatura

O ESP32 faz o controle automaticamente. O fluxo e:

1. O DHT11 de 3 pinos mede a temperatura no pino GPIO 5.
2. Se a temperatura for menor ou igual a 30 C, o ESP32 liga o rele.
3. Se a temperatura chegar a 31 C ou mais, o ESP32 desliga o rele.
4. O estado e a temperatura sao publicados no MQTT pela internet.
5. O Flask pode acompanhar as leituras no historico.

## Configurar o ESP32

1. Copie `include/config.h.example` para `include/config.h`.
2. Preencha `WIFI_SSID` e `WIFI_PASSWORD`.
3. Use o mesmo `MQTT_TOPIC` no ESP32 e no servidor Flask.
4. Grave o firmware com PlatformIO.

O servidor Flask usa o mesmo broker e topico por padrao. Para alterar:

```powershell
$env:MQTT_TOPIC = "granja/temperatura/meu-esp32"
python app.py
```

## Ligacao eletrica

- DHT11 de 3 pinos: VCC em 3V3, GND em GND e DATA no GPIO 5.
- Rele: VCC/GND conforme o modulo e IN no GPIO 26.
- A lampada deve passar pelos contatos COM e NO do rele.

Nunca conecte a tensao da tomada diretamente ao ESP32. Trabalhar com rede eletrica exige modulo de rele adequado, caixa isolante, disjuntor e profissional habilitado. Para testes, use uma carga de baixa tensao.

O broker publico e adequado apenas para demonstracao. Para uso real, prefira MQTT com TLS, usuario, senha e topico privado.
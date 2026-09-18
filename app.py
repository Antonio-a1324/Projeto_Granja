import os
import json

from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
from database import fetch_history, get_db_connection, record_state_change

app = Flask(__name__)

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "granja/temperatura/esp32-granja-001")


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado ao Broker! Código de retorno: {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        temp = payload.get("temperatura")
        lampada = payload.get("lampada")

        if temp is None or lampada is None:
            print("[MQTT ERROR] Mensagem ignorada: campos obrigatórios ausentes.")
            return

        temperatura = float(temp)
        estado_lampada = bool(lampada)
        mudou, minutos = record_state_change(temperatura, estado_lampada)
        if mudou:
            print(f"[MQTT -> DB] Evento salvo: Temp={temperatura}°C | Lampada={estado_lampada} | Minutos={minutos:.2f}")
        else:
            print("[MQTT] Estado sem mudança; leitura ignorada.")
    except Exception as e:
        print(f"[MQTT ERROR] Erro ao processar mensagem: {e}")


mqtt_client = None


def start_mqtt():
    global mqtt_client
    if mqtt_client is not None:
        return

    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        print("[MQTT] Cliente inicializado.")
    except Exception as e:
        print(f"[MQTT ERROR] Não foi possível conectar ao broker: {e}")


@app.route("/")
def home():
    """Renderiza a interface web principal."""
    return render_template("index.html")


@app.route("/api/historico", methods=["GET"])
def get_historico():
    """Retorna os dados cadastrados em formato JSON."""
    try:
        return jsonify(fetch_history()), 200
    except Exception as e:
        return jsonify({"erro": "Falha ao consultar banco de dados", "detalhe": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def get_status():
    """Informa o estado da integração Flask, MQTT e banco."""
    banco_ok = True
    try:
        conn = get_db_connection()
        conn.close()
    except Exception:
        banco_ok = False

    return jsonify(
        {
            "mqtt_conectado": bool(mqtt_client and mqtt_client.is_connected()),
            "mqtt_broker": MQTT_BROKER,
            "mqtt_topico": MQTT_TOPIC,
            "banco_ok": banco_ok,
        }
    )


if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
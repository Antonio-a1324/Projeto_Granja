import os
import json

from flask import Flask, render_template, jsonify, request
import paho.mqtt.client as mqtt
from database import fetch_history, get_db_connection, record_state_change

app = Flask(__name__)

MQTT_BROKER = os.environ.get("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "granja/temperatura/esp32-granja-001")
IS_SERVERLESS = bool(os.environ.get("VERCEL"))


def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado ao Broker! Código de retorno: {rc}")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        process_reading(payload, source="MQTT")
    except Exception as e:
        print(f"[MQTT ERROR] Erro ao processar mensagem: {e}")


def process_reading(payload, source="HTTP"):
    """Valida uma leitura e salva somente mudanças de estado."""
    temp = payload.get("temperatura")
    lampada = payload.get("lampada")

    if temp is None or lampada is None:
        raise ValueError("Os campos 'temperatura' e 'lampada' são obrigatórios.")

    temperatura = float(temp)
    if isinstance(lampada, str):
        lampada = lampada.strip().lower() in ("true", "1", "ligada", "on")
    estado_lampada = bool(lampada)
    mudou, minutos = record_state_change(temperatura, estado_lampada)
    return {
        "salvo": mudou,
        "temperatura": temperatura,
        "lampada": estado_lampada,
        "minutos_ligada": minutos,
        "origem": source,
    }


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


@app.route("/api/leituras", methods=["POST"])
def receber_leitura():
    """Recebe uma leitura JSON de um dispositivo ou worker HTTP."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"erro": "Envie um JSON com temperatura e lampada."}), 400

    try:
        return jsonify(process_reading(payload)), 201
    except (TypeError, ValueError) as error:
        return jsonify({"erro": str(error)}), 400
    except Exception as error:
        return jsonify({"erro": "Falha ao salvar leitura", "detalhe": str(error)}), 500


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
            "mqtt_worker_necessario": IS_SERVERLESS,
            "mqtt_broker": MQTT_BROKER,
            "mqtt_topico": MQTT_TOPIC,
            "banco_ok": banco_ok,
        }
    )


if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
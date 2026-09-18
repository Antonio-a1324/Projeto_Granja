import os
import json
import sqlite3

from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:  # pragma: no cover - fallback em ambiente sem pós-compilação
    psycopg2 = None
    RealDictCursor = None

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///granja.db")


def get_db_connection():
    """Cria uma conexão compatível com Postgres ou SQLite."""
    if DATABASE_URL.startswith("sqlite"):
        conn = sqlite3.connect("granja.db")
        conn.row_factory = sqlite3.Row
        return conn

    if psycopg2 is None:
        raise RuntimeError("psycopg2 não está disponível")

    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Cria a tabela de leituras no banco local ou no Neon."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if DATABASE_URL.startswith("sqlite"):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    temperatura REAL NOT NULL,
                    status_lampada INTEGER NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS leituras (
                    id SERIAL PRIMARY KEY,
                    temperatura FLOAT NOT NULL,
                    status_lampada BOOLEAN NOT NULL,
                    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        conn.commit()
        cur.close()
        conn.close()
        print("[DB] Tabela 'leituras' verificada/criada.")
    except Exception as e:
        print(f"[DB ERROR] Falha ao inicializar o banco: {e}")


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

        if temp is not None and lampada is not None:
            conn = get_db_connection()
            cur = conn.cursor()

            if DATABASE_URL.startswith("sqlite"):
                cur.execute(
                    "INSERT INTO leituras (temperatura, status_lampada) VALUES (?, ?);",
                    (float(temp), 1 if lampada else 0),
                )
            else:
                cur.execute(
                    "INSERT INTO leituras (temperatura, status_lampada) VALUES (%s, %s);",
                    (temp, lampada),
                )

            conn.commit()
            cur.close()
            conn.close()
            print(f"[MQTT -> DB] Leitura Salva: Temp={temp}°C | Lampada={lampada}")
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
        conn = get_db_connection()
        cur = conn.cursor()

        if DATABASE_URL.startswith("sqlite"):
            cur.execute(
                """
                SELECT id, temperatura, status_lampada,
                       strftime('%Y-%m-%d %H:%M:%S', data_hora) as data_hora
                FROM leituras
                ORDER BY id DESC
                LIMIT 50;
                """
            )
        else:
            cur.execute(
                """
                SELECT id, temperatura, status_lampada,
                       TO_CHAR(data_hora, 'YYYY-MM-DD HH24:MI:SS') as data_hora
                FROM leituras
                ORDER BY id DESC
                LIMIT 50;
                """
            )

        leituras = cur.fetchall()
        if DATABASE_URL.startswith("sqlite"):
            resultado = [dict(linha) for linha in leituras]
        else:
            resultado = [dict(linha) for linha in leituras]

        cur.close()
        conn.close()
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"erro": "Falha ao consultar banco de dados", "detalhe": str(e)}), 500


init_db()

if __name__ == "__main__":
    start_mqtt()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
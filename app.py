import os
import json
from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# String de conexão do Neon DB (Substitua pelos seus dados do Neon)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://neondb_owner:npg_qlsIZ94FdSHE@ep-flat-breeze-b43rkljs-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# --- FUNÇÕES DO BANCO DE DADOS (NEON DB) ---
def get_db_connection():
    """Cria e retorna uma conexão com o banco PostgreSQL no Neon."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    """Cria a tabela de leituras no Neon DB caso ela não exista."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id SERIAL PRIMARY KEY,
                temperatura FLOAT NOT NULL,
                status_lampada BOOLEAN NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[DB] Tabela 'leituras' verificada/criada no Neon DB.")
    except Exception as e:
        print(f"[DB ERROR] Falha ao inicializar o banco: {e}")

# --- INTEGRAÇÃO MQTT (PAHO-MQTT) ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "granja/temperatura"

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Conectado ao Broker! Código de retorno: {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        # Decodifica a mensagem JSON enviada pelo ESP32 / Wokwi
        payload = json.loads(msg.payload.decode('utf-8'))
        temp = payload.get("temperatura")
        lampada = payload.get("lampada")

        if temp is not None and lampada is not None:
            # Salva no Neon DB
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO leituras (temperatura, status_lampada) VALUES (%s, %s);",
                (temp, lampada)
            )
            conn.commit()
            cur.close()
            conn.close()
            print(f"[MQTT -> DB] Leitura Salva: Temp={temp}°C | Lampada={lampada}")
    except Exception as e:
        print(f"[MQTT ERROR] Erro ao processar mensagem: {e}")

# Inicializa o cliente MQTT e inicia a escuta em segundo plano
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"[MQTT ERROR] Não foi possível conectar ao broker: {e}")

# --- ROTAS DA API FLASK ---
@app.route('/')
def home():
    """Renderiza a interface web principal."""
    return render_template('index.html')

@app.route('/api/historico', methods=['GET'])
def get_historico():
    """Retorna os dados cadastrados no Neon DB em formato JSON."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, temperatura, status_lampada, 
                   TO_CHAR(data_hora, 'YYYY-MM-DD HH24:MI:SS') as data_hora 
            FROM leituras 
            ORDER BY id DESC 
            LIMIT 50;
        """)
        leituras = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(leituras), 200
    except Exception as e:
        return jsonify({"erro": "Falha ao consultar banco de dados", "detalhe": str(e)}), 500

# Inicializa a tabela do banco antes de rodar a aplicação localmente
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
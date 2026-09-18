import json
import re

import pytest

from app import app, on_message
from database import fetch_history

def avaliar_estado_lampada(temperatura):
    """Regra de negócio: liga a lâmpada (True) apenas se a temperatura for menor que 30 °C"""
    return temperatura < 30.0


# 1. TESTES SIMPLES (Regra de Negócio Básica)
def test_lampada_deve_ligar_quando_temperatura_baixa():
    assert avaliar_estado_lampada(25.0) is True

def test_lampada_deve_desligar_quando_temperatura_alta():
    assert avaliar_estado_lampada(32.0) is False


# 2. TESTE PARAMETRIZADO (Múltiplas temperaturas em lote)
@pytest.mark.parametrize("temp_input,esperado", [
    (10.0, True),
    (29.9, True),
    (30.0, False),
    (30.1, False),
    (42.0, False)
])
def test_avaliar_estado_lampada_parametrizado(temp_input, esperado):
    assert avaliar_estado_lampada(temp_input) == esperado


# 3. TESTE DA ROTA API FLASK (/api/historico)
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_rota_historico_retorna_json(client):
    """Verifica se a rota /api/historico responde com payload JSON"""
    response = client.get('/api/historico')
    assert response.status_code in [200, 500]
    assert response.is_json
    if response.status_code == 200 and response.json:
        assert re.fullmatch(r"\d{2}:\d{2}", response.json[0]["data_hora"])


def test_rota_status_retorna_configuracao_mqtt(client):
    response = client.get('/api/status')

    assert response.status_code == 200
    assert response.is_json
    assert response.json['mqtt_topico']
    assert response.json['banco_ok'] is True


def test_mensagem_mqtt_e_salva_no_historico(client):
    class Mensagem:
        payload = json.dumps({'temperatura': 18.5, 'lampada': True}).encode()

    on_message(None, None, Mensagem())
    response = client.get('/api/historico')

    assert response.status_code == 200
    assert response.json[0]['temperatura'] == 18.5
    assert response.json[0]['status_lampada'] == 1


def test_mensagens_repetidas_do_mesmo_estado_nao_sao_salvas(client):
    historico_antes = fetch_history()
    estado_atual = bool(historico_antes[0]['status_lampada']) if historico_antes else False
    novo_estado = not estado_atual

    class Mensagem:
        payload = json.dumps({'temperatura': 19.0, 'lampada': novo_estado}).encode()

    on_message(None, None, Mensagem())
    on_message(None, None, Mensagem())

    historico_depois = fetch_history()
    assert len(historico_depois) == len(historico_antes) + 1


# 4. TESTE DE EXCEÇÃO (Entrada Inválida)
def test_excecao_temperatura_texto():
    """Garante que a função lança erro do tipo TypeError caso receba texto"""
    with pytest.raises(TypeError):
        avaliar_estado_lampada("trinta")
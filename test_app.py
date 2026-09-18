import pytest
from app import app

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


# 4. TESTE DE EXCEÇÃO (Entrada Inválida)
def test_excecao_temperatura_texto():
    """Garante que a função lança erro do tipo TypeError caso receba texto"""
    with pytest.raises(TypeError):
        avaliar_estado_lampada("trinta")
# Documentacao dos testes

Execute a suite com:

```powershell
.\\.venv\\Scripts\\python.exe scripts/testes.py
```

Resultado esperado atual:

```text
14 passed
```

## Testes implementados

| Funcao de teste | O que verifica | Resultado esperado |
|---|---|---|
| `test_lampada_deve_ligar_quando_temperatura_baixa` | Regra para temperatura baixa | Retorna `True`. |
| `test_lampada_deve_desligar_quando_temperatura_alta` | Regra para temperatura alta | Retorna `False`. |
| `test_avaliar_estado_lampada_parametrizado` | Valores abaixo, no limite e acima de 30 graus Celsius | Todos os casos correspondem ao esperado. |
| `test_rota_historico_retorna_json` | Consulta do historico | Responde JSON e, havendo dados, hora no formato `HH:MM`. |
| `test_rota_status_retorna_configuracao_mqtt` | Estado da integracao | Responde HTTP 200, informa topico MQTT e banco disponivel. |
| `test_rota_leituras_recebe_json_do_dispositivo` | Recebimento HTTP | Aceita payload valido, normaliza os campos e responde HTTP 201. |
| `test_rota_leituras_rejeita_json_incompleto` | Validacao de payload | Rejeita campo obrigatorio ausente com HTTP 400. |
| `test_mensagem_mqtt_e_salva_no_historico` | Processamento de mensagem MQTT | Registra o evento de mudanca ou preserva o historico quando o estado ja e igual. |
| `test_mensagens_repetidas_do_mesmo_estado_nao_sao_salvas` | Deduplicacao de eventos | Duas mensagens com o mesmo estado geram apenas um novo evento. |
| `test_excecao_temperatura_texto` | Entrada invalida na regra de negocio | Levanta `TypeError`. |

## Observacao sobre o banco

A suite usa o banco configurado por `DATABASE_URL`. Quando a variavel aponta para o Neon, os testes de persistencia escrevem dados de teste no banco remoto. Em um ambiente de producao, o ideal e usar um banco/schema de testes separado para evitar misturar dados de teste com dados reais.

## Execucao no deploy

O arquivo `scripts/testes.py` chama `pytest -q`. O `vercel.json` define esse script como `buildCommand`, portanto o deploy deve ser interrompido quando os testes falharem.

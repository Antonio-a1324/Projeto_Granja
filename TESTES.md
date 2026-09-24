# Testes implementados

Execute localmente com:

```powershell
python scripts/testes.py
```

## Cobertura

| Teste | Comportamento verificado | Resultado esperado |
|---|---|---|
| `test_lampada_deve_ligar_quando_temperatura_baixa` | Temperatura baixa | Retorna `True` |
| `test_lampada_deve_desligar_quando_temperatura_alta` | Temperatura alta | Retorna `False` |
| `test_avaliar_estado_lampada_parametrizado` | Limites e valores intermediários | Todos os valores seguem a regra de 30 °C |
| `test_rota_historico_retorna_json` | Consulta do histórico | Retorna JSON e hora `HH:MM` |
| `test_rota_status_retorna_configuracao_mqtt` | Diagnóstico da integração | Retorna configuração MQTT e banco disponível |
| `test_rota_leituras_recebe_json_do_dispositivo` | Recebimento HTTP de leitura | Retorna HTTP 201 com os dados normalizados |
| `test_rota_leituras_rejeita_json_incompleto` | Validação de payload | Retorna HTTP 400 |
| `test_mensagem_mqtt_e_salva_no_historico` | Processamento MQTT | Registra o evento de mudança |
| `test_mensagens_repetidas_do_mesmo_estado_nao_sao_salvas` | Deduplicação | Não cria novo evento para o mesmo estado |
| `test_excecao_temperatura_texto` | Entrada inválida da regra | Lança `TypeError` |

O build da Vercel executa automaticamente `python scripts/testes.py`. O deploy só deve prosseguir se todos os testes passarem.
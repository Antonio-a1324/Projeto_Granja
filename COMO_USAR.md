# Controle da lampada pela temperatura

O ESP32 publica a temperatura e o estado da lampada por MQTT. O Flask recebe as mensagens, salva os eventos no banco e exibe o historico no site.

## Persistencia por evento

O sistema nao grava cada leitura repetida:

- mensagens com o mesmo estado da lampada sao ignoradas;
- ao ligar, grava a temperatura e um evento em `Ativacao`;
- ao desligar, grava a temperatura e calcula os minutos desde a ligacao em `Tempo de uso`.

O modulo [database.py](database.py) cria as tabelas `Temperatura`, `Tempo de uso` e `Ativacao`. Sem `DATABASE_URL`, o projeto usa o arquivo local `granja.db`. Para usar Neon/PostgreSQL, defina `DATABASE_URL` antes de iniciar o Flask.

O campo `TempoLigado(minutos)` e numerico, pois armazena uma duracao em minutos. No script original ele estava como `TIMESTAMP`, que representa uma data/hora.

## Executar o Flask

```powershell
C:/Users/49269418804/AppData/Local/Programs/Python/Python314/python.exe app.py
```

Abra `http://127.0.0.1:5000`. O diagnostico MQTT fica em `http://127.0.0.1:5000/api/status`.

Para enviar uma leitura por HTTP, use `POST /api/leituras` com:

```json
{
	"temperatura": 25.4,
	"lampada": true
}
```

As consultas JSON disponiveis sao `GET /api/historico` e `GET /api/status`.

## Publicar na Vercel

O projeto agora possui `api/index.py` e `vercel.json` para publicar o Flask como funcao serverless.

1. Envie o projeto para um repositorio GitHub, mantendo `.env` fora do repositorio.
2. Na Vercel, importe o repositorio.
3. Em **Settings > Environment Variables**, cadastre:

```text
DATABASE_URL= sua URL do Neon
MQTT_BROKER= broker.hivemq.com
MQTT_PORT= 1883
MQTT_TOPIC= granja/temperatura/esp32-granja-001
```

4. Faca o deploy.
5. Abra a URL gerada pela Vercel. O site ficara disponivel nela e `/api/historico` consultara o Neon.

Importante: a Vercel nao e adequada para manter um cliente MQTT conectado continuamente. O `app.py` continua recebendo MQTT quando executado localmente, mas, para receber mensagens 24 horas na nuvem, mantenha um worker MQTT separado em um computador, Raspberry Pi ou servico com processo persistente. Esse worker deve usar `record_state_change` do `database.py` ou publicar os eventos em uma API protegida.

## Checklist dos requisitos

- Projeto Flask e rota de ingestao: `app.py`, `POST /api/leituras`.
- Banco e tabelas: `database.py`, com `Temperatura`, `Tempo de uso` e `Ativacao`.
- Conexao e persistencia: `get_db_connection`, `record_state_change` e `fetch_history`.
- PyTest: `requirements.txt`.
- Cobertura documentada: `TESTES.md`, com resultado esperado de cada teste.
- Neon: `DATABASE_URL` e criacao/migracao das tabelas no PostgreSQL.
- Vercel: `api/index.py` e `vercel.json`.
- Testes no deploy: `scripts/testes.py`, chamado por `buildCommand` no `vercel.json`.
- Consultas JSON: `GET /api/historico` e `GET /api/status`.

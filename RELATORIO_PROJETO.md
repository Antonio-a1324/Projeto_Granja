Projeto: Granja Inteligente: controle automatico de lampada por temperatura

O que é: O projeto monitora a temperatura de um ambiente por meio de um ESP32 DevKit V1 e um sensor DHT11 de tres pinos. Quando a temperatura fica baixa, o ESP32 aciona um modulo rele, que pode controlar uma lampada. O dispositivo publica a temperatura e o estado da lampada por MQTT.

Uma aplicacao Flask recebe os dados MQTT, valida as mensagens e registra somente mudancas de estado no banco PostgreSQL hospedado no Neon. A interface web consulta o historico por uma API JSON. O projeto tambem possui uma entrada serverless para publicacao do site e das APIs na Vercel.

porque da escolha:

A automacao de temperatura e adequada ao contexto de uma granja porque permite controlar uma fonte de aquecimento de forma automatica, reduzindo a necessidade de verificacao manual e mantendo uma resposta simples e mensuravel.

Objetivos:

Construir um sistema IoT capaz de medir a temperatura, controlar uma lampada automaticamente e disponibilizar os eventos registrados em uma aplicacao web.

O que usamos e para que:

- Ler a temperatura no DHT11 pelo ESP32.
- Ligar o rele quando a temperatura for menor ou igual a 30 graus Celsius.
- Desligar o rele quando a temperatura atingir 31 graus Celsius ou mais.
- Publicar os dados pelo MQTT a cada 10 segundos.
- Evitar gravacoes repetidas quando o estado da lampada nao mudar.
- Calcular o tempo em que a lampada permaneceu ligada.
- Salvar os eventos no PostgreSQL/Neon.
- Disponibilizar consultas JSON e uma interface web.
- Automatizar a execucao dos testes antes do deploy.

Arquitetura do sistema

```text
DHT11 -> ESP32 -> MQTT Broker -> Flask/worker -> PostgreSQL Neon
  |        |          |              |
  |        |          |              +--> /api/historico
  |        |          |              +--> /api/status
  |        |          |              +--> interface web
  |        +--> modulo rele -> lampada
  +--> GPIO 5

Relé IN -> GPIO 26
```

Fluxo de dados:

1. O DHT11 mede a temperatura.
2. O ESP32 decide o estado da lampada usando os limites configurados.
3. O ESP32 publica um JSON no topico `granja/temperatura/esp32-granja-001`.
4. O Flask assina o topico por meio do Paho MQTT.
5. O Flask compara o estado recebido com o ultimo evento salvo.
6. Se nao houver mudanca, a mensagem e ignorada.
7. Se houver mudanca, os dados sao salvos no Neon.
8. O site consulta `GET /api/historico` e exibe os eventos.

componentes e ligações:

- ESP32 DevKit V1.
- Sensor DHT11 de tres pinos.
- Modulo rele.
- Lampada ou carga compativel com o rele.
- Rede Wi-Fi.
- Broker MQTT.

Ligacoes de baixa tensao:

DHT11 +/VCC  -> ESP32 3V3
DHT11 OUT     -> ESP32 GPIO 5
DHT11 -/GND   -> ESP32 GND

Relé IN       -> ESP32 GPIO 26
Relé GND      -> ESP32 GND
Relé VCC      -> alimentacao adequada ao modulo


A ligacao da tensao da tomada deve ser feita em caixa isolante, com rele adequado e por pessoa habilitada. A rede eletrica nao deve ser montada em protoboard nem conectada diretamente ao ESP32.

Implementacao do firmware:

O firmware esta em `src/main.cpp` e e configurado pelo arquivo local `include/config.h`. O arquivo de configuracao nao deve ser enviado ao Git.

Principais decisoes:

- DHT11 no GPIO 5.
- Rele no GPIO 26.
- Limite para ligar: 30 graus Celsius.
- Limite para desligar: 31 graus Celsius.
- Histerese entre os limites para evitar oscilacao do rele.
- Coleta e publicacao a cada 10 segundos.
- Primeira leitura realizada imediatamente apos a inicializacao.
- Reconexao Wi-Fi e MQTT sem bloquear indefinidamente o ciclo principal.

Implementacao Flask e banco:

- `app.py`: aplicacao Flask, assinante MQTT e rotas.
- `database.py`: conexao, criacao/migracao de tabelas, persistencia e consultas.
- `templates/index.html`: interface web.
- `api/index.py`: entrada WSGI para a Vercel.
- `vercel.json`: configuracao de build e roteamento.
- `scripts/testes.py`: comando de testes do build.

Rotas:

- `GET /`: carrega a interface web.
- `GET /api/historico`: retorna os eventos salvos em JSON.
- `GET /api/status`: retorna o estado do banco e configuracao MQTT.
- `POST /api/leituras`: recebe uma leitura JSON diretamente por HTTP.

Exemplo de payload:

json
{
  "temperatura": 25.4,
  "lampada": true
}


As tabelas utilizadas sao:

- `Temperatura`: temperatura e horario do evento.
- `Tempo de uso`: duracao da lampada ligada em minutos, inicio e fim.
- `Ativacao`: estado da lampada, temperatura e referencias dos registros relacionados.

O campo de duracao e numerico. Um `TIMESTAMP` representa um instante no calendario, enquanto a duracao em minutos deve ser armazenada como numero.

Persistencia somente por evento:

O ESP32 publica a cada 10 segundos, mas o banco nao grava cada mensagem. O Flask compara o novo estado com o ultimo estado em `Ativacao`.

- `False -> True`: cria evento de ligacao.
- `True -> False`: cria evento de desligamento e calcula os minutos ligados.
- `True -> True` ou `False -> False`: ignora a mensagem.

Essa estrategia reduz duplicidade no banco e preserva somente os momentos relevantes para o historico.

Testes:

Os testes estao em `test_app.py`, a documentacao detalhada esta em `TESTES.md` e o comando automatizado esta em `scripts/testes.py`.

Execucao:

```powershell
.\\.venv\\Scripts\\python.exe scripts/testes.py
```

Resultado da validacao realizada durante a construcao:

```text
14 passed
```

Os testes cobrem regra de temperatura, limites, formato de horario, rotas Flask, payload invalido, processamento MQTT e deduplicacao de mensagens.

Neon e Vercel:

O banco Neon e acessado pela variavel de ambiente `DATABASE_URL`. A URL nao deve ser colocada no codigo-fonte nem no repositorio.

A Vercel publica a interface Flask e as rotas HTTP por `api/index.py`. O build executa `python scripts/testes.py`, impedindo que uma alteracao com testes falhando seja publicada.

A Vercel nao e usada como assinante MQTT permanente. Para receber mensagens MQTT continuamente, o `app.py` precisa permanecer em execucao em um computador, Raspberry Pi ou outro servico com processo persistente. A Vercel consulta o Neon e publica as rotas web.

Fontes consultadas:

As fontes abaixo foram usadas para orientar a implementacao. Os trechos foram adaptados ao projeto e nao copiados integralmente.

1. **Flask - Quickstart e roteamento**
   - https://flask.palletsprojects.com/en/stable/quickstart/
   - Base para criacao da aplicacao, uso de `Flask`, `app.route`, metodos HTTP, templates e respostas JSON.

2. **MQTT.org - Getting started**
   - https://mqtt.org/getting-started/
   - Base conceitual para o modelo publish/subscribe e comunicacao MQTT.

3. **Paho MQTT Python**
   - https://eclipse.dev/paho/index.php?page=clients/python/docs/index.html
   - Referencia para cliente MQTT Python, callbacks, conexao, assinatura e loop de mensagens.

4. **PlatformIO - Project Configuration File**
   - https://docs.platformio.org/en/latest/projectconf/index.html
   - Referencia para `platformio.ini`, placa ESP32, framework Arduino e bibliotecas do firmware.

5. **Neon - Connect from any app**
   - https://neon.com/docs/connect/connect-from-any-app
   - Referencia para uso da string `DATABASE_URL` e conexao de aplicacoes ao PostgreSQL Neon.

6. **Vercel - Python Functions**
   - https://vercel.com/docs/functions/runtimes/python
   - Referencia para publicar uma funcao Python/WSGI e configurar variaveis de ambiente no deploy.

7. **PyTest - Getting started**
   - https://docs.pytest.org/en/stable/getting-started.html
   - Referencia para organizacao e execucao da suite de testes Python.

Participacao da equipe:

Preencher com a contribuicao real de cada integrante. Um exemplo de formato:

| Integrante | Participacao |
|---|---|
| Nome 1 | Montagem do circuito, testes do sensor e documentacao do hardware. |
| Nome 2 | Desenvolvimento do firmware ESP32, controle do rele e MQTT. |
| Nome 3 | Desenvolvimento Flask, banco Neon e APIs. |
| Nome 4 | Testes, deploy Vercel, relatorio e apresentacao. |

A equipe deve substituir os nomes e descricoes acima pela participacao efetivamente realizada por cada membro.

Entregaveis:

- Repositorio GitHub com os arquivos de codigo-fonte.
- Firmware em `src/main.cpp`.
- Configuracao PlatformIO em `platformio.ini`.
- Aplicacao Flask em `app.py`.
- Camada de banco em `database.py`.
- Testes em `test_app.py`.
- Script de testes em `scripts/testes.py`.
- Interface web em `templates/index.html`.
- Configuracao Vercel em `vercel.json` e `api/index.py`.
- Este relatorio em `RELATORIO_PROJETO.md`.
- Documentacao dos testes em `TESTES.md`.

Conclusao:

O projeto integra sensoriamento, atuacao, comunicacao IoT, persistencia em banco e visualizacao web. A separacao entre firmware, transporte MQTT, aplicacao Flask e banco facilita testes e manutencao. A persistencia por transicao evita que a coleta frequente de 10 segundos produza registros repetidos e permite calcular o tempo real de uso da lampada.

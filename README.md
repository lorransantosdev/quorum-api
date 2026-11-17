# Quorum · API

> **Milhares de pontos. Uma só usina.**

Global Solution 2026.2 · FIAP · Arquitetura Orientada a Serviços e Web Services

## Ficha da CitizenTech

| | |
|---|---|
| **Nome** | Quorum |
| **Cidade** | São Paulo – SP |
| **Cidadão beneficiado** | Pequenos e médios comércios (supermercados, academias, clínicas) e, por tabela, quem depende da rede no fim da tarde |
| **Problema em uma frase** | No fim da tarde a rede fica no limite e o comércio paga multa de ultrapassagem, enquanto baterias, carros e ar-condicionados ficam parados sem coordenação |
| **ODS** | 7 (Energia limpa e acessível), 9 (Indústria, inovação e infraestrutura), 11 (Cidades e comunidades sustentáveis), 13 (Ação contra a mudança global do clima) |

**Como funciona.** O Quorum é uma usina virtual. Cada comércio conecta o que já tem: bateria, carregador de carro elétrico, ar-condicionado, câmara fria. Perto do pico (~18h30), quando a rede pede alívio, o Quorum calcula quanto cada equipamento consegue liberar sem atrapalhar o negócio e aciona os mais flexíveis primeiro: a bateria descarrega (mantendo 20% de reserva para apagão), a recarga do carro é adiada, o ar sobe no máximo 1 °C a cada 30 min, a câmara fria segura o frio por um tempo. Somando milhares de pontos pequenos, a rede recebe potência sem ligar termelétrica. De quebra, o comércio fica abaixo da demanda contratada e não paga a multa de ultrapassagem (REN ANEEL 1.000/2021: clientes do Grupo A pagam até 3x o valor quando a demanda medida passa de 5% acima da contratada). Se o dono não quiser participar num dia específico, aperta o botão **"hoje não"**.

**O que cada parte faz.**

| Parte | Responsabilidade |
|---|---|
| API SOA (este repositório) | Regras de negócio, cadastro, medições, planejamento dos despachos, documentação OpenAPI |
| Infraestrutura Linux ([quorum-infra-linux](https://github.com/lorransantosdev/quorum-infra-linux)) | Hospeda a API e o PostgreSQL, roda as migrações e monitora o `GET /health` |
| App mobile | Consome a API: mostra a situação da demanda, alerta de ultrapassagem e o botão "hoje não" |

**Indicador de impacto.** kW de pico deslocados por despacho (`potencia_atendida_kw`) e multas evitadas (soma de `excedente_kw` que deixou de acontecer nas ultrapassagens).

**Integrantes**

| Nome | RM |
|---|---|
| Lorran | RM ‹preencher› |
| Pedro | RM ‹preencher› |
| Fabiano | RM ‹preencher› |
| Gardim | RM ‹preencher› |

> Todos os dados são **simulados**. Os comércios, CNPJs e leituras são fictícios.

## Arquitetura

Camadas, de fora para dentro. O domínio não importa nada de framework (nem FastAPI, nem SQLAlchemy).

```mermaid
flowchart TD
    C[Cliente HTTP / app mobile] --> API
    subgraph app
        API["api/<br/>rotas, DTOs pydantic, tratamento de erros"]
        APL["aplicacao/<br/>casos de uso"]
        DOM["dominio/<br/>entidades e regras (Python puro)"]
        INF["infraestrutura/<br/>SQLAlchemy, modelos ORM, repositórios"]
    end
    API --> APL
    APL --> DOM
    APL --> INF
    INF --> DB[(PostgreSQL 16)]
```

```
app/
  dominio/         cliente.py, medicao.py, equipamento.py, despacho.py, erros.py
  aplicacao/       clientes.py, equipamentos.py, medicoes.py, despachos.py, erros.py, datas.py
  infraestrutura/  db.py, modelos.py, repositorios.py
  api/             esquemas.py, rotas_*.py, erros.py
migrations/        env.py, versions/0001..0004
tests/             test_dominio.py, test_api.py, conftest.py
main.py
```

A API nunca devolve entidade ORM: toda resposta passa por um DTO de saída (`app/api/esquemas.py`).

## Regras de negócio

Todas em `app/dominio/`, testadas sem banco e sem HTTP.

1. **Demanda contratada** precisa ser maior que zero.
2. **Classificação da demanda** (`Cliente.classificar_demanda`):
   - `NORMAL`: abaixo de 90% do contratado;
   - `ATENCAO`: de 90% até 105% (inclusive);
   - `ULTRAPASSAGEM`: acima de 105% (tolerância de 5% da REN 1.000/2021).
   - `excedente_kw = max(0, demanda − contratada × 1,05)`.
3. **Medição** só aceita leituras de 0 a 10.000 kW. Valor negativo = falha do medidor.
4. **Flexibilidade por equipamento** (`Equipamento.flexibilidade_kw`):
   - Bateria: potência total se a carga estiver acima de 20% (reserva mínima para apagão), senão 0;
   - Carregador VE: potência total (a recarga é adiada);
   - Ar-condicionado: 30% da potência;
   - Câmara fria: 20% da potência;
   - Equipamento inativo: 0.
   - `carga_percentual` só existe para bateria (0 a 100).
5. **Despacho**: potência solicitada > 0 e duração entre 15 e 120 minutos.
6. **Planejamento** (`planejar`): ordena os equipamentos pela maior flexibilidade e vai acionando até chegar na potência pedida. Resultado `ATENDIDO`, `PARCIAL` ou `SEM_CAPACIDADE`. Clientes com "hoje não" (`participa_hoje = false`) ficam de fora.
7. **Remoção**: apagar um cliente apaga junto seus equipamentos e medições (`ON DELETE CASCADE`). Decidimos assim porque medição e equipamento não fazem sentido sem o cliente. A exceção é quando algum equipamento já participou de um despacho: aí a API responde **409**, para não perder o histórico da usina (a FK `acionamento.equipamento_id` é `RESTRICT`).

## Modelo de dados

```mermaid
erDiagram
    CLIENTE ||--o{ EQUIPAMENTO : possui
    CLIENTE ||--o{ MEDICAO : registra
    DESPACHO ||--o{ ACIONAMENTO : gera
    EQUIPAMENTO ||--o{ ACIONAMENTO : participa

    CLIENTE {
        int id PK
        varchar nome
        varchar segmento
        varchar cnpj UK
        varchar bairro
        float demanda_contratada_kw
        boolean participa_hoje
        timestamptz criado_em
    }
    EQUIPAMENTO {
        int id PK
        int cliente_id FK
        varchar tipo
        varchar marca
        float potencia_kw
        float carga_percentual
        boolean ativo
    }
    MEDICAO {
        int id PK
        int cliente_id FK
        timestamptz momento
        float demanda_kw
        varchar situacao
        float excedente_kw
    }
    DESPACHO {
        int id PK
        varchar descricao
        float potencia_solicitada_kw
        float potencia_atendida_kw
        timestamptz inicio
        int duracao_min
        varchar status
        timestamptz criado_em
    }
    ACIONAMENTO {
        int id PK
        int despacho_id FK
        int equipamento_id FK
        float potencia_kw
    }
```

Despacho e equipamento formam uma relação N–N através de `acionamento`. A tabela `medicao` tem índice em `(cliente_id, momento)` para as consultas por período.

### Migrações (Alembic)

| Revisão | O que faz |
|---|---|
| `0001_cria_cliente_equipamento_medicao` | Cria as tabelas iniciais |
| `0002_clientes_simulados` | Carrega 5 comércios fictícios de SP, 10 equipamentos e algumas medições |
| `0003_cria_despacho_e_acionamento` | Evolução: usina virtual (despacho N–N equipamento) |
| `0004_adiciona_participa_hoje_no_cliente` | Evolução: `ALTER TABLE` com `participa_hoje` (botão "hoje não") e `bairro` |

Todas têm `downgrade`. A aplicação não usa `create_all`; o esquema é só das migrações.

## Como rodar

Pré-requisitos: Python 3.11 ou 3.12 e Docker.

```bash
# 1. variáveis de ambiente
cp .env.example .env            # no Windows: copy .env.example .env

# 2. banco PostgreSQL 16 (porta 5433 no host)
docker compose up -d

# 3. ambiente Python
python -m venv .venv
source .venv/bin/activate       # no Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 4. migrações (cria as tabelas e carrega os dados simulados)
alembic upgrade head

# 5. API
uvicorn main:app --host 127.0.0.1 --port 8000
```

O `.env` tem `DB_PASSWORD` (usado pelo docker compose) e `DATABASE_URL` (usado pela API e pelo Alembic), no formato `postgresql+psycopg://usuario:senha@host:porta/banco`. O `.env` não vai para o Git; o modelo é o `.env.example`.

### Banco do zero

```bash
docker compose down -v && docker compose up -d && alembic upgrade head
```

Para voltar tudo: `alembic downgrade base`.

## Documentação da API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

Todo endpoint tem resumo, tag e os códigos de erro documentados. Erros sempre voltam como `{"detail": "..."}`:

| Código | Quando |
|---|---|
| 404 | Cliente, equipamento ou despacho não existe |
| 409 | CNPJ repetido, ou remoção de cliente/equipamento que já participou de despacho |
| 422 | Regra de negócio violada ou dados inválidos |
| 503 | `/health` quando o banco está fora |

## Endpoints

| Método | Rota | Tag | Descrição |
|---|---|---|---|
| GET | `/clientes?pagina=&tamanho=&segmento=` | Clientes | Lista paginada (tamanho padrão 20, máx. 100) |
| GET | `/clientes/{id}` | Clientes | Busca cliente |
| POST | `/clientes` | Clientes | Cadastra cliente (201) |
| PUT | `/clientes/{id}` | Clientes | Atualiza cliente |
| DELETE | `/clientes/{id}` | Clientes | Remove cliente (204, cascata; 409 se já participou de despacho) |
| PATCH | `/clientes/{id}/participacao` | Clientes | Botão "hoje não" |
| POST | `/clientes/{id}/equipamentos` | Equipamentos | Conecta equipamento (201) |
| GET | `/clientes/{id}/equipamentos` | Equipamentos | Lista equipamentos do cliente |
| DELETE | `/equipamentos/{id}` | Equipamentos | Remove equipamento (204) |
| GET | `/clientes/{id}/flexibilidade` | Equipamentos | kW que o cliente consegue liberar no pico |
| POST | `/clientes/{id}/medicoes` | Medições | Registra leitura e classifica (201) |
| GET | `/clientes/{id}/medicoes?de=&ate=` | Medições | Leituras do período, mais recentes primeiro |
| GET | `/medicoes/ultrapassagens?de=&ate=` | Medições | Todas as ultrapassagens do período com o nome do cliente (join) |
| POST | `/despachos` | Despachos | Cria e planeja um despacho (201) |
| GET | `/despachos` | Despachos | Lista despachos, mais recentes primeiro |
| GET | `/despachos/{id}` | Despachos | Busca despacho com os acionamentos |
| GET | `/health` | Saúde | `{"status":"ok","banco":"ok"}` ou 503 |

Datas aceitam ISO 8601 com fuso (`2026-11-18T18:30:00-03:00`). Sem fuso, consideramos horário de Brasília. As respostas sempre saem com `-03:00`.

Exemplo rápido:

```bash
curl -X POST http://localhost:8000/clientes/1/medicoes \
  -H "Content-Type: application/json" \
  -d '{"momento":"2026-11-18T18:30:00-03:00","demanda_kw":330}'
# {"id":6,"cliente_id":1,"momento":"2026-11-18T18:30:00-03:00","demanda_kw":330.0,"situacao":"ULTRAPASSAGEM","excedente_kw":15.0}
```

## Testes

```bash
pytest -v
```

- `tests/test_dominio.py`: regras de negócio puras, sem banco e sem HTTP.
- `tests/test_api.py`: testes de API com `TestClient`, conferindo status **e** corpo. Usam SQLite em memória (`StaticPool`) com `dependency_overrides` no `get_session`, então não precisam do Docker.
- Opcional: para rodar a mesma suíte num PostgreSQL de teste, defina `TEST_DATABASE_URL` (ex.: `postgresql+psycopg://quorum:senha@localhost:5433/quorum_teste`). Use um banco separado, porque as tabelas são recriadas a cada teste.

## Evidências

Saídas reais guardadas em `docs/evidencias/`:

- [`migracoes.txt`](docs/evidencias/migracoes.txt): `alembic upgrade head`, `history`, `downgrade base` e `upgrade head` de novo, mais as tabelas e os dados simulados no PostgreSQL.
- [`testes.txt`](docs/evidencias/testes.txt): saída do `pytest -v` (SQLite) e da mesma suíte contra o PostgreSQL.
- [`api.txt`](docs/evidencias/api.txt): sessão com `curl` passando por todos os endpoints, incluindo os erros 404, 409, 422 e o 503 do `/health` com o banco parado.

Prints (adicionar):

- `docs/evidencias/swagger.png`: tela do Swagger em `/docs`
- `docs/evidencias/redoc.png`: tela do ReDoc em `/redoc`
- `docs/evidencias/despacho.png`: `POST /despachos` executado pelo Swagger

![Swagger](docs/evidencias/swagger.png)

## Origem dos dados

Todos os dados são **simulados** e foram criados pela equipe para a disciplina. Os comércios (Mercado Bom Preço – Vila Mariana, Academia Movimento – Tatuapé, Clínica Vida – Lapa, Padaria Pão Dourado – Mooca, Escola Aprender – Butantã) não existem, os CNPJs são fictícios (`00.000.000/0001-0X`) e as leituras de demanda foram inventadas para mostrar os casos `NORMAL`, `ATENCAO` e `ULTRAPASSAGEM`. As regras de tolerância de 5% e da multa de ultrapassagem seguem a REN ANEEL 1.000/2021.

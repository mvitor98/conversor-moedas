# 💱 Conversor de Moedas - Desafio Técnico (Fintech / MELI)

Aplicação Web Full-Stack para conversão de moedas em tempo real, com persistência em banco de dados chave-valor (Redis), arquitetura modular em camadas (**MVC + Strategy + DAO/DTO**), taxas oficiais sincronizadas automaticamente com o Banco Central, rate limiting por IP e esteira de testes e CI/CD totalmente automatizada.

---

## 🔗 Links Principais em Produção

* **Frontend Web (Vercel):** `https://conversor-moedas-woad.vercel.app`
* **API Backend (Render):** `https://conversor-moedas-wtq2.onrender.com`
* **Documentação Interativa Swagger (OpenAPI):** `https://conversor-moedas-wtq2.onrender.com/docs`
* **Repositório GitHub:** `https://github.com/mvitor98/conversor-moedas`

---

## 🛠️ Arquitetura e Stack Tecnológica

### Architecture Blueprint (Fluxo de Dados em Produção)

```text
  [ Cliente / Navegador ]
            │
            ▼
┌──────────────────────────────────────┐
│  Frontend estático (Vercel CDN)      │
│  - HTML5 + Tailwind (CDN) + JS       │
│  - Chama a API diretamente (CORS)    │
└───────────────────────────┬──────────┘
                            │ HTTPS
                            ▼
┌──────────────────────────────────────┐
│  API (FastAPI / Uvicorn no Render)   │
│  - Controllers (Routers)             │
│  - Rate Limiting por IP (Redis)      │
│  - Domain Services & Strategy        │
│  - DAOs & DTOs (Pydantic v2)         │
│  - RateSyncService ──► PTAX (BCB)    │
└───────────────────────────┬──────────┘
                            │
                            ▼
┌──────────────────────────────────────┐
│  Redis (Upstash REST em produção /   │
│  container TCP no docker-compose)    │
└──────────────────────────────────────┘
```

Localmente (`docker compose up`), o frontend roda atrás de um Nginx que também expõe um reverse proxy `/api/ → api:8000`, útil para simular um ambiente sem CORS entre serviços do mesmo compose. Em produção, o frontend estático na Vercel chama a API do Render diretamente (CORS liberado) — não há Nginx em produção.

### Backend
* **Linguagem & Framework:** Python 3.11+ com **FastAPI**.
* **Banco de Dados:** **Redis 7** via **Upstash REST** (Produção) / Container Docker TCP (Local) — a mesma interface (`get_redis_client()`) abstrai os dois modos.
* **Padrões de Projeto Aplicados:**
  * **MVC (Model-View-Controller):** Separação estrita entre roteadores (`routers.py`), camada de negócios (`services.py`) e DTOs.
  * **Strategy Pattern:** Abstração de consulta de taxas (`RateStrategy`), isolando a regra do provedor de dados (Redis ou APIs externas).
  * **DTO / DAO:** Validação estrita via Pydantic v2 e isolamento de banco via `RedisRateDAO` e `RedisHistoryDAO`.
* **Integração externa:** `RateSyncService` + `bcb_client.py` consultam a API PTAX (Olinda) do Banco Central para obter cotações oficiais (ver seção dedicada abaixo).
* **Rate Limiting:** limitador próprio por IP (janela fixa via `INCR`/`EXPIRE` no Redis já configurado), aplicado a todas as rotas com limites diferentes por sensibilidade. Ver seção **Segurança**.
* **Boas Práticas de Código:** Segue estritamente **PEP8**, **DRY**, **KISS**, **YAGNI** e princípios **SOLID**.

### Frontend
* **Tecnologias:** HTML5 Semântico, Tailwind CSS (via CDN) e JavaScript Vanilla (ES6+) — sem build step.
* **UI:** layout responsivo (uma página, mobile-first), painel lateral (drawer) de taxas cadastradas, toasts de erro/sucesso, estados de carregamento e vazio para cada lista.
* **Infraestrutura em produção:** arquivos estáticos servidos pela CDN da Vercel.

### Qualidade e Testes
* **Testes Automatizados:** **Pytest** + **Fakeredis** (mocks em memória) cobrindo testes unitários de domínio/infraestrutura e testes E2E de API; **Jest** + **jsdom** para o frontend.
* **Linters e Formatadores:** **Black** e **Flake8**.
* **Garantia de Qualidade:** Hooks de **Pre-commit** e pipeline de **CI/CD no GitHub Actions** (`pytest` + `jest` a cada push/PR em `main`).

---

## 💹 Taxas de câmbio: fonte `manual` vs `bcb`

Cada taxa cadastrada carrega uma tag de proveniência (`fonte`) e um timestamp (`atualizado_em`, UTC, precisão de segundo), persistidos junto com o valor no Redis:

* **`bcb`** — sincronizada automaticamente com a **API PTAX (Olinda) do Banco Central do Brasil**. No startup da aplicação (e também sob demanda via `POST /taxas/sincronizar-bcb`), o sistema busca a cotação de fechamento PTAX mais recente e grava `BRL` e `USD` com essa fonte. Qualquer outra moeda coberta pelo PTAX (AUD, CAD, CHF, DKK, EUR, GBP, JPY, NOK, SEK) pode ser sincronizada individualmente via `POST /taxas/sincronizar-bcb?moeda={moeda}` — como o PTAX só cota moedas estrangeiras contra o BRL, a taxa final é calculada via cruzamento (`BRL/USD ÷ BRL/moeda`).
* **`manual`** — cadastrada via `POST /taxas/{moeda}/{valor}`, ou usada como valor de referência inicial para moedas que o PTAX não cobre (ex: **ARS**, peso argentino — o Banco Central não publica cotação oficial para essa moeda). Pode ser atualizada a qualquer momento pelo mesmo endpoint.

Falhas ao consultar o BCB (API fora do ar, sem cotação no período) nunca derrubam a aplicação: ficam registradas em log e a API continua funcionando com as taxas já existentes.

No formulário de cadastro de taxa, o frontend oferece um seletor **Manual / Buscar no BCB**: em modo BCB, basta informar a moeda e o valor é obtido automaticamente a partir do PTAX.

### Painel de taxas cadastradas e histórico de 7 dias

O botão **"Taxas"** no cabeçalho abre um painel lateral (desliza da direita) com duas abas:
* **Cadastradas** — todas as taxas atualmente em vigor (`GET /taxas`), com moeda, valor, fonte (badge) e timestamp de atualização.
* **Histórico (7 dias)** — mudanças de valor registradas nos últimos 7 dias (`GET /taxas/historico`), feed combinado de todas as moedas. Uma entrada só é criada quando o valor **realmente muda** — re-sincronizações do BCB com o mesmo valor (comuns a cada restart do servidor, frequente no plano free do Render) não geram ruído no histórico.

O cabeçalho da página também mostra a "Última atualização" global (a mais recente entre todas as moedas), derivada da mesma chamada a `GET /taxas` — sem endpoint ou estado extra no backend.

---

## 🚀 Execução Local (Docker Compose)

### Pré-requisitos
* **Docker Desktop** e **Docker Compose** instalados.

### Passo a Passo

1. **Clonar o Repositório:**
   ```bash
   git clone https://github.com/mvitor98/conversor-moedas.git
   cd conversor-moedas
   ```
2. **Subir os Containers (Frontend + API + Redis):**
   ```bash
   docker compose up --build
   ```
3. **Acessar os Serviços:**
   * **Frontend Web:** `http://localhost:3000`
   * **API Backend (Swagger):** `http://localhost:8000/docs`

---

## 🧪 Execução de Testes Automatizados

**Backend (Pytest):**
```bash
# Ativar venv e instalar dependências
pip install -r backend/requirements.txt

# Executar suíte do Pytest
pytest -v
```

**Frontend (Jest):**
```bash
cd frontend
npm install
npm test
```

Ambas as suítes também rodam automaticamente no CI (GitHub Actions) a cada push/PR em `main`.

---

## 📌 Guia de Endpoints da API

| Método | Endpoint | Descrição | Retorno Esperado |
| :--- | :--- | :--- | :--- |
| `POST` | `/taxas/{moeda}/{valor}` | Cadastra ou atualiza uma taxa em relação ao USD base (fonte `manual`) | `201 Created` |
| `GET` | `/taxas` | Lista todas as taxas cadastradas, mais recente primeiro | `200 OK` (`404` se não houver nenhuma) |
| `GET` | `/taxas/historico` | Mudanças de valor de taxa nos últimos 7 dias (feed combinado) | `200 OK` (`404` se vazio) |
| `POST` | `/taxas/sincronizar-bcb` | Sincroniza com o PTAX do Banco Central — sem `?moeda=`, atualiza BRL/USD; com `?moeda=X`, só aquela moeda | `200 OK` (`502` se o BCB estiver indisponível) |
| `GET` | `/converter/{valor}/{origem}/{destino}` | Converte um valor entre duas moedas cadastradas | `200 OK` |
| `GET` | `/conversoes` | Retorna o histórico das últimas 5 conversões | `200 OK` (`404` se vazio) |

Todas as rotas acima retornam **`429 Too Many Requests`** (com header `Retry-After`) se o limite de requisições por IP for excedido — ver **Segurança**.

---

## 🛡️ Segurança

* Nenhuma credencial ou token privado está versionado no código. Todas as variáveis de ambiente em produção são injetadas estritamente pelos painéis do Render e Upstash.
* **Rate limiting por IP** em todas as rotas, com janela fixa de 60s contada no Redis (implementação própria em `backend/api/rate_limiter.py`, reaproveitando o mesmo cliente Redis/Upstash já configurado — evita depender de uma lib que exigiria uma conexão `redis://` direta, incompatível com o modo REST usado em produção):
  * Leitura (conversão, históricos, listagens): 100 req/min.
  * Cadastro manual de taxa: 20 req/min.
  * Sincronização com o BCB: 10 req/min (protege a API externa contra uso excessivo).
  * O IP é obtido via `X-Forwarded-For` quando presente (Render fica atrás de um proxy reverso).
  * **Fail-open:** se o Redis estiver indisponível, as requisições não são bloqueadas — evita que uma falha de infraestrutura derrube a disponibilidade da API.
* Validação estrita de entrada via Pydantic v2 e handlers globais de erro padronizam toda resposta de erro no formato `{"erro": "..."}`.

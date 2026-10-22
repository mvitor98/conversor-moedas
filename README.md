# 💱 Conversor de Moedas - Desafio Técnico (Fintech / MELI)

Aplicação Web Full-Stack para conversão de moedas em tempo real, com persistência em banco de dados chave-valor (Redis), arquitetura modular em camadas (**MVC + Strategy + DAO/DTO**), Nginx Reverse Proxy e esteira de testes e CI/CD totalmente automatizada.

---

## 🔗 Links Principais em Produção

* **Frontend Web (Vercel):** `https://conversor-moedas.vercel.app`
* **API Backend (Render):** `https://conversor-moedas-wtq2.onrender.com`
* **Documentação Interativa Swagger (OpenAPI):** `https://conversor-moedas-wtq2.onrender.com/docs`
* **Repositório GitHub:** `https://github.com/mvitor98/conversor-moedas`

---

## 🛠️ Arquitetura e Stack Tecnológica

### Architecture Blueprint (Containers & Fluxo de Dados)

```text
  [ Cliente / Navegador ]
            │
            ▼ (Porta 3000)
┌──────────────────────────────────────┐
│  frontend (Nginx Alpine)             │
│  - Serve HTML5/CSS3/JS Vanilla       │
│  - Reverse Proxy: /api/ ──┐          │
└───────────────────────────┼──────────┘
                            │ (Rede Docker Interna)
                            ▼ (Porta 8000)
┌──────────────────────────────────────┐
│  api (FastAPI / Uvicorn)             │
│  - Controllers (Routers)             │
│  - Domain Services & Strategy        │
│  - DAOs & DTOs (Pydantic v2)         │
│  - RateSyncService ──► PTAX (BCB)    │
└───────────────────────────┬──────────┘
                            │ (Porta 6379)
                            ▼
┌──────────────────────────────────────┐
│  redis (Redis 7 Alpine)              │
│  - Persistência em Disco (Volume)    │
└──────────────────────────────────────┘
```

### Backend
* **Linguagem & Framework:** Python 3.11+ com **FastAPI**.
* **Banco de Dados:** **Redis 7** via **Upstash** (Produção) / Container Docker (Local).
* **Padrões de Projeto Aplicados:**
  * **MVC (Model-View-Controller):** Separação estrita entre roteadores (`routers.py`), camada de negócios (`services.py`) e visualização/DTOs.
  * **Strategy Pattern:** Abstração de consulta de taxas (`RateStrategy`), isolando a regra do provedor de dados (Redis ou APIs externas).
  * **DTO / DAO:** Validação estrita via Pydantic v2 e isolamento de banco via `RedisRateDAO` e `RedisHistoryDAO`.
* **Boas Práticas de Código:** Segue estritamente **PEP8**, **DRY**, **KISS**, **YAGNI** e princípios **SOLID**.

### Frontend
* **Tecnologias:** HTML5 Semântico, CSS3 Responsivo e JavaScript Vanilla (ES6+).
* **Infraestrutura:** Servidor **Nginx Alpine** atuando como Web Server e Proxy Reverso para rotas de API.

### Qualidade e Testes
* **Testes Automatizados:** **Pytest** + **Fakeredis** (Mocks em memória) cobrindo testes unitários de domínio e testes E2E de API.
* **Linters e Formatadores:** **Black** e **Flake8**.
* **Garantia de Qualidade:** Hooks de **Pre-commit** e pipeline de **CI/CD no GitHub Actions**.

---

## 💹 Taxas de câmbio: fonte `manual` vs `bcb`

Cada taxa cadastrada carrega uma tag de proveniência (`fonte`), persistida junto com o valor no Redis:

* **`bcb`** — sincronizada automaticamente com a **API PTAX (Olinda) do Banco Central do Brasil**. No startup da aplicação (e também sob demanda via `POST /taxas/sincronizar-bcb`), o sistema busca a cotação de fechamento PTAX mais recente para o dólar e grava `BRL` e `USD` com essa fonte.
* **`manual`** — cadastrada via `POST /taxas/{moeda}/{valor}`, ou usada como valor de referência inicial para moedas que o PTAX não cobre (ex: **ARS**, peso argentino — o Banco Central não publica cotação oficial para essa moeda). Pode ser atualizada a qualquer momento pelo mesmo endpoint.

Falhas ao consultar o BCB (API fora do ar, sem cotação no período) nunca derrubam a aplicação: ficam registradas em log e a API continua funcionando com as taxas já existentes.

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

Para executar os testes unitários e E2E via ambiente virtual local:

```bash
# Ativar venv e instalar dependências
pip install -r backend/requirements.txt

# Executar suíte do Pytest
pytest -v
```

---

## 📌 Guia de Endpoints da API

| Método | Endpoint | Descrição | Retorno Esperado |
| :--- | :--- | :--- | :--- |
| `POST` | `/taxas/{moeda}/{valor}` | Cadastra ou atualiza uma taxa em relação ao USD base (fonte `manual`) | `201 Created` |
| `POST` | `/taxas/sincronizar-bcb` | Sincroniza BRL/USD com a cotação de fechamento PTAX do Banco Central (fonte `bcb`) | `200 OK` |
| `GET` | `/converter/{valor}/{origem}/{destino}` | Converte um valor entre duas moedas cadastradas | `200 OK` |
| `GET` | `/conversoes` | Retorna o histórico das últimas 5 conversões (`404` se não houver nenhuma) | `200 OK` |

---

## 🛡️ Segurança

Nenhuma credencial ou token privado está versionado no código. Todas as variáveis de ambiente em produção são injetadas estritamente pelos painéis do Render e Upstash.

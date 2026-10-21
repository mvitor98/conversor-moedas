# 💱 Conversor de Moedas - Desafio Técnico (Fintech / MELI)

Aplicação Web Full-Stack para conversão de moedas em tempo real, com persistência em banco chave-valor (Redis), arquitetura em camadas (MVC + Strategy + DAO) e esteira de testes e CI/CD totalmente automatizada.

---

## 🔗 Links Principais de Produção

* **Frontend Web (Vercel):** \https://conversor-moedas.vercel.app\ *(Aguardando Deploy)*
* **API Backend (Render):** \https://conversor-moedas-api.onrender.com\ *(Aguardando Deploy)*
* **Documentação Interativa Swagger (OpenAPI):** \https://conversor-moedas-api.onrender.com/docs\
* **Repositório GitHub:** \https://github.com/mvitor98/conversor-moedas\

---

## 🛠️ Stack Tecnológica & Arquitetura

### Backend
* **Linguagem & Framework:** Python 3.11+ com **FastAPI**.
* **Banco de Dados:** **Redis** (Banco Chave-Valor) via **Upstash** em produção / **Docker** local.
* **Padrões de Projeto Aplicados:**
  * **MVC (Model-View-Controller):** Separação clara entre roteadores/controllers, modelos/serviços de domínio e visualização.
  * **Strategy Pattern:** Padrão abstrato (\RateStrategy\) para consulta de taxas de câmbio, permitindo plugar bancos locais ou APIs externas dinamicamente.
  * **DTO / DAO (Data Transfer Object / Data Access Object):** DTOs com Pydantic v2 para validação rigorosa de entrada/saída e DAOs (\RedisRateDAO\, \RedisHistoryDAO\) para abstração total do banco.
* **Boas Práticas de Código:** Segue estritamente **PEP8**, **DRY**, **KISS**, **YAGNI** e **SOLID**.
* **Observabilidade:** Logs estruturados centralizados via módulo \logging\.

### Frontend
* **Tecnologias:** HTML5 Semântico, CSS3 Responsivo e JavaScript Vanilla (ES6+).
* **Recursos UI:** Feedback visual com spinners de carregamento, alertas toast de erro/sucesso e atualização dinâmica de histórico e moedas.

### Testes & Qualidade
* **Framework de Testes:** **Pytest** com **Fakeredis** (Mocks de banco em memória) cobrindo testes Unitários e E2E.
* **Qualidade de Código:** **Black** (Formatação) e **Flake8** (Linter PEP8).
* **Automação:** Hooks de **Pre-commit** e pipeline de **CI/CD no GitHub Actions** (\.github/workflows/pytest.yml\).

---

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
* **Python 3.11+**
* **Docker & Docker Compose** (opcional para subir o Redis localmente)
* **Git**

### Passo a Passo

1. **Clonar o Repositório:**
   \\\ash
   git clone https://github.com/mvitor98/conversor-moedas.git
   cd conversor-moedas
   \\\

2. **Criar e Ativar o Ambiente Virtual (\env\):**
   \\\ash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   \\\

3. **Instalar Dependências e Configurar Hooks:**
   \\\ash
   pip install -r backend/requirements.txt
   pre-commit install
   \\\

4. **Configurar Variáveis de Ambiente:**
   Copie o arquivo \.env.example\ para \.env\:
   \\\ash
   cp .env.example .env
   \\\

5. **Subir a Aplicação via Docker Compose (Recomendado):**
   Suba o banco Redis e a API em container com um único comando:
   \\\ash
   docker compose up --build
   \\\
   A API estará acessível em: \http://localhost:8000\
   A documentação Swagger estará em: \http://localhost:8000/docs\

6. **Executar a API sem Docker (Modo Manual):**
   Caso já tenha um servidor Redis rodando em \localhost:6379\:
   \\\ash
   uvicorn backend.main:app --reload --port 8000
   \\\

7. **Executar o Frontend:**
   Basta abrir o arquivo \rontend/index.html\ no seu navegador de preferência.

---

## 🧪 Executando os Testes Automatizados

Para rodar a suíte completa de testes unitários e E2E sem necessidade de um banco Redis ativo (utilizando os mocks do \akeredis\):

\\\ash
pytest -v
\\\

---

## 🛡️ Segurança e Variáveis de Ambiente

> ⚠️ **Regra de Ouro:** Nenhuma credencial ou senha é mantida no repositório.
> Todas as chaves e URLs de produção (como o Redis na nuvem) são injetadas estritamente por variáveis de ambiente (\REDIS_URL\) nos painéis do Render e Upstash.

---

## 📌 Guia de Endpoints da API

* **\POST /taxas/{moeda}/{valor}\**: Cadastra ou atualiza uma taxa de câmbio (Base: 1 USD).
  * *Status:* \201 Created\ (Sucesso) | \400 Bad Request\ (Valor inválido ou <= 0).
* **\GET /converter/{valor}/{moeda_origem}/{moeda_destino}\**: Executa a conversão entre duas moedas.
  * *Status:* \200 OK\ (Sucesso) | \400 Bad Request\ (Moeda idêntica ou valor <= 0) | \404 Not Found\ (Taxa não cadastrada).
* **\GET /conversoes\**: Retorna o histórico das últimas 5 conversões realizadas.
  * *Status:* \200 OK\ (Sucesso) | \404 Not Found\ (Histórico vazio).

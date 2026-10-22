const {
  showToast,
  toggleLoading,
  executeConversion,
  executeSaveRate,
  setRateMode,
  loadHistory,
  updateCurrencySelects,
  swapCurrencies,
  syncBcbRates,
  loadRegisteredRates,
  loadRateHistory,
  openRatesPanel,
  closeRatesPanel,
  switchRatesTab,
  formatTimestamp
} = require("../script");

function emptyJsonResponse() {
  return { ok: false, status: 404, json: async () => ({ erro: "Nao encontrado" }) };
}

beforeEach(() => {
  document.body.innerHTML = `
    <div id="toast" class="toast hidden"></div>
    <p id="last-updated-global"></p>
    <input id="amount" value="" />
    <select id="origin-currency"><option value="BRL">BRL</option><option value="USD">USD</option></select>
    <select id="destination-currency"><option value="USD">USD</option><option value="BRL">BRL</option></select>
    <button id="btn-convert"><span class="btn-text">Converter</span><div id="convert-spinner" class="hidden"></div></button>
    <button id="btn-swap-currency"></button>
    <div id="convert-result" class="hidden"><h3 id="result-value"></h3><p id="rate-summary"></p></div>
    <ul id="history-list"></ul>
    <div id="history-loading" class="hidden"></div>
    <button id="btn-rate-mode-manual"></button>
    <button id="btn-rate-mode-bcb"></button>
    <p id="rate-mode-hint"></p>
    <div id="rate-value-group"></div>
    <input id="rate-currency" value="" />
    <input id="rate-value" value="" required />
    <button id="btn-save-rate"><span class="btn-text">Salvar</span><div id="rate-spinner" class="hidden"></div></button>
    <button id="btn-sync-bcb"><span id="sync-bcb-label"></span><div id="sync-bcb-spinner" class="hidden"></div></button>
    <div id="bcb-sync-result" class="hidden"></div>
    <div id="rates-panel-backdrop" class="hidden"></div>
    <aside id="rates-panel" class="translate-x-full" aria-hidden="true"></aside>
    <button id="tab-rates-current"></button>
    <button id="tab-rates-history"></button>
    <button id="tab-rates-cadastro"></button>
    <ul id="rates-current-list"></ul>
    <ul id="rates-history-list" class="hidden"></ul>
    <div id="rates-cadastro-panel" class="hidden"></div>
  `;
  global.fetch = jest.fn();
  setRateMode("manual");
});

afterEach(() => {
  jest.clearAllMocks();
});

describe("Frontend - Validação e UI", () => {
  test("Exibe toast de erro para valores fora do limite [0.01, 10^12]", async () => {
    document.getElementById("amount").value = "0.001";
    await executeConversion();

    const toast = document.getElementById("toast");
    expect(toast.textContent).toContain("entre 0,01 e 1.000.000.000.000");
    expect(toast.classList.contains("hidden")).toBe(false);
  });

  test("Executa conversao com sucesso via API Mock", async () => {
    document.getElementById("amount").value = "100";

    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ convertido: 20, moeda_destino: "USD" })
    }).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => []
    });

    await executeConversion();

    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining("/converter/100/BRL/USD"));
    expect(document.getElementById("result-value").textContent).toBe("20,00 USD");
  });

  test("Adiciona nova moeda aos selects dinamicamente", () => {
    updateCurrencySelects("EUR");
    const originOptions = Array.from(document.getElementById("origin-currency").options).map(o => o.value);
    expect(originOptions).toContain("EUR");
  });

  test("Inverte as moedas de origem e destino", () => {
    document.getElementById("origin-currency").value = "BRL";
    document.getElementById("destination-currency").value = "USD";

    swapCurrencies();

    expect(document.getElementById("origin-currency").value).toBe("USD");
    expect(document.getElementById("destination-currency").value).toBe("BRL");
  });

  test("Sincroniza taxas com o BCB com sucesso", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ mensagem: "ok", taxas: { BRL: 5.02, USD: 1.0 } })
      })
      .mockResolvedValueOnce(emptyJsonResponse());

    await syncBcbRates();

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/taxas/sincronizar-bcb"),
      { method: "POST" }
    );
    expect(document.getElementById("bcb-sync-result").classList.contains("hidden")).toBe(false);
    expect(document.getElementById("toast").classList.contains("hidden")).toBe(false);
  });

  test("Exibe toast de erro quando a sincronização com o BCB falha", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: async () => ({ erro: "BCB fora do ar" })
    });

    await syncBcbRates();

    expect(document.getElementById("toast").textContent).toBe("BCB fora do ar");
  });
});

describe("Frontend - Cadastro de taxa (manual x BCB)", () => {
  test("setRateMode('bcb') esconde o campo de valor e atualiza a dica", () => {
    setRateMode("bcb");

    expect(document.getElementById("rate-value-group").classList.contains("hidden")).toBe(true);
    expect(document.getElementById("rate-value").required).toBe(false);
    expect(document.getElementById("rate-mode-hint").textContent).toContain("PTAX");
  });

  test("setRateMode('manual') volta a exigir o campo de valor", () => {
    setRateMode("bcb");
    setRateMode("manual");

    expect(document.getElementById("rate-value-group").classList.contains("hidden")).toBe(false);
    expect(document.getElementById("rate-value").required).toBe(true);
  });

  test("executeSaveRate em modo BCB chama o endpoint de sincronização por moeda", async () => {
    setRateMode("bcb");
    document.getElementById("rate-currency").value = "eur";

    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ mensagem: "ok", taxas: { EUR: 0.92 } })
      })
      .mockResolvedValueOnce(emptyJsonResponse());

    await executeSaveRate();

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/taxas/sincronizar-bcb?moeda=EUR"),
      { method: "POST" }
    );
    expect(document.getElementById("toast").textContent).toContain("EUR");
  });

  test("executeSaveRate em modo BCB sem moeda informada mostra erro sem chamar a API", async () => {
    setRateMode("bcb");
    document.getElementById("rate-currency").value = "";

    await executeSaveRate();

    expect(global.fetch).not.toHaveBeenCalled();
    expect(document.getElementById("toast").textContent).toContain("Informe a moeda");
  });
});

describe("Frontend - Painel de taxas cadastradas", () => {
  test("formatTimestamp formata uma data ISO em pt-BR", () => {
    const formatado = formatTimestamp("2026-10-22T02:30:15+00:00");
    expect(formatado).not.toBe("—");
    expect(formatado).toMatch(/\d{2}/);
  });

  test("formatTimestamp lida com valores vazios/invalidos", () => {
    expect(formatTimestamp(null)).toBe("—");
    expect(formatTimestamp("não é uma data")).toBe("—");
  });

  test("loadRegisteredRates preenche a lista e o timestamp global", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ([
        { moeda: "BRL", taxa: 5.0, fonte: "bcb", atualizado_em: "2026-10-22T02:00:00+00:00" },
        { moeda: "ARS", taxa: 1000.0, fonte: "manual", atualizado_em: "2026-10-21T10:00:00+00:00" }
      ])
    });

    await loadRegisteredRates();

    const list = document.getElementById("rates-current-list");
    expect(list.innerHTML).toContain("BRL");
    expect(list.innerHTML).toContain("ARS");
    expect(document.getElementById("last-updated-global").textContent).toContain("Última atualização");
  });

  test("loadRegisteredRates mostra estado vazio quando não há taxas (404)", async () => {
    global.fetch.mockResolvedValueOnce(emptyJsonResponse());

    await loadRegisteredRates();

    expect(document.getElementById("rates-current-list").innerHTML).toContain("Nenhuma taxa cadastrada");
  });

  test("loadRateHistory preenche a aba de histórico", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ([
        { moeda: "EUR", taxa: 6.1, fonte: "manual", atualizado_em: "2026-10-20T08:00:00+00:00" }
      ])
    });

    await loadRateHistory();

    expect(document.getElementById("rates-history-list").innerHTML).toContain("EUR");
  });

  test("openRatesPanel e closeRatesPanel alternam a visibilidade do painel", async () => {
    global.fetch.mockResolvedValueOnce(emptyJsonResponse());

    openRatesPanel();
    expect(document.getElementById("rates-panel").classList.contains("translate-x-full")).toBe(false);
    expect(document.getElementById("rates-panel-backdrop").classList.contains("hidden")).toBe(false);

    closeRatesPanel();
    expect(document.getElementById("rates-panel").classList.contains("translate-x-full")).toBe(true);
    expect(document.getElementById("rates-panel-backdrop").classList.contains("hidden")).toBe(true);
  });

  test("switchRatesTab('history') troca a lista visível e carrega o histórico", async () => {
    global.fetch.mockResolvedValueOnce(emptyJsonResponse());

    switchRatesTab("history");

    expect(document.getElementById("rates-current-list").classList.contains("hidden")).toBe(true);
    expect(document.getElementById("rates-history-list").classList.contains("hidden")).toBe(false);
  });

  test("switchRatesTab('cadastro') exibe o formulário de cadastro sem chamar a API", () => {
    switchRatesTab("cadastro");

    expect(document.getElementById("rates-cadastro-panel").classList.contains("hidden")).toBe(false);
    expect(document.getElementById("rates-current-list").classList.contains("hidden")).toBe(true);
    expect(document.getElementById("rates-history-list").classList.contains("hidden")).toBe(true);
    expect(global.fetch).not.toHaveBeenCalled();
  });
});

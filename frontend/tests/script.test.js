const {
  showToast,
  toggleLoading,
  executeConversion,
  executeSaveRate,
  loadHistory,
  updateCurrencySelects
} = require("../script");

beforeEach(() => {
  document.body.innerHTML = `
    <div id="toast" class="toast hidden"></div>
    <input id="amount" value="" />
    <select id="origin-currency"><option value="BRL">BRL</option></select>
    <select id="destination-currency"><option value="USD">USD</option></select>
    <button id="btn-convert"><span class="btn-text">Converter</span><div id="convert-spinner" class="hidden"></div></button>
    <div id="convert-result" class="hidden"><h3 id="result-value"></h3></div>
    <ul id="history-list"></ul>
    <div id="history-loading" class="hidden"></div>
    <input id="rate-currency" value="" />
    <input id="rate-value" value="" />
    <button id="btn-save-rate"><span class="btn-text">Salvar</span><div id="rate-spinner" class="hidden"></div></button>
  `;
  global.fetch = jest.fn();
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
});

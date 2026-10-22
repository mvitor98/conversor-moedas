const isLocal = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

const API_BASE_URL = isLocal
  ? (window.location.port === "3000" ? "/api" : "http://localhost:8000")
  : "https://conversor-moedas-wtq2.onrender.com";

let currentRateMode = "manual";

const RATE_MODE_ACTIVE_CLASS = "flex-1 px-3 py-2 rounded-lg bg-zinc-950 text-white font-medium text-sm text-center transition-colors";
const RATE_MODE_INACTIVE_CLASS = "flex-1 px-3 py-2 rounded-lg text-zinc-600 hover:text-zinc-950 font-medium text-sm text-center transition-colors";
const RATES_TAB_ACTIVE_CLASS = "flex-1 py-3 text-sm font-medium text-zinc-900 border-b-2 border-zinc-900";
const RATES_TAB_INACTIVE_CLASS = "flex-1 py-3 text-sm font-medium text-zinc-500 border-b-2 border-transparent hover:text-zinc-700";

function formatCurrencyValue(val) {
  if (typeof val !== "number") return val;
  return val.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
  });
}

function formatTimestamp(isoString) {
  if (!isoString) return "—";
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return "—";
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
}

function showToast(message, type = "error") {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast ${type}`;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

function toggleLoading(btnId, spinnerId, isLoading) {
  const btn = document.getElementById(btnId);
  const spinner = document.getElementById(spinnerId);
  const btnText = btn ? btn.querySelector(".btn-text") : null;

  if (isLoading) {
    if (btn) btn.disabled = true;
    if (spinner) spinner.classList.remove("hidden");
    if (btnText) btnText.style.opacity = "0.5";
  } else {
    if (btn) btn.disabled = false;
    if (spinner) spinner.classList.add("hidden");
    if (btnText) btnText.style.opacity = "1";
  }
}

function swapCurrencies() {
  const originSelect = document.getElementById("origin-currency");
  const destSelect = document.getElementById("destination-currency");
  if (!originSelect || !destSelect) return;

  const temp = originSelect.value;
  originSelect.value = destSelect.value;
  destSelect.value = temp;
}

async function executeConversion() {
  const amountInput = document.getElementById("amount");
  const originSelect = document.getElementById("origin-currency");
  const destSelect = document.getElementById("destination-currency");
  const resultBox = document.getElementById("convert-result");
  const resultValue = document.getElementById("result-value");
  const rateSummary = document.getElementById("rate-summary");

  const amount = amountInput ? amountInput.value : "";
  const origin = originSelect ? originSelect.value : "BRL";
  const destination = destSelect ? destSelect.value : "USD";

  const parsedAmount = parseFloat(amount);
  if (!amount || isNaN(parsedAmount) || parsedAmount < 0.01 || parsedAmount > 1000000000000) {
    showToast("O valor para conversão deve estar entre 0,01 e 1.000.000.000.000 (1 trilhão).", "error");
    if (amountInput) amountInput.focus();
    return;
  }

  toggleLoading("btn-convert", "convert-spinner", true);
  if (resultBox) resultBox.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/converter/${parsedAmount}/${origin}/${destination}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao realizar a conversão.");
    }

    const formattedVal = formatCurrencyValue(data.convertido);
    if (resultValue) resultValue.textContent = `${formattedVal} ${data.moeda_destino}`;
    if (rateSummary && data.valor) {
      const taxaImplicita = data.convertido / data.valor;
      rateSummary.textContent = `1 ${data.moeda_origem} = ${formatCurrencyValue(taxaImplicita)} ${data.moeda_destino}`;
    }
    if (resultBox) resultBox.classList.remove("hidden");
    await loadHistory();
  } catch (err) {
    console.error("[Conversor Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-convert", "convert-spinner", false);
  }
}

function setRateMode(mode) {
  currentRateMode = mode;
  const manualBtn = document.getElementById("btn-rate-mode-manual");
  const bcbBtn = document.getElementById("btn-rate-mode-bcb");
  const valueGroup = document.getElementById("rate-value-group");
  const valueInput = document.getElementById("rate-value");
  const hint = document.getElementById("rate-mode-hint");
  const isManual = mode === "manual";

  if (manualBtn) manualBtn.className = isManual ? RATE_MODE_ACTIVE_CLASS : RATE_MODE_INACTIVE_CLASS;
  if (bcbBtn) bcbBtn.className = !isManual ? RATE_MODE_ACTIVE_CLASS : RATE_MODE_INACTIVE_CLASS;
  if (valueGroup) valueGroup.classList.toggle("hidden", !isManual);
  if (valueInput) valueInput.required = isManual;
  if (hint) {
    hint.textContent = isManual
      ? "Quanto vale 1 USD na moeda informada."
      : "Busca a cotação oficial do PTAX para a moeda (não cobre ARS).";
  }
}

async function executeSaveRate() {
  if (currentRateMode === "bcb") {
    return fetchRateFromBcb();
  }

  const currencyInput = document.getElementById("rate-currency");
  const rateInput = document.getElementById("rate-value");

  const currency = currencyInput ? currencyInput.value.trim().toUpperCase() : "";
  const rate = rateInput ? rateInput.value : "";
  const parsedRate = parseFloat(rate);

  if (!currency || !rate || isNaN(parsedRate) || parsedRate <= 0) {
    showToast("Preencha a moeda e um valor de taxa maior que zero.", "error");
    return;
  }

  toggleLoading("btn-save-rate", "rate-spinner", true);

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/${currency}/${parsedRate}`, { method: "POST" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao cadastrar a taxa.");
    }

    showToast(`Taxa de ${data.moeda} salva com sucesso!`, "success");
    if (currencyInput) currencyInput.value = "";
    if (rateInput) rateInput.value = "";
    updateCurrencySelects(data.moeda);
    await loadRegisteredRates();
  } catch (err) {
    console.error("[Rate Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-save-rate", "rate-spinner", false);
  }
}

async function fetchRateFromBcb() {
  const currencyInput = document.getElementById("rate-currency");
  const currency = currencyInput ? currencyInput.value.trim().toUpperCase() : "";

  if (!currency) {
    showToast("Informe a moeda para buscar no BCB.", "error");
    return;
  }

  toggleLoading("btn-save-rate", "rate-spinner", true);

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/sincronizar-bcb?moeda=${currency}`, { method: "POST" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao buscar a taxa no BCB.");
    }

    const taxa = data.taxas ? data.taxas[currency] : undefined;
    showToast(`Taxa de ${currency} atualizada via BCB: ${formatCurrencyValue(taxa)}`, "success");
    if (currencyInput) currencyInput.value = "";
    updateCurrencySelects(currency);
    await loadRegisteredRates();
  } catch (err) {
    console.error("[BCB Rate Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-save-rate", "rate-spinner", false);
  }
}

async function syncBcbRates() {
  const btn = document.getElementById("btn-sync-bcb");
  const label = document.getElementById("sync-bcb-label");
  const spinner = document.getElementById("sync-bcb-spinner");
  const resultBox = document.getElementById("bcb-sync-result");

  if (btn) btn.disabled = true;
  if (spinner) spinner.classList.remove("hidden");
  if (label) label.textContent = "Sincronizando...";
  if (resultBox) resultBox.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/sincronizar-bcb`, { method: "POST" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao sincronizar com o BCB.");
    }

    if (resultBox) {
      const taxas = Object.entries(data.taxas || {})
        .map(([moeda, taxa]) => `${moeda}: ${formatCurrencyValue(taxa)}`)
        .join(" • ");
      resultBox.textContent = taxas;
      resultBox.classList.remove("hidden");
    }
    showToast("Taxas sincronizadas com o BCB/PTAX!", "success");
    await loadRegisteredRates();
  } catch (err) {
    console.error("[BCB Sync Error]:", err);
    showToast(err.message, "error");
  } finally {
    if (btn) btn.disabled = false;
    if (spinner) spinner.classList.add("hidden");
    if (label) label.textContent = "Sincronizar agora";
  }
}

function renderRateRecord(item, options = {}) {
  const badgeClass = item.fonte === "bcb" ? "badge badge-bcb" : "badge badge-manual";
  const podeExcluir = Boolean(options.deletable) && item.fonte === "manual";
  const botaoExcluir = podeExcluir
    ? `<button type="button" class="btn-delete-rate shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors" data-moeda="${item.moeda}" aria-label="Excluir taxa de ${item.moeda}" title="Excluir taxa">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0-1 14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2L4 6h16Z"/></svg>
      </button>`
    : "";
  return `<li class="py-2.5 flex items-center justify-between gap-2">
    <div class="min-w-0">
      <div class="flex items-center gap-1.5">
        <span class="font-semibold text-slate-800">${item.moeda}</span>
        <span class="${badgeClass}">${item.fonte}</span>
      </div>
      <div class="text-xs text-slate-400 tabular-nums">${formatTimestamp(item.atualizado_em)}</div>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <span class="font-semibold text-slate-700 tabular-nums">${formatCurrencyValue(item.taxa)}</span>
      ${botaoExcluir}
    </div>
  </li>`;
}

async function loadRegisteredRates() {
  const list = document.getElementById("rates-current-list");
  const globalTimestamp = document.getElementById("last-updated-global");

  try {
    const response = await fetch(`${API_BASE_URL}/taxas`);
    const data = await response.json();

    if (response.status === 404) {
      if (list) list.innerHTML = '<li class="empty-msg">Nenhuma taxa cadastrada ainda.</li>';
      if (globalTimestamp) globalTimestamp.textContent = "";
      return;
    }

    if (!response.ok) {
      throw new Error("Erro ao carregar as taxas cadastradas.");
    }

    if (list) list.innerHTML = data.map(item => renderRateRecord(item, { deletable: true })).join("");
    data.forEach(item => updateCurrencySelects(item.moeda));

    if (globalTimestamp && data.length) {
      const maisRecente = data.reduce((acc, item) => {
        if (!item.atualizado_em) return acc;
        return !acc || item.atualizado_em > acc ? item.atualizado_em : acc;
      }, null);
      globalTimestamp.textContent = maisRecente
        ? `Última atualização: ${formatTimestamp(maisRecente)}`
        : "";
    }
  } catch (err) {
    console.error("[Rates Error]:", err);
  }
}

async function loadRateHistory() {
  const list = document.getElementById("rates-history-list");
  if (!list) return;

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/historico`);
    const data = await response.json();

    if (response.status === 404) {
      list.innerHTML = '<li class="empty-msg">Nenhuma mudança nos últimos 7 dias.</li>';
      return;
    }

    if (!response.ok) {
      throw new Error("Erro ao carregar o histórico de taxas.");
    }

    list.innerHTML = data.map(renderRateRecord).join("");
  } catch (err) {
    console.error("[Rate History Error]:", err);
  }
}

function openRatesPanel() {
  const panel = document.getElementById("rates-panel");
  const backdrop = document.getElementById("rates-panel-backdrop");
  if (panel) {
    panel.classList.remove("translate-x-full");
    panel.setAttribute("aria-hidden", "false");
  }
  if (backdrop) backdrop.classList.remove("hidden");
  loadRegisteredRates();
}

function closeRatesPanel() {
  const panel = document.getElementById("rates-panel");
  const backdrop = document.getElementById("rates-panel-backdrop");
  if (panel) {
    panel.classList.add("translate-x-full");
    panel.setAttribute("aria-hidden", "true");
  }
  if (backdrop) backdrop.classList.add("hidden");
}

function switchRatesTab(tab) {
  const panels = {
    current: document.getElementById("rates-current-list"),
    history: document.getElementById("rates-history-list"),
    cadastro: document.getElementById("rates-cadastro-panel")
  };
  const tabButtons = {
    current: document.getElementById("tab-rates-current"),
    history: document.getElementById("tab-rates-history"),
    cadastro: document.getElementById("tab-rates-cadastro")
  };

  Object.keys(panels).forEach(key => {
    const panel = panels[key];
    if (panel) panel.classList.toggle("hidden", key !== tab);
  });
  Object.keys(tabButtons).forEach(key => {
    const btn = tabButtons[key];
    if (btn) btn.className = key === tab ? RATES_TAB_ACTIVE_CLASS : RATES_TAB_INACTIVE_CLASS;
  });

  if (tab === "history") loadRateHistory();
}

async function loadHistory() {
  const historyList = document.getElementById("history-list");
  const historyLoading = document.getElementById("history-loading");
  if (!historyList) return;

  if (historyLoading) historyLoading.classList.remove("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/conversoes`);
    const data = await response.json();

    if (response.status === 404) {
      historyList.innerHTML = '<li class="empty-msg">Nenhuma conversão realizada ainda.</li>';
      return;
    }

    if (!response.ok) {
      throw new Error("Erro ao carregar o histórico.");
    }

    historyList.innerHTML = data.map(item => {
      const valFormatted = formatCurrencyValue(item.convertido);
      return `<li class="history-item">
        <span>${item.valor} <strong>${item.moeda_origem}</strong> ➔ <strong>${item.moeda_destino}</strong></span>
        <strong>${valFormatted} ${item.moeda_destino}</strong>
      </li>`;
    }).join("");
  } catch (err) {
    console.error("[History Error]:", err);
  } finally {
    if (historyLoading) historyLoading.classList.add("hidden");
  }
}

function updateCurrencySelects(newCurrency) {
  const originSelect = document.getElementById("origin-currency");
  const destSelect = document.getElementById("destination-currency");
  if (!originSelect || !destSelect) return;

  const exists = Array.from(originSelect.options).some(opt => opt.value === newCurrency);
  if (!exists) {
    originSelect.add(new Option(newCurrency, newCurrency));
    destSelect.add(new Option(newCurrency, newCurrency));
  }
}

function removeCurrencyFromSelects(currency) {
  [document.getElementById("origin-currency"), document.getElementById("destination-currency")].forEach(select => {
    if (!select) return;
    const option = Array.from(select.options).find(opt => opt.value === currency);
    if (option) select.removeChild(option);
  });
}

async function deleteRate(moeda) {
  if (!moeda) return;
  const confirmar = typeof window !== "undefined" && typeof window.confirm === "function"
    ? window.confirm(`Excluir a taxa cadastrada de ${moeda}?`)
    : true;
  if (!confirmar) return;

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/${moeda}`, { method: "DELETE" });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao excluir a taxa.");
    }

    showToast(`Taxa de ${moeda} excluída.`, "success");
    removeCurrencyFromSelects(moeda);
    await loadRegisteredRates();
  } catch (err) {
    console.error("[Delete Rate Error]:", err);
    showToast(err.message, "error");
  }
}

if (typeof window !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const btnConvert = document.getElementById("btn-convert");
    const btnSaveRate = document.getElementById("btn-save-rate");
    const btnRefreshHistory = document.getElementById("btn-refresh-history");
    const btnSwapCurrency = document.getElementById("btn-swap-currency");
    const btnSyncBcb = document.getElementById("btn-sync-bcb");
    const btnRateModeManual = document.getElementById("btn-rate-mode-manual");
    const btnRateModeBcb = document.getElementById("btn-rate-mode-bcb");
    const btnOpenRatesPanel = document.getElementById("btn-open-rates-panel");
    const btnCloseRatesPanel = document.getElementById("btn-close-rates-panel");
    const ratesPanelBackdrop = document.getElementById("rates-panel-backdrop");
    const tabRatesCurrent = document.getElementById("tab-rates-current");
    const tabRatesHistory = document.getElementById("tab-rates-history");
    const tabRatesCadastro = document.getElementById("tab-rates-cadastro");
    const btnOpenCadastroMobile = document.getElementById("btn-open-cadastro-mobile");
    const ratesCurrentList = document.getElementById("rates-current-list");

    if (btnConvert) btnConvert.addEventListener("click", executeConversion);
    if (btnSaveRate) btnSaveRate.addEventListener("click", executeSaveRate);
    if (btnRefreshHistory) btnRefreshHistory.addEventListener("click", loadHistory);
    if (btnSwapCurrency) btnSwapCurrency.addEventListener("click", swapCurrencies);
    if (btnSyncBcb) btnSyncBcb.addEventListener("click", syncBcbRates);
    if (btnRateModeManual) btnRateModeManual.addEventListener("click", () => setRateMode("manual"));
    if (btnRateModeBcb) btnRateModeBcb.addEventListener("click", () => setRateMode("bcb"));
    if (btnOpenRatesPanel) btnOpenRatesPanel.addEventListener("click", openRatesPanel);
    if (btnCloseRatesPanel) btnCloseRatesPanel.addEventListener("click", closeRatesPanel);
    if (ratesPanelBackdrop) ratesPanelBackdrop.addEventListener("click", closeRatesPanel);
    if (tabRatesCurrent) tabRatesCurrent.addEventListener("click", () => switchRatesTab("current"));
    if (tabRatesHistory) tabRatesHistory.addEventListener("click", () => switchRatesTab("history"));
    if (tabRatesCadastro) tabRatesCadastro.addEventListener("click", () => switchRatesTab("cadastro"));
    if (btnOpenCadastroMobile) {
      btnOpenCadastroMobile.addEventListener("click", () => {
        openRatesPanel();
        switchRatesTab("cadastro");
      });
    }
    if (ratesCurrentList) {
      ratesCurrentList.addEventListener("click", (e) => {
        const btn = e.target.closest(".btn-delete-rate");
        if (btn) deleteRate(btn.dataset.moeda);
      });
    }

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeRatesPanel();
    });

    loadHistory();
    loadRegisteredRates();
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    showToast,
    toggleLoading,
    executeConversion,
    executeSaveRate,
    fetchRateFromBcb,
    setRateMode,
    loadHistory,
    updateCurrencySelects,
    removeCurrencyFromSelects,
    deleteRate,
    renderRateRecord,
    swapCurrencies,
    syncBcbRates,
    loadRegisteredRates,
    loadRateHistory,
    openRatesPanel,
    closeRatesPanel,
    switchRatesTab,
    formatTimestamp,
    formatCurrencyValue,
    API_BASE_URL
  };
}

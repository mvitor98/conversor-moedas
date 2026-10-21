const isLocal = typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");

const API_BASE_URL = isLocal
  ? (window.location.port === "3000" ? "/api" : "http://localhost:8000")
  : "https://conversor-moedas-api.onrender.com";

function formatCurrencyValue(val) {
  if (typeof val !== "number") return val;
  return val.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4
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

async function executeConversion() {
  const amountInput = document.getElementById("amount");
  const originSelect = document.getElementById("origin-currency");
  const destSelect = document.getElementById("destination-currency");
  const resultBox = document.getElementById("convert-result");
  const resultValue = document.getElementById("result-value");

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
    if (resultBox) resultBox.classList.remove("hidden");
    await loadHistory();
  } catch (err) {
    console.error("[Conversor Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-convert", "convert-spinner", false);
  }
}

async function executeSaveRate() {
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
  } catch (err) {
    console.error("[Rate Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-save-rate", "rate-spinner", false);
  }
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

if (typeof window !== "undefined") {
  document.addEventListener("DOMContentLoaded", () => {
    const btnConvert = document.getElementById("btn-convert");
    const btnSaveRate = document.getElementById("btn-save-rate");
    const btnRefreshHistory = document.getElementById("btn-refresh-history");

    if (btnConvert) btnConvert.addEventListener("click", executeConversion);
    if (btnSaveRate) btnSaveRate.addEventListener("click", executeSaveRate);
    if (btnRefreshHistory) btnRefreshHistory.addEventListener("click", loadHistory);
    loadHistory();
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    showToast,
    toggleLoading,
    executeConversion,
    executeSaveRate,
    loadHistory,
    updateCurrencySelects,
    formatCurrencyValue,
    API_BASE_URL
  };
}

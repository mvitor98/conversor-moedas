// Utiliza o proxy reverso /api configurado no Nginx do Docker ou localhost local
const API_BASE_URL = window.location.port === "3000" ? "/api" : "http://localhost:8000";

console.log("[Conversor] Frontend conectado à API via:", API_BASE_URL);

// Elementos do DOM
const btnConvert = document.getElementById("btn-convert");
const btnSaveRate = document.getElementById("btn-save-rate");
const btnRefreshHistory = document.getElementById("btn-refresh-history");

const resultBox = document.getElementById("convert-result");
const resultValue = document.getElementById("result-value");
const historyList = document.getElementById("history-list");
const toast = document.getElementById("toast");

function showToast(message, type = "error") {
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

// Ação de Conversão
async function executeConversion() {
  const amountInput = document.getElementById("amount");
  const amount = amountInput ? amountInput.value : "";
  const origin = document.getElementById("origin-currency").value;
  const destination = document.getElementById("destination-currency").value;

  if (!amount || parseFloat(amount) <= 0) {
    showToast("Informe um valor maior que zero para conversão.", "error");
    if (amountInput) amountInput.focus();
    return;
  }

  console.log(`[Conversor] Executando conversão: ${amount} ${origin} -> ${destination}`);
  toggleLoading("btn-convert", "convert-spinner", true);
  resultBox.classList.add("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/converter/${amount}/${origin}/${destination}`);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao realizar a conversão.");
    }

    const formattedVal = typeof data.convertido === "number" ? data.convertido.toLocaleString("pt-BR") : data.convertido;
    resultValue.textContent = `${formattedVal} ${data.moeda_destino}`;
    resultBox.classList.remove("hidden");
    loadHistory();
  } catch (err) {
    console.error("[Conversor Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-convert", "convert-spinner", false);
  }
}

// Ação de Salvar Taxa
async function executeSaveRate() {
  const currencyInput = document.getElementById("rate-currency");
  const rateInput = document.getElementById("rate-value");

  const currency = currencyInput.value.trim().toUpperCase();
  const rate = rateInput.value;

  if (!currency || !rate || parseFloat(rate) <= 0) {
    showToast("Preencha a moeda e um valor de taxa maior que zero.", "error");
    return;
  }

  toggleLoading("btn-save-rate", "rate-spinner", true);

  try {
    const response = await fetch(`${API_BASE_URL}/taxas/${currency}/${rate}`, {
      method: "POST"
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao cadastrar a taxa.");
    }

    showToast(`Taxa de ${data.moeda} salva com sucesso!`, "success");
    currencyInput.value = "";
    rateInput.value = "";
    updateCurrencySelects(data.moeda);
  } catch (err) {
    console.error("[Rate Error]:", err);
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-save-rate", "rate-spinner", false);
  }
}

// Carregar Histórico
async function loadHistory() {
  const historyLoading = document.getElementById("history-loading");
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
      const valFormatted = typeof item.convertido === "number" ? item.convertido.toLocaleString("pt-BR") : item.convertido;
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

  const exists = Array.from(originSelect.options).some(opt => opt.value === newCurrency);
  if (!exists) {
    originSelect.add(new Option(newCurrency, newCurrency));
    destSelect.add(new Option(newCurrency, newCurrency));
  }
}

if (btnConvert) btnConvert.addEventListener("click", executeConversion);
if (btnSaveRate) btnSaveRate.addEventListener("click", executeSaveRate);
if (btnRefreshHistory) btnRefreshHistory.addEventListener("click", loadHistory);
document.addEventListener("DOMContentLoaded", loadHistory);

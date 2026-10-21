// Configuração dinâmica da URL base da API
const API_BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : "https://conversor-moedas-api.onrender.com"; // Será atualizada após o deploy na nuvem

// Elementos do DOM
const convertForm = document.getElementById("convert-form");
const rateForm = document.getElementById("rate-form");
const resultBox = document.getElementById("convert-result");
const resultValue = document.getElementById("result-value");
const historyList = document.getElementById("history-list");
const btnRefreshHistory = document.getElementById("btn-refresh-history");
const toast = document.getElementById("toast");

// Funções Utilitárias UI
function showToast(message, type = "error") {
  toast.textContent = message;
  toast.className = 	oast ;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, 4000);
}

function toggleLoading(btnId, spinnerId, isLoading) {
  const btn = document.getElementById(btnId);
  const spinner = document.getElementById(spinnerId);
  const btnText = btn.querySelector(".btn-text");

  if (isLoading) {
    btn.disabled = true;
    spinner.classList.remove("hidden");
    btnText.style.opacity = "0.5";
  } else {
    btn.disabled = false;
    spinner.classList.add("hidden");
    btnText.style.opacity = "1";
  }
}

// 1. Converter Moedas (Etapa 2)
convertForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const amount = document.getElementById("amount").value;
  const origin = document.getElementById("origin-currency").value;
  const destination = document.getElementById("destination-currency").value;

  toggleLoading("btn-convert", "convert-spinner", true);
  resultBox.classList.add("hidden");

  try {
    const response = await fetch(${API_BASE_URL}/converter///);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao realizar a conversão.");
    }

    resultValue.textContent = ${data.convertido.toLocaleString("pt-BR")} ;
    resultBox.classList.remove("hidden");
    loadHistory(); // Atualiza o histórico automaticamente
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-convert", "convert-spinner", false);
  }
});

// 2. Carregar Histórico (Etapa 3)
async function loadHistory() {
  const historyLoading = document.getElementById("history-loading");
  historyLoading.classList.remove("hidden");

  try {
    const response = await fetch(${API_BASE_URL}/conversoes);
    const data = await response.json();

    if (response.status === 404) {
      historyList.innerHTML = '<li class="empty-msg">Nenhuma conversão realizada ainda.</li>';
      return;
    }

    if (!response.ok) {
      throw new Error("Erro ao carregar o histórico.");
    }

    historyList.innerHTML = data.map(item =>
      <li class="history-item">
        <span> <strong></strong> ➔ <strong></strong></span>
        <strong> </strong>
      </li>
    ).join("");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    historyLoading.classList.add("hidden");
  }
}

// 3. Cadastrar/Atualizar Taxa (Etapa 1)
rateForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const currency = document.getElementById("rate-currency").value.trim().toUpperCase();
  const rate = document.getElementById("rate-value").value;

  toggleLoading("btn-save-rate", "rate-spinner", true);

  try {
    const response = await fetch(${API_BASE_URL}/taxas//, {
      method: "POST"
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.erro || "Erro ao cadastrar a taxa.");
    }

    showToast(Taxa de  salva com sucesso!, "success");
    rateForm.reset();
    updateCurrencySelects(data.moeda);
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    toggleLoading("btn-save-rate", "rate-spinner", false);
  }
});

// Adicionar nova moeda cadastrada aos selects da tela
function updateCurrencySelects(newCurrency) {
  const originSelect = document.getElementById("origin-currency");
  const destSelect = document.getElementById("destination-currency");

  const exists = Array.from(originSelect.options).some(opt => opt.value === newCurrency);
  if (!exists) {
    const opt1 = new Option(${newCurrency}, newCurrency);
    const opt2 = new Option(${newCurrency}, newCurrency);
    originSelect.add(opt1);
    destSelect.add(opt2);
  }
}

// Inicialização
btnRefreshHistory.addEventListener("click", loadHistory);
document.addEventListener("DOMContentLoaded", loadHistory);

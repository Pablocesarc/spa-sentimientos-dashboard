
const API_BASE_URL =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://spa-sentimientos-dashboard.onrender.com";
const AGENT_SUMMARIES_URL = `${API_BASE_URL}/api/agente/resumenes`;
const AGENT_DATABASE_URL = `${API_BASE_URL}/api/agente/base-datos?limit=200`;
const API_URL = `${API_BASE_URL}/predict`;
const BATCH_API_URL = `${API_BASE_URL}/predict-batch`;

const form = document.getElementById("sentimentForm");
const commentInput = document.getElementById("comment");
const translateInput = document.getElementById("translate");
const manualDateInput = document.getElementById("manualDate");
const analyzeBtn = document.getElementById("analyzeBtn");

const csvFileInput = document.getElementById("csvFile");
const csvColumnInput = document.getElementById("csvColumn");
const csvDateColumnInput = document.getElementById("csvDateColumn");
const csvLimitInput = document.getElementById("csvLimit");
const bulkAnalyzeBtn = document.getElementById("bulkAnalyzeBtn");
const progressWrap = document.getElementById("progressWrap");
const progressText = document.getElementById("progressText");
const progressPercent = document.getElementById("progressPercent");
const progressFill = document.getElementById("progressFill");

const resultBox = document.getElementById("result");
const sentimentLabel = document.getElementById("sentimentLabel");
const confidenceLabel = document.getElementById("confidenceLabel");
const emotionLabel = document.getElementById("emotionLabel");
const translatedText = document.getElementById("translatedText");
const interpretationText = document.getElementById("interpretationText");
const recommendationText = document.getElementById("recommendationText");

const probabilityBars = document.getElementById("probabilityBars");
const keywordList = document.getElementById("keywordList");
const modelKeywordList = document.getElementById("modelKeywordList");

const kpiTotal = document.getElementById("kpiTotal");
const kpiPositive = document.getElementById("kpiPositive");
const kpiNegative = document.getElementById("kpiNegative");
const kpiConfidence = document.getElementById("kpiConfidence");

const historyTable = document.getElementById("historyTable");
const clearDashboardBtn = document.getElementById("clearDashboardBtn");
const exportBtn = document.getElementById("exportBtn");
const reloadAgentBtn = document.getElementById("reloadAgentBtn");
const agentStatus = document.getElementById("agentStatus");
const agentContent = document.getElementById("agentContent");

const agentDate = document.getElementById("agentDate");
const agentTotal = document.getElementById("agentTotal");
const agentSatisfaction = document.getElementById("agentSatisfaction");
const agentMainTopic = document.getElementById("agentMainTopic");
const agentSummaryText = document.getElementById("agentSummaryText");

const agentPositive = document.getElementById("agentPositive");
const agentNeutral = document.getElementById("agentNeutral");
const agentNegative = document.getElementById("agentNegative");

const agentTopics = document.getElementById("agentTopics");
const agentRecommendations = document.getElementById("agentRecommendations");
const agentAlerts = document.getElementById("agentAlerts");
const agentHistoryList = document.getElementById("agentHistoryList");
const reloadDatabaseBtn = document.getElementById("reloadDatabaseBtn");
const databaseStatus = document.getElementById("databaseStatus");
const databaseContent = document.getElementById("databaseContent");
const databaseCounters = document.getElementById("databaseCounters");
const dbCommentsTable = document.getElementById("dbCommentsTable");
const dbSummariesTable = document.getElementById("dbSummariesTable");
const dbRecommendationsTable = document.getElementById("dbRecommendationsTable");
const dbAlertsTable = document.getElementById("dbAlertsTable");
const dbTopicsTable = document.getElementById("dbTopicsTable");

const HISTORY_STORAGE_KEY = "spa_sentiment_history_v4";
let history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY)) || [];

let sentimentChart = null;
let emotionChart = null;
let dailyMoodChart = null;

if (manualDateInput) {
  manualDateInput.value = getTodayDate();
}

document.querySelectorAll(".example-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    commentInput.value = btn.textContent;
  });
});

document.querySelectorAll(".tab-btn").forEach((button) => {
  button.addEventListener("click", () => {
    const tabName = button.dataset.tab;

    document.querySelectorAll(".tab-btn").forEach((item) => {
      item.classList.toggle("active", item === button);
    });

    document.querySelectorAll(".tab-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `tab-${tabName}`);
    });

    if (tabName === "agent") {
      loadAgentSummaries();
    }
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = commentInput.value.trim();
  const translate = translateInput.checked;

  if (!text) {
    alert("Escribe un comentario primero.");
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analizando...";

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text,
        translate_to_english: translate
      })
    });

    const data = await response.json();

    if (data.error) {
      alert(data.error);
      return;
    }

    data.analysis_date = manualDateInput?.value || getTodayDate();

    renderResult(data);
    addToHistory(data);
    renderDashboard();

  } catch (error) {
    console.error(error);
    alert("No se pudo conectar con la API. Revisa que FastAPI esté ejecutándose.");
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analizar";
  }
});

bulkAnalyzeBtn.addEventListener("click", async () => {
  const file = csvFileInput.files[0];

  if (!file) {
    alert("Selecciona un archivo CSV primero.");
    return;
  }

  const limit = Number(csvLimitInput.value || 50);

  if (limit < 1 || limit > 200) {
    alert("El límite debe estar entre 1 y 200 comentarios.");
    return;
  }

  bulkAnalyzeBtn.disabled = true;
  bulkAnalyzeBtn.textContent = "Procesando CSV...";
  setProgress(0, "Leyendo CSV...");

  try {
    const csvText = await readFileAsText(file);
    const rows = parseCSV(csvText);

    if (rows.length < 2) {
      alert("El CSV no tiene suficientes filas.");
      return;
    }

    const headers = rows[0].map((h) => normalizeHeader(h));
    const dataRows = rows.slice(1);

    const selectedColumn = csvColumnInput.value.trim();
    const selectedDateColumn = csvDateColumnInput.value.trim();
    const columnIndex = findCommentColumnIndex(headers, selectedColumn);
    const dateColumnIndex = findDateColumnIndex(headers, selectedDateColumn);

    if (columnIndex === -1) {
      alert("No se encontró la columna indicada. Revisa el nombre de la columna.");
      return;
    }

    const records = dataRows
      .map((row) => ({
        text: (row[columnIndex] || "").trim(),
        date: normalizeDateValue(dateColumnIndex !== -1 ? row[dateColumnIndex] : "") || getTodayDate()
      }))
      .filter((item) => item.text.length > 0)
      .slice(0, limit);

    if (records.length === 0) {
      alert("No se encontraron comentarios válidos en el CSV.");
      return;
    }

    setProgress(10, `Enviando ${records.length} comentarios...`);

    const results = await analyzeInChunks(records, 25);

    if (results.length === 0) {
      alert("No se pudo analizar ningún comentario.");
      return;
    }

    results.forEach((item) => addToHistory(item));
    renderResult(results[results.length - 1]);
    renderDashboard();

    setProgress(100, `Listo: ${results.length} comentarios analizados.`);

  } catch (error) {
    console.error(error);
    alert("Ocurrió un error procesando el CSV.");
  } finally {
    bulkAnalyzeBtn.disabled = false;
    bulkAnalyzeBtn.textContent = "Analizar CSV";
  }
});

clearDashboardBtn.addEventListener("click", () => {
  history = [];
  localStorage.removeItem(HISTORY_STORAGE_KEY);
  renderDashboard();
});

exportBtn.addEventListener("click", () => {
  exportHistoryCSV();
});
if (reloadAgentBtn) {
  reloadAgentBtn.addEventListener("click", () => {
    loadAgentSummaries();
  });
}

if (reloadDatabaseBtn) {
  reloadDatabaseBtn.addEventListener("click", () => {
    loadAgentDatabase();
  });
}

async function analyzeInChunks(records, chunkSize) {
  const allResults = [];
  const total = records.length;

  for (let i = 0; i < records.length; i += chunkSize) {
    const chunk = records.slice(i, i + chunkSize);
    const texts = chunk.map((item) => item.text);

    setProgress(
      Math.round((i / total) * 90) + 10,
      `Analizando ${Math.min(i + chunk.length, total)} de ${total}...`
    );

    const response = await fetch(BATCH_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        texts,
        translate_to_english: translateInput.checked
      })
    });

    const data = await response.json();

    if (data.error) {
      throw new Error(data.error);
    }

    data.results.forEach((result, index) => {
      allResults.push({
        ...result,
        analysis_date: chunk[index]?.date || getTodayDate()
      });
    });
  }

  return allResults;
}

function setProgress(percent, text) {
  progressWrap.classList.remove("hidden");
  progressPercent.textContent = `${percent}%`;
  progressFill.style.width = `${percent}%`;
  progressText.textContent = text;
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;

    reader.readAsText(file, "UTF-8");
  });
}

function parseCSV(text) {
  const rows = [];
  let currentRow = [];
  let currentCell = "";
  let insideQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (char === '"' && insideQuotes && nextChar === '"') {
      currentCell += '"';
      i++;
    } else if (char === '"') {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      currentRow.push(currentCell);
      currentCell = "";
    } else if ((char === "\n" || char === "\r") && !insideQuotes) {
      if (char === "\r" && nextChar === "\n") {
        i++;
      }

      currentRow.push(currentCell);

      if (currentRow.some((cell) => cell.trim() !== "")) {
        rows.push(currentRow);
      }

      currentRow = [];
      currentCell = "";
    } else {
      currentCell += char;
    }
  }

  currentRow.push(currentCell);
  if (currentRow.some((cell) => cell.trim() !== "")) {
    rows.push(currentRow);
  }

  return rows;
}

function normalizeHeader(header) {
  return String(header || "")
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function findCommentColumnIndex(headers, selectedColumn) {
  if (selectedColumn) {
    const normalizedSelected = normalizeHeader(selectedColumn);
    return headers.findIndex((h) => h === normalizedSelected);
  }

  const candidates = [
    "comentario",
    "comentarios",
    "texto",
    "text",
    "comment",
    "review",
    "resena",
    "reseña",
    "opinion",
    "opinión"
  ].map(normalizeHeader);

  for (const candidate of candidates) {
    const idx = headers.findIndex((h) => h === candidate);
    if (idx !== -1) return idx;
  }

  // Si no encuentra una columna clara, usa la primera columna.
  return 0;
}

function findDateColumnIndex(headers, selectedColumn) {
  if (selectedColumn) {
    const normalizedSelected = normalizeHeader(selectedColumn);
    return headers.findIndex((h) => h === normalizedSelected);
  }

  const candidates = [
    "fecha",
    "date",
    "dia",
    "día",
    "fecha_comentario",
    "fecha comentario",
    "created_at",
    "created",
    "timestamp"
  ].map(normalizeHeader);

  for (const candidate of candidates) {
    const idx = headers.findIndex((h) => h === candidate);
    if (idx !== -1) return idx;
  }

  return -1;
}

function getTodayDate() {
  return new Date().toISOString().slice(0, 10);
}

function normalizeDateValue(value) {
  const raw = String(value || "").trim();

  if (!raw) return "";

  const isoMatch = raw.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (isoMatch) {
    return buildISODate(isoMatch[1], isoMatch[2], isoMatch[3]);
  }

  const dayFirstMatch = raw.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
  if (dayFirstMatch) {
    return buildISODate(dayFirstMatch[3], dayFirstMatch[2], dayFirstMatch[1]);
  }

  const parsed = new Date(raw);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toISOString().slice(0, 10);
  }

  return "";
}

function buildISODate(year, month, day) {
  const yyyy = String(year).padStart(4, "0");
  const mm = String(month).padStart(2, "0");
  const dd = String(day).padStart(2, "0");
  const date = new Date(`${yyyy}-${mm}-${dd}T00:00:00`);

  if (Number.isNaN(date.getTime())) return "";

  return `${yyyy}-${mm}-${dd}`;
}

function formatDisplayDate(dateValue) {
  const normalized = normalizeDateValue(dateValue) || getTodayDate();
  const date = new Date(`${normalized}T00:00:00`);

  return date.toLocaleDateString("es-BO", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function formatShortDate(dateValue) {
  const normalized = normalizeDateValue(dateValue) || getTodayDate();
  const date = new Date(`${normalized}T00:00:00`);

  return date.toLocaleDateString("es-BO", {
    day: "2-digit",
    month: "short"
  });
}

function renderResult(data) {
  resultBox.classList.remove("hidden");

  sentimentLabel.textContent = `${getSentimentEmoji(data.sentiment)} ${data.sentiment}`;
  sentimentLabel.className = getSentimentClass(data.sentiment);

  confidenceLabel.textContent = `${Math.round(data.confidence * 100)}%`;
  emotionLabel.textContent = `${getEmotionEmoji(data.dominant_emotion)} ${data.dominant_emotion}`;

  translatedText.textContent = data.text_used_by_model;
  interpretationText.textContent = data.interpretation;
  recommendationText.textContent = data.recommendation;

  renderProbabilityBars(data.probabilities);
  renderSpanishKeywords(data.keywords_from_comment_es);
  renderModelKeywords(data.model_keywords_en);
}

function renderProbabilityBars(probabilities) {
  probabilityBars.innerHTML = "";

  Object.entries(probabilities).forEach(([label, value]) => {
    const percent = Math.round(value * 100);

    const item = document.createElement("div");
    item.className = "bar-item";

    item.innerHTML = `
      <div class="bar-meta">
        <span>${getSentimentEmoji(label)} ${label}</span>
        <span>${percent}%</span>
      </div>
      <div class="bar-track">
        <div class="bar-fill" style="width: ${percent}%"></div>
      </div>
    `;

    probabilityBars.appendChild(item);
  });
}

function renderSpanishKeywords(keywords) {
  keywordList.innerHTML = "";

  if (!keywords || keywords.length === 0) {
    keywordList.innerHTML = `<span class="chip">Sin palabras clave detectadas</span>`;
    return;
  }

  keywords.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item.word;
    keywordList.appendChild(chip);
  });
}

function renderModelKeywords(keywords) {
  modelKeywordList.innerHTML = "";

  if (!keywords || keywords.length === 0) {
    modelKeywordList.innerHTML = `<span class="chip">No disponible</span>`;
    return;
  }

  keywords.slice(0, 10).forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = item.word;
    modelKeywordList.appendChild(chip);
  });
}

function addToHistory(data) {
  const item = {
    original_text: data.original_text,
    sentiment: data.sentiment,
    dominant_emotion: data.dominant_emotion,
    confidence: data.confidence,
    probabilities: data.probabilities,
    emotion_scores: data.emotion_scores,
    keywords_from_comment_es: data.keywords_from_comment_es || [],
    analysis_date: normalizeDateValue(data.analysis_date) || getTodayDate(),
    created_at: new Date().toISOString()
  };

  history.unshift(item);
  history = history.slice(0, 500);

  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
}

function renderDashboard() {
  renderKPIs();
  renderHistoryTable();
  renderSentimentChart();
  renderEmotionChart();
  renderDailyMoodChart();
}

function renderKPIs() {
  const total = history.length;

  kpiTotal.textContent = total;

  if (total === 0) {
    kpiPositive.textContent = "0%";
    kpiNegative.textContent = "0%";
    kpiConfidence.textContent = "0%";
    return;
  }

  const positives = history.filter((item) => item.sentiment === "Positivo").length;
  const negatives = history.filter((item) => item.sentiment === "Negativo").length;
  const avgConfidence = history.reduce((acc, item) => acc + Number(item.confidence || 0), 0) / total;

  kpiPositive.textContent = `${Math.round((positives / total) * 100)}%`;
  kpiNegative.textContent = `${Math.round((negatives / total) * 100)}%`;
  kpiConfidence.textContent = `${Math.round(avgConfidence * 100)}%`;
}

function renderHistoryTable() {
  historyTable.innerHTML = "";

  if (history.length === 0) {
    historyTable.innerHTML = `
      <tr>
        <td colspan="5">Todavía no hay análisis realizados.</td>
      </tr>
    `;
    return;
  }

  history.slice(0, 50).forEach((item) => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${formatDisplayDate(item.analysis_date || item.created_at)}</td>
      <td>${escapeHtml(item.original_text)}</td>
      <td class="${getSentimentClass(item.sentiment)}">${getSentimentEmoji(item.sentiment)} ${item.sentiment}</td>
      <td>${getEmotionEmoji(item.dominant_emotion)} ${item.dominant_emotion}</td>
      <td>${Math.round(item.confidence * 100)}%</td>
    `;

    historyTable.appendChild(tr);
  });
}

function renderSentimentChart() {
  const ctx = document.getElementById("sentimentChart");

  const counts = {
    Positivo: 0,
    Neutral: 0,
    Negativo: 0
  };

  history.forEach((item) => {
    if (counts[item.sentiment] !== undefined) {
      counts[item.sentiment]++;
    }
  });

  if (sentimentChart) {
    sentimentChart.destroy();
  }

  sentimentChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: Object.keys(counts),
      datasets: [{
        label: "Cantidad",
        data: Object.values(counts)
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      }
    }
  });
}

function renderEmotionChart() {
  const ctx = document.getElementById("emotionChart");

  const counts = {};

  history.forEach((item) => {
    const emotion = item.dominant_emotion || "Neutral";
    counts[emotion] = (counts[emotion] || 0) + 1;
  });

  if (emotionChart) {
    emotionChart.destroy();
  }

  emotionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: Object.keys(counts),
      datasets: [{
        label: "Emociones",
        data: Object.values(counts)
      }]
    },
    options: {
      responsive: true
    }
  });
}

function renderDailyMoodChart() {
  const ctx = document.getElementById("dailyMoodChart");
  if (!ctx) return;

  const sentimentLabels = ["Positivo", "Neutral", "Negativo"];
  const grouped = {};

  history.forEach((item) => {
    const date = normalizeDateValue(item.analysis_date || item.created_at) || getTodayDate();

    if (!grouped[date]) {
      grouped[date] = {
        Positivo: 0,
        Neutral: 0,
        Negativo: 0
      };
    }

    if (grouped[date][item.sentiment] !== undefined) {
      grouped[date][item.sentiment]++;
    }
  });

  const dates = Object.keys(grouped).sort();
  const labels = dates.map(formatShortDate);

  const datasets = sentimentLabels.map((sentiment) => ({
    label: `${getSentimentEmoji(sentiment)} ${sentiment}`,
    data: dates.map((date) => grouped[date][sentiment] || 0)
  }));

  if (dailyMoodChart) {
    dailyMoodChart.destroy();
  }

  dailyMoodChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets
    },
    options: {
      responsive: true,
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => {
              const index = items[0]?.dataIndex ?? 0;
              return formatDisplayDate(dates[index]);
            }
          }
        }
      },
      scales: {
        x: {
          stacked: true
        },
        y: {
          stacked: true,
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      }
    }
  });
}

function exportHistoryCSV() {
  if (history.length === 0) {
    alert("No hay datos para exportar.");
    return;
  }

  const rows = [
    ["fecha", "comentario", "sentimiento", "emocion", "confianza", "palabras_clave_es", "fecha_registro"]
  ];

  history.forEach((item) => {
    const keywords = (item.keywords_from_comment_es || []).map((k) => k.word).join(" | ");

    rows.push([
      normalizeDateValue(item.analysis_date || item.created_at) || getTodayDate(),
      item.original_text,
      item.sentiment,
      item.dominant_emotion,
      `${Math.round(item.confidence * 100)}%`,
      keywords,
      item.created_at
    ]);
  });

  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = "historial_sentimientos_spa.csv";
  a.click();

  URL.revokeObjectURL(url);
}

function getSentimentEmoji(sentiment) {
  if (sentiment === "Positivo") return "😊";
  if (sentiment === "Negativo") return "😠";
  if (sentiment === "Neutral") return "😐";
  return "🤖";
}

function getEmotionEmoji(emotion) {
  const emojis = {
    Alegría: "😄",
    Tristeza: "😢",
    Enojo: "😡",
    Miedo: "😨",
    Confianza: "🤝",
    Asco: "🤢",
    Sorpresa: "😮",
    Neutral: "😐"
  };

  return emojis[emotion] || "✨";
}

function getSentimentClass(sentiment) {
  if (sentiment === "Positivo") return "sent-positive";
  if (sentiment === "Negativo") return "sent-negative";
  return "sent-neutral";
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
async function loadAgentSummaries() {
  if (!agentStatus || !agentContent) return;

  agentStatus.textContent = "Cargando resúmenes del agente...";
  agentStatus.classList.remove("hidden");
  agentContent.classList.add("hidden");

  try {
    const response = await fetch(AGENT_SUMMARIES_URL);

    if (!response.ok) {
      throw new Error("No se pudo obtener la información del agente.");
    }

    const summaries = await response.json();

    if (!Array.isArray(summaries) || summaries.length === 0) {
      agentStatus.textContent = "Todavía no hay resúmenes generados por el agente.";
      return;
    }

    renderAgentSummary(summaries[0]);
    renderAgentHistory(summaries);

    agentStatus.classList.add("hidden");
    agentContent.classList.remove("hidden");

    loadAgentDatabase();

  } catch (error) {
    console.error(error);
    agentStatus.textContent = "No se pudo cargar el agente. Verifica que el backend esté activo en Render.";
  }
}

async function renderAgentSummary(summary) {
  agentDate.textContent = formatDisplayDate(summary.fecha);
  agentTotal.textContent = summary.total_comentarios ?? 0;
  agentSatisfaction.textContent = `${Math.round(Number(summary.nivel_satisfaccion || 0))}%`;
  agentMainTopic.textContent = summary.tema_principal || "-";

  agentSummaryText.textContent = summary.resumen || "Resumen no disponible.";

  agentPositive.textContent = summary.positivos ?? 0;
  agentNeutral.textContent = summary.neutrales ?? 0;
  agentNegative.textContent = summary.negativos ?? 0;

  agentTopics.innerHTML = `<span class="chip">Cargando temas...</span>`;
  agentRecommendations.innerHTML = `<li>Cargando recomendaciones...</li>`;
  agentAlerts.innerHTML = `<li>Cargando alertas...</li>`;

  try {
    const response = await fetch(`${AGENT_SUMMARIES_URL}/${summary.id}`);

    if (!response.ok) {
      throw new Error("No se pudo obtener el detalle del resumen.");
    }

    const detail = await response.json();

    renderAgentTopics(detail.temas_frecuentes || []);
    renderAgentRecommendations(detail.recomendaciones || []);
    renderAgentAlerts(detail.alertas || []);

  } catch (error) {
    console.error(error);
    agentTopics.innerHTML = `<span class="chip">No disponible</span>`;
    agentRecommendations.innerHTML = `<li>No se pudieron cargar las recomendaciones.</li>`;
    agentAlerts.innerHTML = `<li>No se pudieron cargar las alertas.</li>`;
  }
}

function renderAgentTopics(topics) {
  agentTopics.innerHTML = "";

  if (!topics || topics.length === 0) {
    agentTopics.innerHTML = `<span class="chip">Sin temas frecuentes</span>`;
    return;
  }

  topics.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${item.tema} (${item.cantidad})`;
    agentTopics.appendChild(chip);
  });
}

function renderAgentRecommendations(recommendations) {
  agentRecommendations.innerHTML = "";

  if (!recommendations || recommendations.length === 0) {
    agentRecommendations.innerHTML = `<li>Sin recomendaciones registradas.</li>`;
    return;
  }

  recommendations.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${escapeHtml(item.prioridad || "media").toUpperCase()}</strong> -
      ${escapeHtml(item.descripcion || "")}
    `;
    agentRecommendations.appendChild(li);
  });
}

function renderAgentAlerts(alerts) {
  agentAlerts.innerHTML = "";

  if (!alerts || alerts.length === 0) {
    agentAlerts.innerHTML = `<li>Sin alertas activas.</li>`;
    return;
  }

  alerts.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${escapeHtml(item.nivel || "medio").toUpperCase()}</strong> -
      ${escapeHtml(item.mensaje || "")}
    `;
    agentAlerts.appendChild(li);
  });
}

function renderAgentHistory(summaries) {
  agentHistoryList.innerHTML = "";

  summaries.slice(0, 8).forEach((item) => {
    const div = document.createElement("div");
    div.className = "agent-history-item";

    div.innerHTML = `
      <div>
        <strong>${formatDisplayDate(item.fecha)}</strong>
        <p>${escapeHtml(item.resumen || "Sin resumen.")}</p>
      </div>
      <span>${Math.round(Number(item.nivel_satisfaccion || 0))}%</span>
    `;

    agentHistoryList.appendChild(div);
  });
}

async function loadAgentDatabase() {
  if (!databaseStatus || !databaseContent) return;

  databaseStatus.textContent = "Cargando base de datos del agente...";
  databaseStatus.classList.remove("hidden");
  databaseContent.classList.add("hidden");

  try {
    const response = await fetch(AGENT_DATABASE_URL);

    if (!response.ok) {
      throw new Error("No se pudo obtener la base de datos del agente.");
    }

    const data = await response.json();

    renderDatabaseCounters(data.conteos || {});
    renderDbComments(data.comentarios || []);
    renderDbSummaries(data.resumenes_diarios || []);
    renderDbRecommendations(data.recomendaciones || []);
    renderDbAlerts(data.alertas || []);
    renderDbTopics(data.temas_frecuentes || []);

    databaseStatus.classList.add("hidden");
    databaseContent.classList.remove("hidden");
  } catch (error) {
    console.error(error);
    databaseStatus.textContent = "No se pudo cargar la base de datos. Verifica el endpoint /api/agente/base-datos en Render.";
  }
}

function renderDatabaseCounters(counts) {
  if (!databaseCounters) return;

  const items = [
    ["Comentarios", counts.comentarios || 0],
    ["Resúmenes", counts.resumenes_diarios || 0],
    ["Recomendaciones", counts.recomendaciones || 0],
    ["Alertas", counts.alertas || 0],
    ["Temas", counts.temas_frecuentes || 0]
  ];

  databaseCounters.innerHTML = items.map(([label, value]) => `
    <div class="kpi">
      <span>${label}</span>
      <strong>${value}</strong>
    </div>
  `).join("");
}

function renderDbComments(comments) {
  if (!dbCommentsTable) return;

  if (!comments.length) {
    dbCommentsTable.innerHTML = `<tr><td colspan="6">No hay comentarios guardados.</td></tr>`;
    return;
  }

  dbCommentsTable.innerHTML = comments.map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${formatDisplayDate(item.fecha)}</td>
      <td>${escapeHtml(shortText(item.texto, 120))}</td>
      <td class="${getSentimentClass(item.sentimiento)}">${getSentimentEmoji(item.sentimiento)} ${escapeHtml(item.sentimiento || "-")}</td>
      <td>${getEmotionEmoji(item.emocion)} ${escapeHtml(item.emocion || "-")}</td>
      <td>${formatPercent(item.confianza)}</td>
    </tr>
  `).join("");
}

function renderDbSummaries(summaries) {
  if (!dbSummariesTable) return;

  if (!summaries.length) {
    dbSummariesTable.innerHTML = `<tr><td colspan="8">No hay resúmenes guardados.</td></tr>`;
    return;
  }

  dbSummariesTable.innerHTML = summaries.map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${formatDisplayDate(item.fecha)}</td>
      <td>${item.total_comentarios ?? 0}</td>
      <td>${item.positivos ?? 0}</td>
      <td>${item.neutrales ?? 0}</td>
      <td>${item.negativos ?? 0}</td>
      <td>${Math.round(Number(item.nivel_satisfaccion || 0))}%</td>
      <td>${escapeHtml(shortText(item.resumen, 140))}</td>
    </tr>
  `).join("");
}

function renderDbRecommendations(recommendations) {
  if (!dbRecommendationsTable) return;

  if (!recommendations.length) {
    dbRecommendationsTable.innerHTML = `<tr><td colspan="5">No hay recomendaciones guardadas.</td></tr>`;
    return;
  }

  dbRecommendationsTable.innerHTML = recommendations.map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${item.resumen_id}</td>
      <td>${escapeHtml(item.tipo || "-")}</td>
      <td>${escapeHtml(item.prioridad || "media")}</td>
      <td>${escapeHtml(shortText(item.descripcion, 160))}</td>
    </tr>
  `).join("");
}

function renderDbAlerts(alerts) {
  if (!dbAlertsTable) return;

  if (!alerts.length) {
    dbAlertsTable.innerHTML = `<tr><td colspan="6">No hay alertas guardadas.</td></tr>`;
    return;
  }

  dbAlertsTable.innerHTML = alerts.map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${item.resumen_id}</td>
      <td>${escapeHtml(item.tipo || "-")}</td>
      <td>${escapeHtml(item.nivel || "medio")}</td>
      <td>${item.activa ? "Sí" : "No"}</td>
      <td>${escapeHtml(shortText(item.mensaje, 160))}</td>
    </tr>
  `).join("");
}

function renderDbTopics(topics) {
  if (!dbTopicsTable) return;

  if (!topics.length) {
    dbTopicsTable.innerHTML = `<tr><td colspan="5">No hay temas frecuentes guardados.</td></tr>`;
    return;
  }

  dbTopicsTable.innerHTML = topics.map((item) => `
    <tr>
      <td>${item.id}</td>
      <td>${item.resumen_id}</td>
      <td>${escapeHtml(item.tema || "-")}</td>
      <td>${item.cantidad ?? 0}</td>
      <td>${escapeHtml(item.sentimiento_asociado || "-")}</td>
    </tr>
  `).join("");
}

function shortText(text, maxLength = 120) {
  const value = String(text || "").trim();
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}...`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (Number.isNaN(number)) return "-";
  return number <= 1 ? `${Math.round(number * 100)}%` : `${Math.round(number)}%`;
}

renderDashboard();
loadAgentSummaries(); 
const resultados = document.getElementById("resultados");
const searchForm = document.getElementById("search-form");
const airportInputs = Array.from(
  document.querySelectorAll(".autocomplete-group input"),
);
const suggestionRequests = new Map();
const suggestionState = new Map();

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  buscar();
});

airportInputs.forEach((input) => {
  const panel = input.parentElement.querySelector(".suggestions-panel");
  suggestionState.set(input.id, { items: [], activeIndex: -1, panel });

  input.addEventListener("input", () => {
    input.dataset.selectedIata = "";
    debounceSuggestions(input);
  });

  input.addEventListener("focus", () => {
    if (input.value.trim()) {
      debounceSuggestions(input, true);
    }
  });

  input.addEventListener("blur", () => {
    window.setTimeout(() => hideSuggestions(input.id), 150);
  });

  input.addEventListener("keydown", (event) => {
    handleSuggestionKeydown(event, input);
  });
});

function debounceSuggestions(input, immediate = false) {
  const query = input.value.trim();

  if (!query) {
    hideSuggestions(input.id);
    return;
  }

  if (suggestionRequests.has(input.id)) {
    window.clearTimeout(suggestionRequests.get(input.id));
  }

  const delay = immediate ? 0 : 180;
  const timeoutId = window.setTimeout(
    () => fetchSuggestions(input, query),
    delay,
  );
  suggestionRequests.set(input.id, timeoutId);
}

async function fetchSuggestions(input, query) {
  try {
    const response = await fetch(
      `/api/aeroportos?q=${encodeURIComponent(query)}`,
    );
    const items = response.ok ? await response.json() : [];
    renderSuggestions(input.id, items);
  } catch (error) {
    renderSuggestions(input.id, []);
  }
}

function renderSuggestions(inputId, items) {
  const state = suggestionState.get(inputId);

  if (!state) {
    return;
  }

  state.items = Array.isArray(items) ? items.slice(0, 6) : [];
  state.activeIndex = -1;
  state.panel.innerHTML = "";

  if (!state.items.length) {
    state.panel.hidden = true;
    return;
  }

  state.items.forEach((item, index) => {
    const option = createElement("button", "suggestion-item");
    option.type = "button";
    option.dataset.index = String(index);
    option.innerHTML = `
      <strong>${item.label}</strong>
      <span>${item.country}</span>
    `;
    option.addEventListener("mousedown", (event) => {
      event.preventDefault();
      selectSuggestion(inputId, index);
    });
    state.panel.append(option);
  });

  state.panel.hidden = false;
}

function selectSuggestion(inputId, index) {
  const state = suggestionState.get(inputId);
  const input = document.getElementById(inputId);

  if (!state || !input || !state.items[index]) {
    return;
  }

  const item = state.items[index];
  input.value = item.iata;
  input.dataset.selectedIata = item.iata;
  input.dataset.selectedLabel = item.label;
  hideSuggestions(inputId);
}

function handleSuggestionKeydown(event, input) {
  const state = suggestionState.get(input.id);

  if (!state || state.panel.hidden || !state.items.length) {
    return;
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    state.activeIndex = Math.min(state.activeIndex + 1, state.items.length - 1);
    updateActiveSuggestion(input.id);
  }

  if (event.key === "ArrowUp") {
    event.preventDefault();
    state.activeIndex = Math.max(state.activeIndex - 1, 0);
    updateActiveSuggestion(input.id);
  }

  if (event.key === "Enter" && state.activeIndex >= 0) {
    event.preventDefault();
    selectSuggestion(input.id, state.activeIndex);
  }

  if (event.key === "Escape") {
    hideSuggestions(input.id);
  }
}

function updateActiveSuggestion(inputId) {
  const state = suggestionState.get(inputId);

  if (!state) {
    return;
  }

  const children = Array.from(state.panel.querySelectorAll(".suggestion-item"));

  children.forEach((child, index) => {
    child.classList.toggle("is-active", index === state.activeIndex);
  });
}

function hideSuggestions(inputId) {
  const state = suggestionState.get(inputId);

  if (!state) {
    return;
  }

  state.panel.hidden = true;
  state.panel.innerHTML = "";
  state.items = [];
  state.activeIndex = -1;
}

function formatPrice(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/D";
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatPath(path) {
  return Array.isArray(path) && path.length
    ? path.join(" → ")
    : "Rota indisponível";
}

function createElement(tag, className, textContent) {
  const element = document.createElement(tag);
  if (className) {
    element.className = className;
  }
  if (textContent !== undefined) {
    element.textContent = textContent;
  }
  return element;
}

function renderBadge(label, value) {
  const badge = createElement("div", "metric-badge");
  const labelNode = createElement("span", "metric-badge__label", label);
  const valueNode = createElement("strong", "metric-badge__value", value);
  badge.append(labelNode, valueNode);
  return badge;
}

function renderLegs(legs) {
  const list = createElement("div", "legs-list");

  if (!Array.isArray(legs) || legs.length === 0) {
    const empty = createElement(
      "p",
      "empty-state",
      "Sem detalhes de trechos para exibir.",
    );
    list.append(empty);
    return list;
  }

  legs.forEach((leg, index) => {
    const legItem = createElement("div", "leg-item");
    const left = createElement(
      "span",
      "leg-item__index",
      String(index + 1).padStart(2, "0"),
    );
    const route = createElement(
      "strong",
      "leg-item__route",
      `${leg.from} → ${leg.to}`,
    );
    const price = createElement(
      "span",
      "leg-item__price",
      formatPrice(leg.price),
    );
    legItem.append(left, route, price);
    list.append(legItem);
  });

  return list;
}

function renderRouteGroup(
  title,
  summaryLabel,
  summaryValue,
  routes,
  metaLabel,
) {
  const section = createElement("section", "result-section");
  const header = createElement("div", "result-section__header");
  const heading = createElement("h3", "result-section__title", title);
  const summary = createElement(
    "p",
    "result-section__summary",
    `${summaryLabel}: ${summaryValue}`,
  );
  header.append(heading, summary);
  section.append(header);

  if (!Array.isArray(routes) || routes.length === 0) {
    const empty = createElement("div", "result-card result-card--empty");
    empty.append(
      createElement(
        "p",
        "empty-state",
        "Nenhuma rota encontrada para este critério.",
      ),
    );
    section.append(empty);
    return section;
  }

  const routeGrid = createElement("div", "route-grid");

  routes.forEach((route, index) => {
    const card = createElement("article", "result-card");
    const cardHeader = createElement("div", "result-card__header");
    cardHeader.append(
      createElement("span", "route-rank", `Opção ${index + 1}`),
      createElement("span", "route-price", formatPrice(route.total_price)),
    );

    const path = createElement("p", "route-path", formatPath(route.path));
    const meta = createElement("div", "route-meta");
    meta.append(
      renderBadge(
        metaLabel,
        String(route.connections ?? route.segments ?? "N/D"),
      ),
      renderBadge("Custo total", formatPrice(route.total_price)),
    );

    card.append(cardHeader, path, meta, renderLegs(route.legs));
    routeGrid.append(card);
  });

  section.append(routeGrid);
  return section;
}

function renderResults(data) {
  resultados.innerHTML = "";
  resultados.style.display = "block";

  const dashboard = createElement("div", "dashboard");

  const intro = createElement("section", "summary-panel");
  const introTitle = createElement(
    "h2",
    "summary-panel__title",
    `${data.bfs?.origin ?? data.dijkstra?.origin ?? "Origem"} → ${data.bfs?.destination ?? data.dijkstra?.destination ?? "Destino"}`,
  );
  const introText = createElement(
    "p",
    "summary-panel__text",
    "Comparação entre menor número de conexões, menor preço total e voo direto.",
  );
  const introBadges = createElement("div", "summary-panel__badges");

  introBadges.append(
    renderBadge("BFS", data.bfs?.found ? "Encontrou rota" : "Sem rota"),
    renderBadge(
      "Dijkstra",
      data.dijkstra?.found ? "Encontrou rota" : "Sem rota",
    ),
    renderBadge(
      "Direto",
      data.direto?.has_direct_route ? "Disponível" : "Indisponível",
    ),
  );

  intro.append(introTitle, introText, introBadges);
  dashboard.append(intro);

  const overview = createElement("section", "overview-grid");
  const bfsBest = data.bfs?.routes?.[0];
  const dijkstraBest = data.dijkstra?.routes?.[0];
  const directPrice = data.direto?.has_direct_route
    ? formatPrice(data.direto.direct_price)
    : "Sem voo direto";

  overview.append(
    renderMetricCard(
      "Melhor BFS",
      bfsBest ? formatPrice(bfsBest.total_price) : "Sem rota",
      bfsBest ? `${bfsBest.connections} conexão(ões)` : "Limites atingidos",
    ),
    renderMetricCard(
      "Melhor Dijkstra",
      dijkstraBest ? formatPrice(dijkstraBest.total_price) : "Sem rota",
      dijkstraBest
        ? `${dijkstraBest.segments} segmento(s)`
        : "Nenhum caminho encontrado",
    ),
    renderMetricCard(
      "Voo direto",
      directPrice,
      data.direto?.has_direct_route
        ? "Rota sem conexão"
        : "Nenhum voo direto disponível",
    ),
  );
  dashboard.append(overview);

  const bfsSection = renderRouteGroup(
    "Busca por menor número de conexões",
    "Conexões da melhor rota",
    data.bfs?.found ? String(data.bfs.connections ?? "N/D") : "Sem rota",
    data.bfs?.routes,
    "Conexões",
  );

  const dijkstraSection = renderRouteGroup(
    "Busca por menor preço total",
    "Segmentos da melhor rota",
    data.dijkstra?.found ? String(data.dijkstra.segments ?? "N/D") : "Sem rota",
    data.dijkstra?.routes,
    "Segmentos",
  );

  dashboard.append(bfsSection, dijkstraSection);

  const directSection = createElement("section", "direct-panel");
  const directTitle = createElement(
    "h3",
    "result-section__title",
    "Voo direto",
  );
  directSection.append(directTitle);

  if (data.direto?.has_direct_route) {
    const directCard = createElement("div", "direct-card");
    directCard.append(
      createElement(
        "p",
        "direct-card__route",
        `${data.direto.origin} → ${data.direto.destination}`,
      ),
      createElement(
        "strong",
        "direct-card__price",
        formatPrice(data.direto.direct_price),
      ),
      createElement(
        "span",
        "direct-card__status",
        "Existe voo direto com preço calculado",
      ),
    );
    directSection.append(directCard);
  } else {
    const directCard = createElement("div", "direct-card direct-card--empty");
    directCard.append(
      createElement(
        "p",
        "empty-state",
        data.direto?.message || "Não existe voo direto para essa combinação.",
      ),
    );
    directSection.append(directCard);
  }

  dashboard.append(directSection);

  const limitsSection = createElement("section", "limits-panel");
  const limitsTitle = createElement(
    "h3",
    "result-section__title",
    "Limites e segurança",
  );
  const limitsGrid = createElement("div", "limits-grid");

  limitsGrid.append(
    renderLimitCard(
      "BFS",
      data.bfs?.limits?.max_connections,
      data.bfs?.limits?.expansions_used,
      data.bfs?.limits?.truncated,
    ),
    renderLimitCard(
      "Dijkstra",
      data.dijkstra?.limits?.max_segments,
      null,
      data.dijkstra?.limits?.truncated,
    ),
  );

  limitsSection.append(limitsTitle, limitsGrid);
  dashboard.append(limitsSection);

  resultados.append(dashboard);
}

function renderMetricCard(title, value, subtitle) {
  const card = createElement("article", "overview-card");
  card.append(
    createElement("span", "overview-card__title", title),
    createElement("strong", "overview-card__value", value),
    createElement("span", "overview-card__subtitle", subtitle),
  );
  return card;
}

function renderLimitCard(title, primary, secondary, truncated) {
  const card = createElement("article", "limit-card");
  const valueText =
    primary === null || primary === undefined ? "N/D" : String(primary);
  card.append(
    createElement("span", "limit-card__title", title),
    createElement("strong", "limit-card__value", valueText),
    createElement(
      "span",
      "limit-card__subtitle",
      secondary === null || secondary === undefined
        ? truncated
          ? "Resultado truncado"
          : "Busca completa"
        : `${secondary} expansões usadas`,
    ),
    createElement(
      "span",
      truncated
        ? "status-chip status-chip--warning"
        : "status-chip status-chip--success",
      truncated ? "Truncado" : "Completo",
    ),
  );
  return card;
}

function renderLoadingState(origin, destination) {
  resultados.innerHTML = "";
  resultados.style.display = "block";

  const loading = createElement("div", "loading-state");
  loading.append(
    createElement(
      "strong",
      "loading-state__title",
      "Buscando as melhores opções...",
    ),
    createElement(
      "span",
      "loading-state__text",
      `${origin.toUpperCase()} → ${destination.toUpperCase()}`,
    ),
  );
  resultados.append(loading);
}

function renderError(message) {
  resultados.innerHTML = "";
  resultados.style.display = "block";

  const errorBox = createElement("div", "error-state");
  errorBox.append(
    createElement(
      "strong",
      "error-state__title",
      "Não foi possível concluir a busca.",
    ),
    createElement("p", "error-state__text", message),
  );
  resultados.append(errorBox);
}

async function resolveAirportCode(input) {
  const rawValue = input.value.trim();

  if (!rawValue) {
    return "";
  }

  if (/^[A-Z]{3}$/.test(rawValue)) {
    return rawValue;
  }

  const selectedIata = input.dataset.selectedIata;
  if (selectedIata) {
    return selectedIata;
  }

  const response = await fetch(
    `/api/aeroportos?q=${encodeURIComponent(rawValue)}`,
  );
  const matches = response.ok ? await response.json() : [];

  if (!Array.isArray(matches) || matches.length === 0) {
    return "";
  }

  const exactCityMatch = matches.find(
    (item) => item.city?.toLowerCase() === rawValue.toLowerCase(),
  );
  const chosen = exactCityMatch || matches[0];
  input.value = chosen.iata;
  input.dataset.selectedIata = chosen.iata;
  input.dataset.selectedLabel = chosen.label;
  return chosen.iata;
}

async function buscar() {
  const origemInput = document.getElementById("origem");
  const destinoInput = document.getElementById("destino");

  const origem = await resolveAirportCode(origemInput);
  const destino = await resolveAirportCode(destinoInput);

  if (!origem || !destino) {
    alert(
      "Digite uma cidade, nome de aeroporto ou código IATA e selecione uma sugestão.",
    );
    return;
  }

  renderLoadingState(origem, destino);

  try {
    const response = await fetch(
      `/api/rotas?origem=${encodeURIComponent(origem)}&destino=${encodeURIComponent(destino)}`,
    );
    const data = await response.json();

    if (response.ok) {
      renderResults(data);
      return;
    }

    renderError(data.erro || "Falha na busca.");
  } catch (error) {
    renderError(`Erro de conexão com o servidor: ${error.message || error}`);
  }
}

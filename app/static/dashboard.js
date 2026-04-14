const state = {
  activities: [],
  filteredActivities: [],
  paginatedActivities: [],
  highPriority: [],
  digest: null,
  digestPreview: "",
  digestMarkdown: "",
  filters: {
    search: "",
    category: "",
    reviewStatus: "",
  },
  reviewActions: JSON.parse(window.localStorage.getItem("csePulseReviewActions") || "{}"),
  digestTab: "preview",
  pagination: {
    page: 1,
    pageSize: 10,
  },
};

async function fetchPayload(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function persistReviewActions() {
  window.localStorage.setItem("csePulseReviewActions", JSON.stringify(state.reviewActions));
}

function safeText(value) {
  return value ?? "";
}

function priorityClass(priority) {
  if (priority >= 5) return "priority-high";
  if (priority >= 3) return "priority-medium";
  return "priority-low";
}

function setStatus(message, tone = "neutral") {
  const node = document.getElementById("status-message");
  node.textContent = message;
  node.className = `status-message status-${tone}`;
}

function setInlineFeedback(id, message = "") {
  const node = document.getElementById(id);
  if (!message) {
    node.textContent = "";
    node.className = "inline-feedback inline-feedback-hidden";
    return;
  }
  node.textContent = message;
  node.className = "inline-feedback";
}

function createBadge(label, className = "") {
  return `<span class="pill ${className}">${label}</span>`;
}

function deriveReviewLabel(activity) {
  return state.reviewActions[activity.id] || activity.review_status || "pending";
}

function formatReviewLabel(label) {
  return label === "not reviewed" ? "pending" : label;
}

function createReviewBadge(activity) {
  return createBadge(`Review ${formatReviewLabel(deriveReviewLabel(activity))}`, "review-chip");
}

function activitySearchBlob(activity) {
  return [
    activity.faculty_name,
    activity.ai_summary,
    activity.category,
    activity.raw_text,
    activity.review_status,
  ]
    .join(" ")
    .toLowerCase();
}

function filterActivities(activities) {
  return activities.filter((activity) => {
    if (state.filters.category && activity.category !== state.filters.category) {
      return false;
    }
    if (state.filters.reviewStatus && activity.review_status !== state.filters.reviewStatus) {
      return false;
    }
    if (state.filters.search) {
      return activitySearchBlob(activity).includes(state.filters.search.toLowerCase());
    }
    return true;
  });
}

function getPaginationMeta() {
  const totalItems = state.filteredActivities.length;
  const pageSize = state.pagination.pageSize;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const currentPage = Math.min(state.pagination.page, totalPages);
  const startIndex = totalItems === 0 ? 0 : (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return {
    totalItems,
    totalPages,
    currentPage,
    startIndex,
    endIndex,
  };
}

function updatePaginatedActivities() {
  const meta = getPaginationMeta();
  state.pagination.page = meta.currentPage;
  state.paginatedActivities = state.filteredActivities.slice(meta.startIndex, meta.endIndex);
}

function createActivityCard(activity) {
  return `
    <article class="inbox-item" data-activity-id="${activity.id}">
      <div class="inbox-item-header">
        <h3 class="item-title">${safeText(activity.faculty_name) || "Unknown faculty"}</h3>
      </div>
      <div class="item-badges">
        ${createBadge(activity.category)}
        ${createBadge(`Priority ${activity.priority}`, priorityClass(activity.priority))}
        ${createReviewBadge(activity)}
      </div>
      <p class="item-summary">${safeText(activity.ai_summary)}</p>
      <div class="meta-line">Detected ${activity.detected_at.slice(0, 10)} • Source ${activity.source_type}</div>
      <div class="review-actions">
        <button class="review-button review-approve" type="button" data-review-action="approved" data-activity-id="${activity.id}">Approve</button>
        <button class="review-button review-reject" type="button" data-review-action="rejected" data-activity-id="${activity.id}">Reject</button>
        <button class="review-button review-mark" type="button" data-review-action="reviewed" data-activity-id="${activity.id}">Mark reviewed</button>
      </div>
    </article>
  `;
}

function renderPagination() {
  const summary = document.getElementById("pagination-summary");
  const prevButton = document.getElementById("pagination-prev");
  const nextButton = document.getElementById("pagination-next");
  const pagesContainer = document.getElementById("pagination-pages");
  const meta = getPaginationMeta();

  summary.textContent = meta.totalItems === 0
    ? "Showing 0-0 of 0"
    : `Showing ${meta.startIndex + 1}-${meta.endIndex} of ${meta.totalItems}`;

  prevButton.disabled = meta.currentPage <= 1;
  nextButton.disabled = meta.currentPage >= meta.totalPages || meta.totalItems === 0;

  pagesContainer.innerHTML = Array.from({ length: meta.totalPages }, (_, index) => {
    const page = index + 1;
    const activeClass = page === meta.currentPage ? "is-active" : "";
    return `<button class="page-number ${activeClass}" type="button" data-page-number="${page}">${page}</button>`;
  }).join("");
}

function renderInbox() {
  const container = document.getElementById("activity-inbox");
  if (!state.filteredActivities.length) {
    container.className = "inbox-list empty-state";
    container.innerHTML = "No activities match the current filters.";
    renderPagination();
    return;
  }

  container.className = "inbox-list";
  container.innerHTML = state.paginatedActivities.map(createActivityCard).join("");
  renderPagination();
}

function renderSpotlight() {
  const container = document.getElementById("spotlight-panel");
  const items = state.highPriority.slice(0, 3);

  if (!items.length) {
    container.className = "spotlight-list empty-state";
    container.innerHTML = "No high-priority items under the current filters.";
    return;
  }

  container.className = "spotlight-list";
  container.innerHTML = items
    .map(
      (item) => `
        <article class="spotlight-card" data-activity-id="${item.id}">
          <div class="spotlight-header">
            <h4>${safeText(item.faculty_name) || "Unknown faculty"}</h4>
            ${createBadge(`P${item.priority}`, priorityClass(item.priority))}
          </div>
          <p class="spotlight-summary">${safeText(item.ai_summary)}</p>
          <div class="meta-line">${item.category} • ${item.detected_at.slice(0, 10)}</div>
        </article>
      `,
    )
    .join("");
}

function buildChartRows(labelValuePairs, className) {
  const max = Math.max(...labelValuePairs.map((item) => item.value), 1);
  return `
    <div class="${className}">
      ${labelValuePairs
        .map(
          (item) => `
            <div class="${className === "timeline-bars" ? "timeline-row" : "chart-row"}">
              <span>${item.label}</span>
              <div class="${className === "timeline-bars" ? "timeline-track" : "chart-track"}">
                <div class="${className === "timeline-bars" ? "timeline-fill" : "chart-fill"}" style="width: ${(item.value / max) * 100}%"></div>
              </div>
              <strong>${item.value}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderCharts() {
  const charts = document.getElementById("charts-grid");
  const activities = state.filteredActivities;

  if (!activities.length) {
    charts.className = "charts-grid empty-state";
    charts.innerHTML = "Charts will appear when activity data is available.";
    return;
  }

  const categoryCounts = {};
  const priorityCounts = { "Priority 5": 0, "Priority 4": 0, "Priority 1-3": 0 };

  activities.forEach((activity) => {
    categoryCounts[activity.category] = (categoryCounts[activity.category] || 0) + 1;
    if (activity.priority >= 5) {
      priorityCounts["Priority 5"] += 1;
    } else if (activity.priority >= 4) {
      priorityCounts["Priority 4"] += 1;
    } else {
      priorityCounts["Priority 1-3"] += 1;
    }
  });

  const categoryRows = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 4)
    .map(([label, value]) => ({ label, value }));

  const priorityRows = Object.entries(priorityCounts).map(([label, value]) => ({ label, value }));

  charts.className = "charts-grid";
  charts.innerHTML = `
    <article class="chart-card">
      <h4>Category mix</h4>
      ${buildChartRows(categoryRows, "chart-bars")}
    </article>
    <article class="chart-card">
      <h4>Priority mix</h4>
      ${buildChartRows(priorityRows, "chart-bars")}
    </article>
  `;
}

function renderTimeline() {
  const container = document.getElementById("timeline-chart");
  const activities = state.filteredActivities;

  if (!activities.length) {
    container.className = "timeline-chart empty-state";
    container.innerHTML = "No timeline data under the current filters.";
    return;
  }

  const countsByDay = {};
  activities.forEach((activity) => {
    const day = activity.detected_at.slice(0, 10);
    countsByDay[day] = (countsByDay[day] || 0) + 1;
  });

  const rows = Object.entries(countsByDay)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .slice(-7)
    .map(([label, value]) => ({ label, value }));

  container.className = "timeline-chart";
  container.innerHTML = buildChartRows(rows, "timeline-bars");
}

function renderDigestSummary() {
  const container = document.getElementById("digest-summary-cards");
  if (!state.digest) {
    container.className = "digest-summary-cards empty-state";
    container.innerHTML = "Digest summary is not ready yet.";
    return;
  }

  container.className = "digest-summary-cards";
  container.innerHTML = `
    <article class="digest-summary-card">
      <span class="meta-line">Date range</span>
      <strong>${state.digest.date_range.start_date}</strong>
      <span class="meta-line">to ${state.digest.date_range.end_date}</span>
    </article>
    <article class="digest-summary-card">
      <span class="meta-line">Sections</span>
      <strong>${state.digest.sections.length}</strong>
      <span class="meta-line">grouped categories</span>
    </article>
    <article class="digest-summary-card">
      <span class="meta-line">Digest items</span>
      <strong>${state.digest.total_items}</strong>
      <span class="meta-line">current preview window</span>
    </article>
  `;
}

function renderDigestWorkspace() {
  document.getElementById("digest-preview-content").textContent = state.digestPreview || "No preview available.";
  document.getElementById("digest-json-content").textContent = state.digest
    ? JSON.stringify(state.digest, null, 2)
    : "No JSON digest available.";
  document.getElementById("digest-markdown-content").textContent = state.digestMarkdown || "No markdown export available.";
  renderDigestSummary();
}

function renderKpis() {
  document.getElementById("kpi-total").textContent = String(state.activities.length);
  document.getElementById("kpi-pending").textContent = String(
    state.activities.filter((item) => item.review_status === "pending").length,
  );
  document.getElementById("kpi-priority").textContent = String(state.highPriority.length);
  document.getElementById("kpi-digest").textContent = String(state.digest?.total_items || 0);
}

function renderSyncCard() {
  const actions = Object.values(state.reviewActions);
  const reviewed = actions.filter((item) => item === "reviewed").length;
  const approved = actions.filter((item) => item === "approved").length;

  document.getElementById("sync-reviewed-count").textContent = String(reviewed);
  document.getElementById("sync-approved-count").textContent = String(approved);

  const stateNode = document.getElementById("sync-state");
  const messageNode = document.getElementById("sync-message");

  if (approved > 0) {
    stateNode.textContent = "Ready to sync";
    messageNode.textContent = "Approved items are queued in local demo state.";
  } else if (reviewed > 0) {
    stateNode.textContent = "Review in progress";
    messageNode.textContent = "Items have been reviewed locally, but none are approved yet.";
  } else {
    stateNode.textContent = "Mock-safe mode";
    messageNode.textContent = "Waiting for local review actions.";
  }
}

function buildDigestQuery() {
  const params = new URLSearchParams({
    max_items_per_category: "4",
  });

  if (state.filters.reviewStatus) {
    params.set("review_status", state.filters.reviewStatus);
  }

  return params.toString();
}

function applyFiltersAndRender() {
  state.filteredActivities = filterActivities(state.activities);
  state.pagination.page = 1;
  updatePaginatedActivities();
  state.highPriority = state.filteredActivities.filter((item) => item.priority >= 4);

  renderInbox();
  renderSpotlight();
  renderCharts();
  renderTimeline();

  const filterSummary = [
    state.filters.search ? `search: "${state.filters.search}"` : null,
    state.filters.category ? `category: ${state.filters.category}` : null,
    state.filters.reviewStatus ? `status: ${state.filters.reviewStatus}` : null,
  ]
    .filter(Boolean)
    .join(" • ");

  setInlineFeedback("inbox-feedback", filterSummary ? `Showing ${filterSummary}.` : "");
}

function updateDigestTab(nextTab) {
  state.digestTab = nextTab;
  document.querySelectorAll("[data-digest-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.digestTab === nextTab);
  });
  document.querySelectorAll("[data-digest-panel]").forEach((panel) => {
    panel.classList.toggle("is-active", panel.dataset.digestPanel === nextTab);
  });
}

function openDetailModal(activityId) {
  const activity = state.activities.find((item) => item.id === activityId);
  if (!activity) {
    return;
  }

  const modal = document.getElementById("detail-modal");
  const content = document.getElementById("detail-modal-content");
  const reviewLabel = formatReviewLabel(deriveReviewLabel(activity));

  content.innerHTML = `
    <div class="detail-grid">
      <div>
        <p class="section-tag">Activity Detail</p>
        <h3 id="detail-modal-title">${safeText(activity.faculty_name) || "Unknown faculty"}</h3>
        <div class="item-badges">
          ${createBadge(activity.category)}
          ${createBadge(`Priority ${activity.priority}`, priorityClass(activity.priority))}
          ${createBadge(`Review ${reviewLabel}`, "review-chip")}
        </div>
      </div>
      <div class="detail-box">
        <h4>Summary</h4>
        <p>${safeText(activity.ai_summary)}</p>
      </div>
      <div class="detail-box">
        <h4>Source Details</h4>
        <p><b>Detected:</b> ${activity.detected_at}</p>
        <p><b>Source type:</b> ${activity.source_type}</p>
        <p><b>Source URL:</b> ${safeText(activity.source_url) || "Unavailable"}</p>
      </div>
      <div class="detail-box">
        <h4>Raw Activity Text</h4>
        <p>${safeText(activity.raw_text)}</p>
      </div>
    </div>
  `;

  modal.classList.remove("modal-hidden");
  modal.setAttribute("aria-hidden", "false");
}

function closeDetailModal() {
  const modal = document.getElementById("detail-modal");
  modal.classList.add("modal-hidden");
  modal.setAttribute("aria-hidden", "true");
}

function handleReviewAction(activityId, nextState) {
  state.reviewActions[activityId] = nextState;
  persistReviewActions();
  applyFiltersAndRender();
  renderSyncCard();
  setStatus(`Review updated locally: ${nextState}.`, "success");
}

async function loadDashboard({ digestOnly = false } = {}) {
  setStatus(digestOnly ? "Refreshing digest..." : "Loading dashboard...", "loading");
  if (!digestOnly) {
    setInlineFeedback("inbox-feedback", "Loading activity inbox...");
  }
  setInlineFeedback("digest-feedback", "Loading digest workspace...");

  try {
    if (!digestOnly) {
      state.activities = await fetchPayload("/activities?sort_by=detected_at&sort_order=desc");
      applyFiltersAndRender();
      renderKpis();
    }

    const digestQuery = buildDigestQuery();
    const [digest, preview, markdown] = await Promise.all([
      fetchPayload(`/digest?${digestQuery}`),
      fetchPayload(`/digest/preview?${digestQuery}`),
      fetchPayload(`/digest/export/markdown?${digestQuery}&include_section_totals=true&summary_max_length=140`),
    ]);

    state.digest = digest;
    state.digestPreview = preview;
    state.digestMarkdown = markdown;

    renderDigestWorkspace();
    renderKpis();
    renderSyncCard();
    setInlineFeedback("digest-feedback", digest.sections.length ? "" : "Digest is empty for the current window.");
    setStatus(digestOnly ? "Digest refreshed." : "Dashboard is live.", "success");
  } catch (error) {
    if (!digestOnly) {
      setInlineFeedback("inbox-feedback", "Unable to load activity inbox right now.");
    }
    setInlineFeedback("digest-feedback", "Unable to load digest workspace right now.");
    setStatus(digestOnly ? "Digest refresh failed." : "Unable to load dashboard data.", "error");
    console.error(error);
  }
}

async function runMockIngestion() {
  const button = document.getElementById("ingest-button");
  button.disabled = true;
  setStatus("Running mock ingestion...", "loading");

  try {
    const result = await fetchPayload("/ingest/mock", { method: "POST" });
    await loadDashboard();
    setStatus(`Mock ingestion complete. Added ${result.ingested_count} activities.`, "success");
  } catch (error) {
    setStatus("Mock ingestion failed.", "error");
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

function changePage(nextPage) {
  state.pagination.page = nextPage;
  updatePaginatedActivities();
  renderInbox();
}

function changePageSize(nextSize) {
  state.pagination.pageSize = nextSize;
  state.pagination.page = 1;
  updatePaginatedActivities();
  renderInbox();
  setStatus(`Page size updated to ${nextSize}.`, "success");
}

function applyFiltersFromInputs() {
  state.filters.search = document.getElementById("search-filter").value.trim();
  state.filters.category = document.getElementById("category-filter").value;
  state.filters.reviewStatus = document.getElementById("review-status-filter").value;
  applyFiltersAndRender();
  renderKpis();
}

function clearFilters() {
  document.getElementById("search-filter").value = "";
  document.getElementById("category-filter").value = "";
  document.getElementById("review-status-filter").value = "";
  state.filters = { search: "", category: "", reviewStatus: "" };
  applyFiltersAndRender();
  renderKpis();
  setStatus("Filters cleared.", "success");
}

function bindStaticEvents() {
  document.getElementById("ingest-button").addEventListener("click", runMockIngestion);
  document.getElementById("digest-refresh-button").addEventListener("click", () => loadDashboard({ digestOnly: true }));
  document.getElementById("search-filter").addEventListener("input", applyFiltersFromInputs);
  document.getElementById("category-filter").addEventListener("change", applyFiltersFromInputs);
  document.getElementById("review-status-filter").addEventListener("change", applyFiltersFromInputs);
  document.getElementById("clear-filters-button").addEventListener("click", clearFilters);
  document.getElementById("page-size-selector").addEventListener("change", (event) => {
    changePageSize(Number(event.target.value));
  });
  document.getElementById("pagination-prev").addEventListener("click", () => {
    changePage(Math.max(1, state.pagination.page - 1));
  });
  document.getElementById("pagination-next").addEventListener("click", () => {
    const meta = getPaginationMeta();
    changePage(Math.min(meta.totalPages, state.pagination.page + 1));
  });
  document.querySelectorAll("[data-digest-tab]").forEach((button) => {
    button.addEventListener("click", () => updateDigestTab(button.dataset.digestTab));
  });
  document.getElementById("modal-close-button").addEventListener("click", closeDetailModal);
  document.querySelector("[data-close-modal='true']").addEventListener("click", closeDetailModal);
}

function bindDynamicEvents() {
  document.getElementById("activity-inbox").addEventListener("click", (event) => {
    const reviewButton = event.target.closest("[data-review-action]");
    if (reviewButton) {
      event.stopPropagation();
      handleReviewAction(reviewButton.dataset.activityId, reviewButton.dataset.reviewAction);
      return;
    }

    const card = event.target.closest("[data-activity-id]");
    if (card) {
      openDetailModal(card.dataset.activityId);
    }
  });

  document.getElementById("spotlight-panel").addEventListener("click", (event) => {
    const card = event.target.closest("[data-activity-id]");
    if (card) {
      openDetailModal(card.dataset.activityId);
    }
  });

  document.getElementById("pagination-pages").addEventListener("click", (event) => {
    const button = event.target.closest("[data-page-number]");
    if (button) {
      changePage(Number(button.dataset.pageNumber));
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindStaticEvents();
  bindDynamicEvents();
  updateDigestTab("preview");
  loadDashboard();
});

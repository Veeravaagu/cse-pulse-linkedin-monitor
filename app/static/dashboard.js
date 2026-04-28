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
    reviewStatus: "pending",
  },
  digestTab: "preview",
  pagination: {
    page: 1,
    pageSize: 25,
    total: 0,
  },
  digestWindow: {
    startDate: "",
    endDate: "",
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

function safeText(value) {
  return value ?? "";
}

function formatDateInput(date) {
  return date.toISOString().slice(0, 10);
}

function defaultDigestWindow() {
  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - 7);
  return {
    startDate: formatDateInput(start),
    endDate: formatDateInput(end),
  };
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
  return activity.review_status || "pending";
}

function formatReviewLabel(label) {
  return label;
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
    activity.source_type,
    activity.source_url,
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
  const totalItems = state.pagination.total;
  const pageSize = state.pagination.pageSize;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const currentPage = Math.min(state.pagination.page, totalPages);
  const startIndex = totalItems === 0 ? 0 : (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + state.filteredActivities.length, totalItems);

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
  state.paginatedActivities = state.filteredActivities;
}

function createActivityCard(activity) {
  const activityLabel = safeText(activity.faculty_name) || "General CSE activity";
  const summary = safeText(activity.ai_summary);
  const reviewControls =
    activity.review_status === "pending"
      ? `
        <div class="review-actions">
          <button class="review-button review-approve" type="button" data-review-action="approved" data-activity-id="${activity.id}">Approve</button>
          <button class="review-button review-reject" type="button" data-review-action="rejected" data-activity-id="${activity.id}">Reject</button>
        </div>
      `
      : "";

  return `
    <article class="inbox-item" data-activity-id="${activity.id}">
      <div class="inbox-item-header">
        <h3 class="item-title" title="${activityLabel}">${activityLabel}</h3>
      </div>
      <div class="item-badges">
        ${createBadge(activity.category)}
        ${createBadge(`Priority ${activity.priority}`, priorityClass(activity.priority))}
        ${createReviewBadge(activity)}
      </div>
      <p class="item-summary" title="${summary}">${summary}</p>
      <div class="meta-line">Detected ${activity.detected_at.slice(0, 10)} • Source ${activity.source_type}</div>
      ${reviewControls}
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
    ? "Showing 0-0 of 0 recent matches"
    : `Showing ${meta.startIndex + 1}-${meta.endIndex} of ${meta.totalItems} recent matches`;

  prevButton.disabled = meta.currentPage <= 1;
  nextButton.disabled = meta.currentPage >= meta.totalPages || meta.totalItems === 0;

  pagesContainer.textContent = `Page ${meta.currentPage} of ${meta.totalPages}`;
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
            <h4>${safeText(item.faculty_name) || "General CSE activity"}</h4>
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
      <strong class="digest-date-range">${state.digest.date_range.start_date} to ${state.digest.date_range.end_date}</strong>
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
  document.getElementById("kpi-total").textContent = String(state.pagination.total);
  document.getElementById("kpi-pending").textContent = String(
    state.activities.filter((item) => item.review_status === "pending").length,
  );
  document.getElementById("kpi-priority").textContent = String(state.highPriority.length);
  document.getElementById("kpi-digest").textContent = String(state.digest?.total_items || 0);
}

function renderSyncCard() {
  const rejected = state.activities.filter((item) => item.review_status === "rejected").length;
  const approved = state.activities.filter((item) => item.review_status === "approved").length;

  document.getElementById("sync-rejected-count").textContent = String(rejected);
  document.getElementById("sync-approved-count").textContent = String(approved);

  const stateNode = document.getElementById("sync-state");
  const messageNode = document.getElementById("sync-message");

  if (approved > 0) {
    stateNode.textContent = "Ready to sync";
    messageNode.textContent = "Approved items are visible on this page.";
  } else if (rejected > 0) {
    stateNode.textContent = "Review in progress";
    messageNode.textContent = "Rejected items are visible on this page.";
  } else {
    stateNode.textContent = "Review queue";
    messageNode.textContent = "Waiting for review actions on this page.";
  }
}

function buildDigestQuery() {
  const params = new URLSearchParams({
    max_items_per_category: "4",
  });

  if (state.digestWindow.startDate) {
    params.set("start_date", state.digestWindow.startDate);
  }
  if (state.digestWindow.endDate) {
    params.set("end_date", state.digestWindow.endDate);
  }
  if (state.filters.reviewStatus) {
    params.set("review_status", state.filters.reviewStatus);
  }

  return params.toString();
}

function updateExportLink(digestQuery = buildDigestQuery()) {
  const params = new URLSearchParams(digestQuery);
  params.set("include_section_totals", "true");
  params.set("summary_max_length", "140");
  document.getElementById("export-markdown-button").href = `/digest/export/markdown?${params.toString()}`;
}

function applyDigestWindowFromInputs() {
  state.digestWindow.startDate = document.getElementById("digest-start-date").value;
  state.digestWindow.endDate = document.getElementById("digest-end-date").value;
  if (
    state.digestWindow.startDate &&
    state.digestWindow.endDate &&
    state.digestWindow.startDate > state.digestWindow.endDate
  ) {
    setInlineFeedback("digest-feedback", "Start date must be before end date.");
    return;
  }
  updateExportLink();
  loadDashboard({ digestOnly: true });
}

function applyFiltersAndRender() {
  state.filteredActivities = filterActivities(state.activities);
  updatePaginatedActivities();
  state.highPriority = state.filteredActivities.filter((item) => item.priority >= 4);

  updateStatusTabs();
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

  setInlineFeedback("inbox-feedback", filterSummary ? `Current page filter: ${filterSummary}.` : "");
}

function buildActivityPageQuery() {
  const params = new URLSearchParams({
    sort_by: "detected_at",
    sort_order: "desc",
    days: "30",
    limit: String(state.pagination.pageSize),
    offset: String((state.pagination.page - 1) * state.pagination.pageSize),
  });

  if (state.filters.reviewStatus) {
    params.set("review_status", state.filters.reviewStatus);
  }
  return params.toString();
}

async function loadActivityPage() {
  const page = await fetchPayload(`/activities/page?${buildActivityPageQuery()}`);
  if (!page.items.length && page.total > 0 && page.offset >= page.total) {
    state.pagination.page = Math.ceil(page.total / state.pagination.pageSize);
    return loadActivityPage();
  }

  state.activities = page.items;
  state.pagination.total = page.total;
  state.pagination.pageSize = page.limit;
  state.pagination.page = Math.floor(page.offset / page.limit) + 1;
  applyFiltersAndRender();
  renderKpis();
}

function updateStatusTabs() {
  document.querySelectorAll("[data-status-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.statusTab === state.filters.reviewStatus);
  });
}

function updateStatusFilter(nextStatus) {
  state.filters.reviewStatus = nextStatus;
  state.pagination.page = 1;
  loadActivityPage();
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
        <h3 id="detail-modal-title">${safeText(activity.faculty_name) || "General CSE activity"}</h3>
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

async function handleReviewAction(activityId, nextState, button) {
  const endpoint = nextState === "approved" ? "approve" : "reject";
  button.disabled = true;
  setStatus(`Updating review status to ${nextState}...`, "loading");

  try {
    const updated = await fetchPayload(`/activities/${activityId}/${endpoint}`, { method: "POST" });
    state.activities = state.activities.map((activity) => (activity.id === updated.id ? updated : activity));
    await loadActivityPage();
    renderSyncCard();
    setStatus(`Activity ${nextState}.`, "success");
  } catch (error) {
    button.disabled = false;
    setStatus("Review update failed.", "error");
    console.error(error);
  }
}

async function loadDashboard({ digestOnly = false } = {}) {
  setStatus(digestOnly ? "Refreshing digest..." : "Loading dashboard...", "loading");
  if (!digestOnly) {
    setInlineFeedback("inbox-feedback", "Loading activity inbox...");
  }
  setInlineFeedback("digest-feedback", "Loading digest workspace...");

  try {
    if (!digestOnly) {
      await loadActivityPage();
    }

    const digestQuery = buildDigestQuery();
    updateExportLink(digestQuery);
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

async function runIngestion() {
  const button = document.getElementById("ingest-button");
  button.disabled = true;
  setStatus("Running ingestion...", "loading");

  try {
    const result = await fetchPayload("/ingest", { method: "POST" });
    await loadDashboard();
    setStatus(`Ingestion complete. Added ${result.ingested_count} activities.`, "success");
  } catch (error) {
    setStatus("Ingestion failed.", "error");
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

function changePage(nextPage) {
  state.pagination.page = nextPage;
  loadActivityPage();
}

function changePageSize(nextSize) {
  state.pagination.pageSize = nextSize;
  state.pagination.page = 1;
  loadActivityPage();
  setStatus(`Page size updated to ${nextSize}.`, "success");
}

function applyFiltersFromInputs() {
  state.filters.search = document.getElementById("search-filter").value.trim();
  state.filters.category = document.getElementById("category-filter").value;
  applyFiltersAndRender();
  renderKpis();
}

function clearFilters() {
  document.getElementById("search-filter").value = "";
  document.getElementById("category-filter").value = "";
  state.filters.search = "";
  state.filters.category = "";
  applyFiltersAndRender();
  renderKpis();
  setStatus("Filters cleared.", "success");
}

function bindStaticEvents() {
  document.getElementById("ingest-button").addEventListener("click", runIngestion);
  document.getElementById("digest-refresh-button").addEventListener("click", () => loadDashboard({ digestOnly: true }));
  document.getElementById("digest-start-date").addEventListener("change", applyDigestWindowFromInputs);
  document.getElementById("digest-end-date").addEventListener("change", applyDigestWindowFromInputs);
  document.getElementById("search-filter").addEventListener("input", applyFiltersFromInputs);
  document.getElementById("category-filter").addEventListener("change", applyFiltersFromInputs);
  document.getElementById("clear-filters-button").addEventListener("click", clearFilters);
  document.querySelectorAll("[data-status-tab]").forEach((button) => {
    button.addEventListener("click", () => updateStatusFilter(button.dataset.statusTab));
  });
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
      handleReviewAction(reviewButton.dataset.activityId, reviewButton.dataset.reviewAction, reviewButton);
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

}

document.addEventListener("DOMContentLoaded", () => {
  state.digestWindow = defaultDigestWindow();
  document.getElementById("digest-start-date").value = state.digestWindow.startDate;
  document.getElementById("digest-end-date").value = state.digestWindow.endDate;
  updateExportLink();
  bindStaticEvents();
  bindDynamicEvents();
  updateDigestTab("preview");
  loadDashboard();
});

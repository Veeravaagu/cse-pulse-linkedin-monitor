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
  selectedActivityIds: new Set(),
  pendingDeleteIds: [],
};

const isPublicView = (() => {
  const params = new URLSearchParams(window.location.search);
  return params.get("public") === "1";
})();

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

function getSelectedActivities() {
  return state.activities.filter((activity) => state.selectedActivityIds.has(activity.id));
}

function getVisibleRejectedActivities() {
  return state.filteredActivities.filter((activity) => activity.review_status === "rejected");
}

function isActionableTab() {
  if (isPublicView) {
    return false;
  }
  return ["pending", "approved", "rejected"].includes(state.filters.reviewStatus);
}

function clearSelection() {
  state.selectedActivityIds.clear();
}

function pruneSelection() {
  const loadedIds = new Set(state.activities.map((activity) => activity.id));
  state.selectedActivityIds.forEach((activityId) => {
    if (!loadedIds.has(activityId)) {
      state.selectedActivityIds.delete(activityId);
    }
  });
}

function updateBatchActions() {
  const toolbar = document.getElementById("batch-toolbar");
  if (isPublicView) {
    toolbar.hidden = true;
    document.getElementById("selection-summary").textContent = "0 selected";
    document.getElementById("batch-actions").innerHTML = "";
    return;
  }
  const actions = document.getElementById("batch-actions");
  const selectedActivities = getSelectedActivities();
  const selectedRejectedCount = selectedActivities.filter((activity) => activity.review_status === "rejected").length;
  const visibleRejectedCount = getVisibleRejectedActivities().length;
  const selectedCount = selectedActivities.length;
  const status = state.filters.reviewStatus;

  actions.innerHTML = "";
  if (status === "pending") {
    toolbar.hidden = selectedCount === 0;
    if (selectedCount > 0) {
      actions.insertAdjacentHTML(
        "beforeend",
        `
          <button id="batch-approve-button" class="review-button review-approve" type="button" data-batch-review-action="approved">Approve</button>
          <button id="batch-reject-button" class="review-button review-reject" type="button" data-batch-review-action="rejected">Reject</button>
        `,
      );
    }
  } else if (status === "approved") {
    toolbar.hidden = selectedCount === 0;
    if (selectedCount > 0) {
      actions.insertAdjacentHTML(
        "beforeend",
        `<button id="batch-reject-button" class="review-button review-reject" type="button" data-batch-review-action="rejected">Move to rejected</button>`,
      );
    }
  } else if (status === "rejected") {
    toolbar.hidden = selectedCount === 0;
    if (selectedCount > 0) {
      actions.insertAdjacentHTML(
        "beforeend",
        `
          <button id="batch-approve-button" class="review-button review-approve" type="button" data-batch-review-action="approved">Restore</button>
          <button id="delete-selected-rejected-button" class="review-button review-delete" type="button" data-delete-selected-rejected="true" ${selectedRejectedCount === 0 ? "disabled" : ""}>Delete permanently</button>
        `,
      );
      if (visibleRejectedCount > 0) {
        actions.insertAdjacentHTML(
          "beforeend",
          `<button id="delete-visible-rejected-button" class="review-button review-delete" type="button" data-delete-visible-rejected="true">Delete all rejected currently visible</button>`,
        );
      }
    }
  } else {
    toolbar.hidden = true;
  }

  document.getElementById("selection-summary").textContent =
    selectedCount === 1 ? "1 selected" : `${selectedCount} selected`;
}

function createActivityCard(activity) {
  const activityLabel = safeText(activity.faculty_name) || "General CSE activity";
  const summary = safeText(activity.ai_summary);
  const isSelected = state.selectedActivityIds.has(activity.id);
  const selected = isSelected ? "checked" : "";
  const selectControl = isActionableTab()
    ? `
        <label class="activity-select" aria-label="Select activity">
          <input type="checkbox" data-select-activity-id="${activity.id}" ${selected} />
        </label>
      `
    : "";
  let reviewControls = "";

  if (isPublicView) {
    reviewControls = "";
  } else if (isSelected) {
    reviewControls = "";
  } else if (state.filters.reviewStatus === "pending") {
    reviewControls = `
      <div class="review-actions">
        <button class="review-button review-approve" type="button" data-review-action="approved" data-activity-id="${activity.id}">Approve</button>
        <button class="review-button review-reject" type="button" data-review-action="rejected" data-activity-id="${activity.id}">Reject</button>
      </div>
    `;
  } else if (state.filters.reviewStatus === "approved") {
    reviewControls = `
      <div class="review-actions">
        <button class="review-button review-reject" type="button" data-review-action="rejected" data-activity-id="${activity.id}">Move to rejected</button>
      </div>
    `;
  } else if (state.filters.reviewStatus === "rejected") {
    reviewControls = `
      <div class="review-actions">
        <button class="review-button review-approve" type="button" data-review-action="approved" data-activity-id="${activity.id}">Move to approved</button>
        <button class="review-button review-delete" type="button" data-delete-activity-id="${activity.id}">Delete permanently</button>
      </div>
    `;
  }

  return `
    <article class="inbox-item ${isSelected ? "is-selected" : ""}" data-activity-id="${activity.id}">
      <div class="inbox-item-header">
        ${selectControl}
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
    updateBatchActions();
    return;
  }

  container.className = "inbox-list";
  container.innerHTML = state.paginatedActivities.map(createActivityCard).join("");
  renderPagination();
  updateBatchActions();
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

function renderDigestWorkspace() {
  document.getElementById("digest-preview-content").textContent = state.digestPreview || "No preview available.";
  document.getElementById("digest-json-content").textContent = state.digest
    ? JSON.stringify(state.digest, null, 2)
    : "No JSON digest available.";
  document.getElementById("digest-markdown-content").textContent = state.digestMarkdown || "No markdown export available.";
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
  pruneSelection();
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
}

async function loadPublicActivities() {
  setInlineFeedback("inbox-feedback", "Loading public activity feed...");
  const items = await fetchPayload("/activities/public");
  state.activities = Array.isArray(items) ? items : [];
  state.pagination.total = state.activities.length;
  state.pagination.page = 1;
  applyFiltersAndRender();
}

function updateStatusTabs() {
  document.querySelectorAll("[data-status-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.statusTab === state.filters.reviewStatus);
  });
}

function updateStatusFilter(nextStatus) {
  state.filters.reviewStatus = nextStatus;
  state.pagination.page = 1;
  clearSelection();
  updateBatchActions();
  if (isPublicView) {
    applyFiltersAndRender();
    return;
  }
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
  button.disabled = true;
  setStatus(`Updating review status to ${nextState}...`, "loading");

  try {
    const updated = await fetchPayload(`/activities/${activityId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ review_status: nextState }),
    });
    state.activities = state.activities.map((activity) => (activity.id === updated.id ? updated : activity));
    await loadActivityPage();
    setStatus(`Activity ${nextState}.`, "success");
  } catch (error) {
    button.disabled = false;
    setStatus("Review update failed.", "error");
    console.error(error);
  }
}

async function handleBatchReviewAction(nextState) {
  const ids = Array.from(state.selectedActivityIds);
  if (!ids.length) {
    return;
  }

  setStatus(`Updating ${ids.length} selected activities...`, "loading");

  try {
    const result = await fetchPayload("/activities/batch", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids, review_status: nextState }),
    });
    clearSelection();
    await loadActivityPage();
    setStatus(`Updated ${result.updated_count} activities.`, "success");
  } catch (error) {
    setStatus("Batch review update failed.", "error");
    console.error(error);
  }
}

function openDeleteConfirm(ids, noun = "selected activities") {
  const rejectedIds = ids.filter((activityId) => {
    const activity = state.activities.find((item) => item.id === activityId);
    return activity && activity.review_status === "rejected";
  });
  if (!rejectedIds.length) {
    return;
  }

  state.pendingDeleteIds = rejectedIds;
  const modal = document.getElementById("delete-confirm-modal");
  const message = document.getElementById("delete-confirm-message");
  message.textContent =
    rejectedIds.length === 1
      ? "You are about to permanently delete this activity. This action is irreversible. Do you want to continue?"
      : `You are about to permanently delete ${rejectedIds.length} ${noun}. This action is irreversible. Do you want to continue?`;
  modal.classList.remove("modal-hidden");
  modal.setAttribute("aria-hidden", "false");
}

function closeDeleteConfirm() {
  state.pendingDeleteIds = [];
  const modal = document.getElementById("delete-confirm-modal");
  modal.classList.add("modal-hidden");
  modal.setAttribute("aria-hidden", "true");
}

async function confirmDeleteActivities() {
  const ids = state.pendingDeleteIds;
  if (!ids.length) {
    closeDeleteConfirm();
    return;
  }

  const button = document.getElementById("delete-confirm-button");
  button.disabled = true;
  setStatus(`Deleting ${ids.length} rejected activities...`, "loading");

  try {
    if (ids.length === 1) {
      await fetchPayload(`/activities/${ids[0]}`, { method: "DELETE" });
    } else {
      await fetchPayload("/activities/batch", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids }),
      });
    }
    ids.forEach((activityId) => state.selectedActivityIds.delete(activityId));
    closeDeleteConfirm();
    await loadActivityPage();
    setStatus(ids.length === 1 ? "Activity deleted." : `Deleted ${ids.length} rejected activities.`, "success");
  } catch (error) {
    setStatus("Delete failed.", "error");
    console.error(error);
  } finally {
    button.disabled = false;
  }
}

async function loadDashboard({ digestOnly = false } = {}) {
  setStatus(digestOnly ? "Refreshing digest..." : "Loading dashboard...", "loading");
  if (!digestOnly) {
    setInlineFeedback("inbox-feedback", "Loading activity inbox...");
  }
  if (!isPublicView) {
    setInlineFeedback("digest-feedback", "Loading digest workspace...");
  }

  try {
    if (isPublicView) {
      if (!digestOnly) {
        await loadPublicActivities();
      }
      state.digest = null;
      state.digestPreview = "Digest preview is unavailable in public view.";
      state.digestMarkdown = "Digest markdown export is unavailable in public view.";
      renderDigestWorkspace();
      setInlineFeedback("digest-feedback", "Digest workspace is admin-only.");
      setStatus(digestOnly ? "Public view is read-only." : "Dashboard is live.", "success");
      return;
    }

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
  if (isPublicView) {
    applyFiltersAndRender();
    return;
  }
  loadActivityPage();
}

function changePageSize(nextSize) {
  state.pagination.pageSize = nextSize;
  state.pagination.page = 1;
  if (isPublicView) {
    applyFiltersAndRender();
  } else {
    loadActivityPage();
  }
  setStatus(`Page size updated to ${nextSize}.`, "success");
}

function applyFiltersFromInputs() {
  state.filters.search = document.getElementById("search-filter").value.trim();
  state.filters.category = document.getElementById("category-filter").value;
  applyFiltersAndRender();
}

function clearFilters() {
  document.getElementById("search-filter").value = "";
  document.getElementById("category-filter").value = "";
  state.filters.search = "";
  state.filters.category = "";
  applyFiltersAndRender();
  setStatus("Filters cleared.", "success");
}

function bindStaticEvents() {
  const ingestButton = document.getElementById("ingest-button");
  if (!isPublicView) {
    ingestButton.addEventListener("click", runIngestion);
  } else {
    ingestButton.hidden = true;
  }
  const logoutForm = document.getElementById("logout-form");
  if (isPublicView) {
    logoutForm.hidden = true;
  }
  const digestRefreshButton = document.getElementById("digest-refresh-button");
  if (!isPublicView) {
    digestRefreshButton.addEventListener("click", () => loadDashboard({ digestOnly: true }));
    document.getElementById("digest-start-date").addEventListener("change", applyDigestWindowFromInputs);
    document.getElementById("digest-end-date").addEventListener("change", applyDigestWindowFromInputs);
  } else {
    digestRefreshButton.hidden = true;
  }
  document.getElementById("search-filter").addEventListener("input", applyFiltersFromInputs);
  document.getElementById("category-filter").addEventListener("change", applyFiltersFromInputs);
  document.getElementById("clear-filters-button").addEventListener("click", clearFilters);
  document.getElementById("batch-toolbar").addEventListener("click", (event) => {
    if (isPublicView) {
      return;
    }
    const reviewButton = event.target.closest("[data-batch-review-action]");
    if (reviewButton) {
      handleBatchReviewAction(reviewButton.dataset.batchReviewAction);
      return;
    }

    if (event.target.closest("[data-delete-selected-rejected]")) {
      openDeleteConfirm(Array.from(state.selectedActivityIds));
      return;
    }

    if (event.target.closest("[data-delete-visible-rejected]")) {
      openDeleteConfirm(
        getVisibleRejectedActivities().map((activity) => activity.id),
        "currently visible rejected activities",
      );
    }
  });
  document.getElementById("delete-cancel-button").addEventListener("click", closeDeleteConfirm);
  document.getElementById("delete-confirm-button").addEventListener("click", confirmDeleteActivities);
  document.querySelector("[data-close-delete-modal='true']").addEventListener("click", closeDeleteConfirm);
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
    if (isPublicView) {
      const card = event.target.closest("[data-activity-id]");
      if (card) {
        openDetailModal(card.dataset.activityId);
      }
      return;
    }

    const selectBox = event.target.closest("[data-select-activity-id]");
    if (selectBox) {
      event.stopPropagation();
      const card = selectBox.closest("[data-activity-id]");
      if (selectBox.checked) {
        state.selectedActivityIds.add(selectBox.dataset.selectActivityId);
        card?.classList.add("is-selected");
      } else {
        state.selectedActivityIds.delete(selectBox.dataset.selectActivityId);
        card?.classList.remove("is-selected");
      }
      updateBatchActions();
      return;
    }

    const deleteButton = event.target.closest("[data-delete-activity-id]");
    if (deleteButton) {
      event.stopPropagation();
      openDeleteConfirm([deleteButton.dataset.deleteActivityId]);
      return;
    }

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

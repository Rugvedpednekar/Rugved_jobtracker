const API_BASE = "";
const STATUS_ORDER = ["Wishlist", "Applied", "Interview", "Offered", "Accepted", "Rejected", "Archived", "Later"];
const TASK_STATUSES = ["open", "in_progress", "done"];

const state = {
  jobs: [],
  recommendedJobs: [],
  documents: [],
  parsedProfile: {},
  settings: {},
  dashboard: null,
  chatHistory: [],
  currentIntake: null,
  currentResumeDocument: null,
  activeDocument: null,
  activeJobDetails: null,
  jobDetailsEditMode: false,
  parsing: false,
  parseError: "",
  chatAvailable: true,
};

const dom = {
  loginScreen: document.getElementById("login-screen"),
  appShell: document.getElementById("app-shell"),
  loginForm: document.getElementById("login-form"),
  loginEmail: document.getElementById("login-email"),
  loginPassword: document.getElementById("login-password"),
  loginError: document.getElementById("login-error"),
  toast: document.getElementById("toast"),
  pageTitle: document.getElementById("page-title"),
  navButtons: document.querySelectorAll(".nav-btn"),
  panels: document.querySelectorAll(".section-panel"),
  logoutBtn: document.getElementById("logout-btn"),
  refreshDashboardBtn: document.getElementById("refresh-dashboard-btn"),
  jobsRefreshBtn: document.getElementById("jobs-refresh-btn"),
  discoverJobsBtn: document.getElementById("discover-jobs-btn"),
  openAddJobBtn: document.getElementById("open-add-job"),
  openAddJobJobsBtn: document.getElementById("open-add-job-jobs"),
  addJobModal: document.getElementById("add-job-modal"),
  addJobForm: document.getElementById("add-job-form"),
  closeAddJobModal: document.getElementById("close-add-job-modal"),
  cancelAddJobModal: document.getElementById("cancel-add-job-modal"),
  openParseJobBtns: [document.getElementById("open-parse-job"), document.getElementById("open-parse-job-jobs")],
  parseJobModal: document.getElementById("parse-job-modal"),
  closeParseJobModal: document.getElementById("close-parse-job-modal"),
  jobUrlInput: document.getElementById("job-url-input"),
  parseJobBtn: document.getElementById("parse-job-btn"),
  parseLoading: document.getElementById("parse-loading"),
  parseEmpty: document.getElementById("parse-empty"),
  parseError: document.getElementById("parse-error"),
  parseJobResults: document.getElementById("parse-job-results"),
  parsedCompany: document.getElementById("parsed-company"),
  parsedRole: document.getElementById("parsed-role"),
  parsedLocation: document.getElementById("parsed-location"),
  parsedMatchScore: document.getElementById("parsed-match-score"),
  parsedSkills: document.getElementById("parsed-skills"),
  parsedSummary: document.getElementById("parsed-summary"),
  parsedMatchSummary: document.getElementById("parsed-match-summary"),
  parsedTailoringNotes: document.getElementById("parsed-tailoring-notes"),
  jobActions: document.getElementById("job-actions"),
  generatedOutput: document.getElementById("generated-output"),
  jobDetailsModal: document.getElementById("job-details-modal"),
  closeJobDetailsModal: document.getElementById("close-job-details-modal"),
  editJobDetailsBtn: document.getElementById("edit-job-details-btn"),
  jobDetailsTitle: document.getElementById("job-details-title"),
  jobDetailsStatus: document.getElementById("job-details-status"),
  jobDetailsMatch: document.getElementById("job-details-match"),
  jobDetailsGrid: document.getElementById("job-details-grid"),
  jobDetailsForm: document.getElementById("job-details-form"),
  cancelJobDetailsEdit: document.getElementById("cancel-job-details-edit"),
  jobDetailsCompany: document.getElementById("job-details-company"),
  jobDetailsRole: document.getElementById("job-details-role"),
  jobDetailsStatusSelect: document.getElementById("job-details-status-select"),
  jobDetailsDate: document.getElementById("job-details-date"),
  jobDetailsLocation: document.getElementById("job-details-location"),
  jobDetailsSalary: document.getElementById("job-details-salary"),
  jobDetailsSponsor: document.getElementById("job-details-sponsor"),
  jobDetailsLink: document.getElementById("job-details-link"),
  jobDetailsMatchScore: document.getElementById("job-details-match-score"),
  jobDetailsNotes: document.getElementById("job-details-notes"),
  jobDetailsSummary: document.getElementById("job-details-summary"),
  jobDetailsTimestamps: document.getElementById("job-details-timestamps"),
  jobsSearchInput: document.getElementById("jobs-search-input"),
  jobsStatusFilter: document.getElementById("jobs-status-filter"),
  jobsList: document.getElementById("jobs-list"),
  totalCount: document.getElementById("total-count"),
  wishlistCount: document.getElementById("wishlist-count"),
  appliedCount: document.getElementById("applied-count"),
  interviewCount: document.getElementById("interview-count"),
  offeredCount: document.getElementById("offered-count"),
  acceptedCount: document.getElementById("accepted-count"),
  wishlistBadge: document.getElementById("wishlist-badge"),
  appliedBadge: document.getElementById("applied-badge"),
  interviewBadge: document.getElementById("interview-badge"),
  offeredBadge: document.getElementById("offered-badge"),
  acceptedBadge: document.getElementById("accepted-badge"),
  laterBadge: document.getElementById("later-badge"),
  wishlistColumn: document.getElementById("wishlist-column"),
  appliedColumn: document.getElementById("applied-column"),
  interviewColumn: document.getElementById("interview-column"),
  offeredColumn: document.getElementById("offered-column"),
  acceptedColumn: document.getElementById("accepted-column"),
  laterColumn: document.getElementById("later-column"),
  documentsList: document.getElementById("documents-list"),
  recentIntakes: document.getElementById("recent-intakes"),
  briefingSummary: document.getElementById("briefing-summary"),
  dailyBriefingText: document.getElementById("daily-briefing-text"),
  recommendedMeta: document.getElementById("recommended-meta"),
  recommendedJobsList: document.getElementById("recommended-jobs-list"),
  followupList: document.getElementById("followup-list"),
  focusList: document.getElementById("focus-list"),
  resumeBox: document.getElementById("resume-box"),
  resumeMeta: document.getElementById("resume-meta"),
  resumeUploadStatus: document.getElementById("resume-upload-status"),
  uploadResumeBtn: document.getElementById("upload-resume-btn"),
  replaceResumeBtn: document.getElementById("replace-resume-btn"),
  downloadResumeBtn: document.getElementById("download-resume-btn"),
  resumeUploadInput: document.getElementById("resume-upload-input"),
  parsedProfileOutput: document.getElementById("parsed-profile-output"),
  analyzeResumeBtn: document.getElementById("analyze-resume-btn"),
  saveResumeBtn: document.getElementById("save-resume-btn"),
  keywordBox: document.getElementById("keyword-box"),
  saveKeywordsBtn: document.getElementById("save-keywords-btn"),
  syncWindow: document.getElementById("sync-window"),
  preferredLocation: document.getElementById("preferred-location"),
  preferredLocations: document.getElementById("preferred-locations"),
  targetRoles: document.getElementById("target-roles"),
  minimumJobMatchScore: document.getElementById("minimum-job-match-score"),
  sponsorshipRequired: document.getElementById("sponsorship-required"),
  toneSetting: document.getElementById("tone-setting"),
  userNotes: document.getElementById("user-notes"),
  saveSettingsBtn: document.getElementById("save-settings-btn"),
  gmailSyncStatus: document.getElementById("gmail-sync-status"),
  emailParserInput: document.getElementById("email-parser-input"),
  emailJobLink: document.getElementById("email-job-link"),
  parsedEmailStatus: document.getElementById("parsed-email-status"),
  parsedEmailReason: document.getElementById("parsed-email-reason"),
  parseEmailBtn: document.getElementById("parse-email-btn"),
  chatMessages: document.getElementById("chat-messages"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  documentEditorModal: document.getElementById("document-editor-modal"),
  closeDocumentEditorModal: document.getElementById("close-document-editor-modal"),
  documentEditorTitle: document.getElementById("document-editor-title"),
  documentEditorSubtitle: document.getElementById("document-editor-subtitle"),
  documentEditorName: document.getElementById("document-editor-name"),
  documentEditorText: document.getElementById("document-editor-text"),
  saveDocumentBtn: document.getElementById("save-document-btn"),
  downloadDocumentPdfBtn: document.getElementById("download-document-pdf-btn")
};

let lastModalTrigger = null;

function showToast(message) {
  if (!dom.toast) return;
  dom.toast.textContent = message;
  dom.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => dom.toast.classList.add("hidden"), 2400);
}

function safeText(value, fallback = "—") {
  return value || fallback;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDateValue(value, fallback = "Not specified") {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

function formatDateTimeValue(value, fallback = "Not specified") {
  if (!value) return fallback;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function renderDetailValue(value, fallback = "Not specified") {
  const text = value ? escapeHtml(value) : escapeHtml(fallback);
  return `<div class="job-detail-value${value ? "" : " is-fallback"}">${text}</div>`;
}

function renderDetailLink(value, fallback = "Not specified") {
  if (!value) return renderDetailValue("", fallback);
  const href = escapeHtml(value);
  return `<div class="job-detail-value"><a class="job-detail-link" href="${href}" target="_blank" rel="noopener noreferrer">${href}</a></div>`;
}

function renderDetailList(items, fallback = "Not specified") {
  if (!items?.length) return renderDetailValue("", fallback);
  return `<div class="chip-row">${items.map(item => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div>`;
}

function renderParsedProfile(profile = {}) {
  const cards = [
    ["Summary", profile.summary || "Not specified", "full-span"],
    ["Skills", Array.isArray(profile.skills) ? profile.skills : [], "chips"],
    ["Target roles", Array.isArray(profile.roles) ? profile.roles : [], "chips"],
    ["Domains", Array.isArray(profile.domains) ? profile.domains : [], "chips"],
    ["Locations", Array.isArray(profile.locations) ? profile.locations : [], "chips"],
    ["Experience level", profile.experienceLevel || "Not specified", ""],
    ["Education", Array.isArray(profile.education) ? profile.education : [], "chips"]
  ];
  dom.parsedProfileOutput.innerHTML = `<div class="parsed-profile-grid">${cards.map(([label, value, type]) => `
    <section class="parsed-profile-card${type === "full-span" ? " full-span" : ""}">
      <div class="job-detail-label">${label}</div>
      ${type === "chips" ? renderDetailList(value, "Not specified") : renderDetailValue(value, "Not specified")}
    </section>
  `).join("")}</div>`;
}

function setResumeMeta(profile) {
  const source = profile?.current_resume_document?.name || state.currentResumeDocument?.name || "No saved resume yet";
  const updated = profile?.current_resume_document?.updated_at || state.currentResumeDocument?.updated_at;
  dom.resumeMeta.textContent = updated
    ? `${source} • last saved ${formatDateTimeValue(updated)}`
    : `${source}. Paste text or upload a file to build your working resume.`;
}

async function downloadPdf(title, contentText, fileName) {
  const response = await fetch(`${API_BASE}/api/documents/export-pdf`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content_text: contentText, file_name: fileName })
  });
  if (!response.ok) {
    const data = await safeJSON(response);
    throw new Error(data.detail || "Unable to export PDF");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName || `${title}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function emptyState(title, message = "") {
  return `<div class="empty-state"><strong>${title}</strong>${message ? `<p>${message}</p>` : ""}</div>`;
}

function showLogin() {
  dom.loginScreen.classList.remove("hidden");
  dom.appShell.classList.add("hidden");
}

function showApp() {
  dom.loginScreen.classList.add("hidden");
  dom.appShell.classList.remove("hidden");
}

function setSection(sectionId) {
  dom.panels.forEach(panel => panel.classList.toggle("hidden", panel.id !== sectionId));
  dom.navButtons.forEach(button => button.classList.toggle("active", button.dataset.section === sectionId));
  if (dom.pageTitle) {
    const active = Array.from(dom.navButtons).find(button => button.dataset.section === sectionId);
    dom.pageTitle.textContent = active ? active.textContent.trim() : "Tracker";
  }
}

async function safeJSON(response) {
  try {
    return await response.json();
  } catch {
    return {};
  }
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });
  const data = await safeJSON(response);
  if (!response.ok) {
    throw new Error(data.detail || data.message || "Request failed");
  }
  return data;
}

function normalizeKeywordLines(text) {
  return text.split(/\n|,/).map(item => item.trim()).filter(Boolean);
}

function renderChips(items = []) {
  if (!items.length) return `<span class="muted">No items yet.</span>`;
  return items.map(item => `<span class="chip">${item}</span>`).join("");
}

function renderTrackerCard(job) {
  return `
    <article class="job-card-mini">
      <h4>${safeText(job.company, "Unknown company")}</h4>
      <p>${safeText(job.role, "Unknown role")}</p>
      <div class="chip-row">
        <span class="status-pill">${safeText(job.status, "Applied")}</span>
        ${job.ai_match_score ? `<span class="chip">Match ${job.ai_match_score}%</span>` : ""}
      </div>
    </article>
  `;
}

function renderBoardColumn(element, items, label) {
  element.innerHTML = items.length
    ? items.map(renderTrackerCard).join("")
    : emptyState(`No ${label.toLowerCase()} jobs yet`, "This column will populate when a real job reaches this stage.");
}

function renderDashboard() {
  const data = state.dashboard || { stats: {}, columns: {}, daily_briefing: {} };
  const stats = data.stats || {};
  dom.totalCount.textContent = stats.total_jobs || 0;
  dom.wishlistCount.textContent = stats.wishlist_count || 0;
  dom.appliedCount.textContent = stats.applied_count || 0;
  dom.interviewCount.textContent = stats.interview_count || 0;
  dom.offeredCount.textContent = stats.offered_count || 0;
  dom.acceptedCount.textContent = stats.accepted_count || 0;
  dom.wishlistBadge.textContent = stats.wishlist_count || 0;
  dom.appliedBadge.textContent = stats.applied_count || 0;
  dom.interviewBadge.textContent = stats.interview_count || 0;
  dom.offeredBadge.textContent = stats.offered_count || 0;
  dom.acceptedBadge.textContent = stats.accepted_count || 0;
  dom.laterBadge.textContent = stats.later_count || 0;
  renderBoardColumn(dom.wishlistColumn, data.columns?.Wishlist || [], "Wishlist");
  renderBoardColumn(dom.appliedColumn, data.columns?.Applied || [], "Applied");
  renderBoardColumn(dom.interviewColumn, data.columns?.Interview || [], "Interview");
  renderBoardColumn(dom.offeredColumn, data.columns?.Offered || [], "Offered");
  renderBoardColumn(dom.acceptedColumn, data.columns?.Accepted || [], "Accepted");
  renderBoardColumn(dom.laterColumn, data.columns?.Later || [], "Later");

  const briefing = data.daily_briefing || {};
  dom.briefingSummary.textContent = briefing.summary || "No briefing available yet.";
  dom.dailyBriefingText.textContent = briefing.summary || "No briefing available yet.";
  dom.followupList.innerHTML = (briefing.follow_up_suggestions || []).length
    ? briefing.follow_up_suggestions.map(item => `<div class="list-item">${item}</div>`).join("")
    : emptyState("No follow-ups yet", "Your actual reminders will appear here after activity is recorded.");
  dom.focusList.innerHTML = (briefing.focus_today || []).length
    ? briefing.focus_today.map(item => `<div class="list-item">${item}</div>`).join("")
    : emptyState("No focus items yet", "Once applications move or become stale, the highest-priority next steps will appear here.");
  dom.recentIntakes.innerHTML = (data.recent_intakes || []).length
    ? data.recent_intakes.map(item => `<div class="list-item"><strong>${safeText(item.company)}</strong><p class="muted">${safeText(item.role)} • ${safeText(item.location, "Location pending")}</p></div>`).join("")
    : emptyState("No parsed jobs yet", "Parsed job links will appear here after successful intake.");
  if (data.recommended_today) {
    state.recommendedJobs = data.recommended_today;
  }
  renderRecommendedJobs();
}

function renderRecommendedJobs() {
  const jobs = state.recommendedJobs || [];
  dom.recommendedMeta.textContent = jobs.length
    ? `${jobs.length} high-match roles surfaced from the latest scan.`
    : "No high-score matches yet. Run the morning scan after saving your profile and preferences.";
  dom.recommendedJobsList.innerHTML = jobs.length ? jobs.map(job => `
    <article class="recommended-card panel" data-recommended-job-id="${job.id}">
      <div class="section-head compact">
        <div>
          <p class="eyebrow">${safeText(job.company, "Unknown company")}</p>
          <h3>${safeText(job.role, "Unknown role")}</h3>
        </div>
        <div class="score-badge">${job.score || 0}/100</div>
      </div>
      <p class="muted">${safeText(job.location)} ${job.domain ? `• ${job.domain}` : ""}</p>
      <p>${safeText(job.summary, "No summary available.")}</p>
      <div>
        <p class="label">Why it matches</p>
        <div class="chip-row">${renderChips(job.match_reasons || [])}</div>
      </div>
      <div>
        <p class="label">Missing skills / gaps</p>
        <div class="chip-row">${renderChips(job.missing_points || [])}</div>
      </div>
      <div class="inline-actions">
        <button class="btn btn-primary" data-recommended-action="apply" type="button">Apply</button>
        <button class="btn btn-secondary" data-recommended-action="save_to_wishlist" type="button">Save to wishlist</button>
        <button class="btn btn-ghost" data-recommended-action="dismiss" type="button">Dismiss</button>
        <button class="btn btn-secondary" data-recommended-action="match_resume" type="button">Match resume</button>
        <button class="btn btn-secondary" data-recommended-action="generate_resume" type="button">Generate resume</button>
        <button class="btn btn-secondary" data-recommended-action="generate_cover_letter" type="button">Generate cover letter</button>
      </div>
    </article>
  `).join("") : emptyState("No recommendations yet", "Run the morning scan or connect data sources to surface real roles.");
}


function filteredJobs() {
  const query = dom.jobsSearchInput.value.trim().toLowerCase();
  const statusFilter = dom.jobsStatusFilter.value;
  return state.jobs.filter(job => {
    const haystack = [job.company, job.role, job.notes, job.field, job.location, job.job_summary].join(" ").toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    const matchesStatus = !statusFilter || job.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
}

function renderJobsList() {
  const jobs = filteredJobs();
  if (!jobs.length) {
    const hasJobs = state.jobs.length > 0;
    dom.jobsList.innerHTML = hasJobs
      ? emptyState("No jobs match the current filters", "Try clearing the search or status filter.")
      : emptyState("No jobs saved yet", "Add a job manually or parse a live job link to start tracking.");
    return;
  }
  dom.jobsList.innerHTML = `
    <div class="table-head table-row">
      <span>Company / Role</span>
      <span>Status</span>
      <span>Location</span>
      <span>Match</span>
      <span>Actions</span>
    </div>
    ${jobs.map(job => `
      <div class="table-row" data-job-id="${job.id}">
        <div>
          <button class="job-primary-button" data-action="open-details" type="button" aria-label="Open details for ${escapeHtml(safeText(job.company, "job"))}">
            <strong>${safeText(job.company)}</strong>
            <p class="muted">${safeText(job.role)}<br><span class="job-summary-preview">${safeText(job.job_summary, "No summary saved")}</span></p>
          </button>
        </div>
        <div>
          <select class="field job-status-select" data-action="status">
            ${STATUS_ORDER.map(status => `<option value="${status}" ${job.status === status ? "selected" : ""}>${status}</option>`).join("")}
          </select>
        </div>
        <div>${safeText(job.location)}</div>
        <div>${job.ai_match_score ? `${job.ai_match_score}%` : "—"}</div>
        <div class="inline-actions">
          <button class="btn btn-ghost" data-action="delete" type="button">Delete</button>
        </div>
      </div>
    `).join("")}
  `;
}

function openJobDetailsModal(job, trigger = null) {
  if (!job || !dom.jobDetailsModal) return;
  state.activeJobDetails = job;
  state.jobDetailsEditMode = false;
  lastModalTrigger = trigger || document.activeElement;
  const title = [job.company, job.role].filter(Boolean).join(" — ") || "Job details";
  dom.jobDetailsTitle.textContent = title;
  dom.jobDetailsStatus.textContent = safeText(job.status, "Not specified");
  dom.jobDetailsMatch.textContent = job.ai_match_score ? `Match ${job.ai_match_score}%` : "Match not available";
  const cards = [
    ["Company name", renderDetailValue(job.company, "Not specified")],
    ["Role title", renderDetailValue(job.role, "Not specified")],
    ["Application status", renderDetailValue(job.status, "Not specified")],
    ["When I applied", renderDetailValue(formatDateValue(job.date, "Not specified"), "Not specified")],
    ["Location", renderDetailValue(job.location, "Not specified")],
    ["Salary", renderDetailValue(job.salary, "Not specified")],
    ["Sponsorship info", renderDetailValue(job.sponsor || job.sponsorship, "Not specified")],
    ["Job link", renderDetailLink(job.link, "Not specified")],
    ["Source", renderDetailValue(job.source, "Not specified")],
    ["Match score", renderDetailValue(job.ai_match_score ? `${job.ai_match_score}%` : "", "Not specified")],
    ["Created date", renderDetailValue(formatDateTimeValue(job.created_at, "Not specified"), "Not specified")],
    ["Updated date", renderDetailValue(formatDateTimeValue(job.updated_at, "Not specified"), "Not specified")],
    ["Skills", renderDetailList(job.skills, "No skills parsed"), "full-span"],
    ["Notes", renderDetailValue(job.notes, "No notes added"), "full-span"],
    ["Summary / parsed description", renderDetailValue(job.job_summary, "Not specified"), "full-span"],
    ["Match summary", renderDetailValue(job.ai_match_summary, "Not specified"), "full-span"]
  ];
  dom.jobDetailsGrid.innerHTML = cards.map(([label, valueHtml, span]) => `
    <section class="job-detail-card${span ? ` ${span}` : ""}">
      <div class="job-detail-label">${label}</div>
      ${valueHtml}
    </section>
  `).join("");
  dom.jobDetailsGrid.classList.remove("hidden");
  dom.jobDetailsForm.classList.add("hidden");
  dom.editJobDetailsBtn.classList.remove("hidden");
  dom.jobDetailsModal.classList.remove("hidden");
  dom.jobDetailsModal.setAttribute("aria-hidden", "false");
  dom.closeJobDetailsModal.focus();
}

function populateJobDetailsForm(job) {
  dom.jobDetailsCompany.value = job.company || "";
  dom.jobDetailsRole.value = job.role || "";
  dom.jobDetailsStatusSelect.innerHTML = STATUS_ORDER.map(status => `<option value="${status}" ${job.status === status ? "selected" : ""}>${status}</option>`).join("");
  dom.jobDetailsDate.value = job.date || "";
  dom.jobDetailsLocation.value = job.location || "";
  dom.jobDetailsSalary.value = job.salary || "";
  dom.jobDetailsSponsor.value = job.sponsor || "";
  dom.jobDetailsLink.value = job.link || "";
  dom.jobDetailsMatchScore.value = job.ai_match_score ?? "";
  dom.jobDetailsNotes.value = job.notes || "";
  dom.jobDetailsSummary.value = job.job_summary || "";
  dom.jobDetailsTimestamps.textContent = `Created ${formatDateTimeValue(job.created_at, "Not specified")} • Updated ${formatDateTimeValue(job.updated_at, "Not specified")}`;
}

function enableJobDetailsEditMode() {
  if (!state.activeJobDetails) return;
  state.jobDetailsEditMode = true;
  populateJobDetailsForm(state.activeJobDetails);
  dom.jobDetailsGrid.classList.add("hidden");
  dom.jobDetailsForm.classList.remove("hidden");
  dom.editJobDetailsBtn.classList.add("hidden");
  dom.jobDetailsCompany.focus();
}

function disableJobDetailsEditMode() {
  state.jobDetailsEditMode = false;
  dom.jobDetailsGrid.classList.remove("hidden");
  dom.jobDetailsForm.classList.add("hidden");
  dom.editJobDetailsBtn.classList.remove("hidden");
}

function closeJobDetailsModal() {
  if (!dom.jobDetailsModal) return;
  disableJobDetailsEditMode();
  dom.jobDetailsModal.classList.add("hidden");
  dom.jobDetailsModal.setAttribute("aria-hidden", "true");
  if (lastModalTrigger && typeof lastModalTrigger.focus === "function") {
    lastModalTrigger.focus();
  }
}

function openDocumentEditor(doc, subtitle = "") {
  if (!doc) return;
  state.activeDocument = { ...doc };
  lastModalTrigger = document.activeElement;
  dom.documentEditorTitle.textContent = doc.name || "Document preview";
  dom.documentEditorSubtitle.textContent = subtitle || "Review and refine this generated draft before exporting it.";
  dom.documentEditorName.value = doc.name || "";
  dom.documentEditorText.value = doc.content_text || "";
  dom.documentEditorModal.classList.remove("hidden");
  dom.documentEditorModal.setAttribute("aria-hidden", "false");
  dom.documentEditorText.focus();
}

function closeActiveDocumentEditor() {
  dom.documentEditorModal.classList.add("hidden");
  dom.documentEditorModal.setAttribute("aria-hidden", "true");
  state.activeDocument = null;
  if (lastModalTrigger && typeof lastModalTrigger.focus === "function") {
    lastModalTrigger.focus();
  }
}

function renderProfile() {
  renderParsedProfile(state.parsedProfile || {});
  setResumeMeta({});
}

function renderSettings() {
  dom.syncWindow.value = String(state.settings.sync_window_hours || 24);
  dom.preferredLocation.value = state.settings.preferred_location || "";
  dom.preferredLocations.value = (state.settings.preferred_locations || []).join("\n");
  dom.targetRoles.value = (state.settings.target_roles || []).join("\n");
  dom.minimumJobMatchScore.value = String(state.settings.minimum_job_match_score || 72);
  dom.sponsorshipRequired.checked = Boolean(state.settings.sponsorship_required);
  dom.userNotes.value = state.settings.user_notes || "";
  dom.toneSetting.value = state.settings.tone || "concise";
}

function renderDocuments() {
  dom.documentsList.innerHTML = state.documents.length
    ? state.documents.map(doc => `
      <div class="document-card">
        <div class="document-card-head">
          <div>
            <strong>${safeText(doc.name)}</strong>
            <p class="muted">${safeText(doc.doc_type)} • Updated ${formatDateTimeValue(doc.updated_at, "recently")}</p>
          </div>
          <button class="btn btn-secondary" type="button" data-action="open-document" data-document-id="${doc.id}">Open</button>
        </div>
        <p class="document-preview">${safeText(doc.content_text.slice(0, 320), "No content")}...</p>
      </div>
    `).join("")
    : emptyState("No saved documents yet", "Generated resumes, cover letters, and drafts will appear here after you create them.");
}

function renderChatHistory() {
  if (!state.chatAvailable) {
    dom.chatMessages.innerHTML = emptyState("Assistant unavailable", "The chat backend is not connected right now, so the UI will not fake responses or actions.");
    return;
  }
  dom.chatMessages.innerHTML = state.chatHistory.length
    ? state.chatHistory.map(item => `
      <div class="chat-bubble ${item.role === "assistant" ? "assistant" : "user"}">
        <div class="chat-bubble-meta">${item.role === "assistant" ? "Assistant" : "You"}</div>
        <p>${item.message}</p>
      </div>
    `).join("")
    : emptyState("No conversation yet", "Ask about your jobs, profile, or documents when the assistant backend is available.");
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

function populateEmailJobDropdown() {
  dom.emailJobLink.innerHTML = `<option value="">Optionally link to a job</option>${state.jobs.map(job => `<option value="${job.id}">${job.company} — ${job.role}</option>`).join("")}`;
}

function renderParseResults() {
  const intake = state.currentIntake;
  dom.parseLoading.classList.toggle("hidden", !state.parsing);
  dom.parseError.classList.toggle("hidden", !state.parseError);
  dom.parseError.textContent = state.parseError || "";
  const showEmpty = !state.parsing && !state.parseError && !intake;
  dom.parseEmpty.classList.toggle("hidden", !showEmpty);
  if (!intake) {
    dom.parseJobResults.classList.add("hidden");
    dom.generatedOutput.textContent = "Choose an action to generate or save an output.";
    return;
  }
  const parsed = intake.parsed_job || {};
  const match = intake.match_analysis || {};
  dom.parseJobResults.classList.remove("hidden");
  dom.parsedCompany.textContent = safeText(parsed.company);
  dom.parsedRole.textContent = safeText(parsed.role);
  dom.parsedLocation.textContent = safeText(parsed.location);
  dom.parsedMatchScore.textContent = match.score ? `${match.score}%` : "—";
  dom.parsedSkills.innerHTML = renderChips(parsed.skills || []);
  dom.parsedSummary.textContent = safeText(parsed.summary);
  dom.parsedMatchSummary.textContent = safeText(match.summary, "No match summary yet.");
  const tailoringNotes = match.tailoring_notes || [];
  dom.parsedTailoringNotes.classList.toggle("hidden", !tailoringNotes.length);
  dom.parsedTailoringNotes.innerHTML = tailoringNotes.length
    ? `<p class="label">Tailoring guidance</p><div class="chip-row">${tailoringNotes.map(note => `<span class="chip">${escapeHtml(note)}</span>`).join("")}</div>`
    : "";
  dom.jobActions.innerHTML = (intake.suggested_actions || []).length ? (intake.suggested_actions || []).map(action => `
    <button class="action-card" type="button" data-action-id="${action.id}">
      <strong>${action.label}</strong>
      <p class="muted">${action.description}</p>
    </button>
  `).join("") : emptyState("No actions available", "This parse completed, but no follow-up actions were returned by the backend.");
  dom.generatedOutput.innerHTML = "Choose an action to generate or save an output.";
}


async function loadDashboard() {
  state.dashboard = await api("/api/dashboard/simple");
  dom.gmailSyncStatus.textContent = state.dashboard.gmail_sync?.message || "Not configured";
  renderDashboard();
}

async function loadJobs() {
  state.jobs = await api("/api/jobs");
  renderJobsList();
  populateEmailJobDropdown();
}

async function loadRecommendedJobs() {
  state.recommendedJobs = await api("/api/jobs/recommended");
  renderRecommendedJobs();
}

async function loadProfile() {
  const profile = await api("/api/profile");
  dom.resumeBox.value = profile.resume_text || "";
  state.parsedProfile = profile.parsed_profile || {};
  state.chatHistory = profile.chat_history || [];
  state.chatAvailable = true;
  state.documents = profile.documents || [];
  state.currentResumeDocument = profile.current_resume_document || null;
  renderProfile();
  setResumeMeta(profile);
  renderChatHistory();
  renderDocuments();
  const keywords = await api("/api/keywords");
  dom.keywordBox.value = (keywords.keywords || []).join("\n");
}

async function loadSettings() {
  const data = await api("/api/settings");
  state.settings = data.settings || {};
  dom.gmailSyncStatus.textContent = data.gmail_sync?.message || "Not configured";
  renderSettings();
}

async function loadDocuments() {
  state.documents = await api("/api/documents");
  state.currentResumeDocument = state.documents.find(doc => doc.doc_type === "resume") || state.currentResumeDocument;
  renderDocuments();
  setResumeMeta({});
}

async function loadAllData() {
  await Promise.all([loadDashboard(), loadJobs(), loadRecommendedJobs(), loadProfile(), loadSettings(), loadDocuments()]);
}

async function checkAuth() {
  try {
    await api("/api/auth/me");
    showApp();
    await loadAllData();
  } catch {
    showLogin();
  }
}

async function handleLogin(event) {
  event.preventDefault();
  dom.loginError.classList.add("hidden");
  try {
    await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: dom.loginEmail.value.trim(), password: dom.loginPassword.value })
    });
    showApp();
    await loadAllData();
    setSection("tracker");
    showToast("Logged in");
  } catch (error) {
    dom.loginError.textContent = error.message;
    dom.loginError.classList.remove("hidden");
  }
}

async function handleLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch {
    // ignore
  }
  dom.loginForm.reset();
  showLogin();
  showToast("Logged out");
}

async function handleAddJob(event) {
  event.preventDefault();
  const formData = new FormData(dom.addJobForm);
  const payload = Object.fromEntries(formData.entries());
  payload.date = payload.date || new Date().toISOString().slice(0, 10);
  payload.skills = [];
  payload.metadata_json = {};
  try {
    await api("/api/jobs", { method: "POST", body: JSON.stringify(payload) });
    dom.addJobForm.reset();
    dom.addJobModal.classList.add("hidden");
    await Promise.all([loadDashboard(), loadJobs()]);
    showToast("Job added");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleJobListClick(event) {
  const row = event.target.closest("[data-job-id]");
  if (!row) return;
  if (event.target.closest('[data-action="open-details"]')) {
    const job = state.jobs.find(item => item.id === row.dataset.jobId);
    openJobDetailsModal(job, event.target.closest('[data-action="open-details"]'));
    return;
  }
  if (event.target.dataset.action === "delete") {
    try {
      await api(`/api/jobs/${row.dataset.jobId}`, { method: "DELETE" });
      await Promise.all([loadDashboard(), loadJobs()]);
      showToast("Job deleted");
    } catch (error) {
      showToast(error.message);
    }
  }
}

async function handleJobListChange(event) {
  const row = event.target.closest("[data-job-id]");
  if (!row || event.target.dataset.action !== "status") return;
  try {
    await api(`/api/jobs/${row.dataset.jobId}`, {
      method: "PUT",
      body: JSON.stringify({ status: event.target.value })
    });
    await Promise.all([loadDashboard(), loadJobs()]);
    showToast("Status updated");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleResumeAnalyze() {
  try {
    const data = await api("/api/resume/analyze", {
      method: "POST",
      body: JSON.stringify({ resume_text: dom.resumeBox.value })
    });
    state.parsedProfile = data.parsed_profile || {};
    renderProfile();
    showToast("Resume analyzed");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleResumeUpload(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch(`${API_BASE}/api/resume/upload`, {
      method: "POST",
      credentials: "include",
      body: formData
    });
    const data = await safeJSON(response);
    if (!response.ok) throw new Error(data.detail || "Unable to upload resume");
    dom.resumeBox.value = data.resume_text || "";
    state.parsedProfile = data.parsed_profile || {};
    renderProfile();
    dom.resumeUploadStatus.textContent = `Loaded ${data.filename} using ${data.parser.toUpperCase()} extraction. Review and save when ready.`;
    showToast("Resume uploaded");
  } catch (error) {
    dom.resumeUploadStatus.textContent = error.message;
    showToast(error.message);
  } finally {
    event.target.value = "";
  }
}

async function handleResumeSave() {
  try {
    const data = await api("/api/resume/save", {
      method: "POST",
      body: JSON.stringify({ resume_text: dom.resumeBox.value, parsed_profile: state.parsedProfile })
    });
    state.parsedProfile = data.parsed_profile || state.parsedProfile;
    await Promise.all([loadProfile(), loadDocuments()]);
    dom.resumeUploadStatus.textContent = "Resume saved to your profile workspace.";
    showToast("Resume saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleResumeDownload() {
  const content = dom.resumeBox.value.trim();
  if (!content) {
    showToast("Add or upload resume content first");
    return;
  }
  try {
    await downloadPdf("Primary Resume", content, "primary_resume.pdf");
    showToast("Resume PDF downloaded");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleKeywordsSave() {
  try {
    await api("/api/keywords", {
      method: "POST",
      body: JSON.stringify({ keywords: normalizeKeywordLines(dom.keywordBox.value) })
    });
    showToast("Keywords saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleSettingsSave() {
  try {
    const data = await api("/api/settings", {
      method: "POST",
      body: JSON.stringify({
        sync_window_hours: Number(dom.syncWindow.value || 24),
        preferred_location: dom.preferredLocation.value,
        preferred_locations: normalizeKeywordLines(dom.preferredLocations.value),
        target_roles: normalizeKeywordLines(dom.targetRoles.value),
        sponsorship_required: dom.sponsorshipRequired.checked,
        minimum_job_match_score: Number(dom.minimumJobMatchScore.value || 72),
        user_notes: dom.userNotes.value,
        tone: dom.toneSetting.value
      })
    });
    state.settings = data.settings || {};
    renderSettings();
    dom.gmailSyncStatus.textContent = data.gmail_sync?.message || "Not configured";
    showToast("Settings saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleDiscoverJobs() {
  const button = dom.discoverJobsBtn;
  button.disabled = true;
  button.textContent = "Scanning...";
  try {
    const data = await api("/api/jobs/discover", { method: "POST" });
    state.recommendedJobs = data.recommended_jobs || [];
    renderRecommendedJobs();
    await Promise.all([loadDashboard()]);
    showToast(`Morning scan finished: ${data.recommended_count || 0} matches`);
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Run morning scan";
  }
}

async function handleRecommendedJobClick(event) {
  const button = event.target.closest("[data-recommended-action]");
  const card = event.target.closest("[data-recommended-job-id]");
  if (!button || !card) return;
  try {
    const data = await api(`/api/jobs/recommended/${card.dataset.recommendedJobId}/action`, {
      method: "POST",
      body: JSON.stringify({ action: button.dataset.recommendedAction })
    });
    if (data.document?.content_text) {
      dom.parseJobModal.classList.remove("hidden");
      dom.generatedOutput.innerHTML = `Generated <strong>${escapeHtml(data.document.name)}</strong>. Review and edit it before exporting.`;
      openDocumentEditor(data.document, `Tailored for ${card.querySelector("h3")?.textContent || "this role"}.`);
    } else if (data.match_analysis) {
      dom.generatedOutput.innerHTML = `<strong>Match summary</strong><p class="muted">${escapeHtml(data.match_analysis.summary || "Resume comparison ready.")}</p>`;
      dom.parseJobModal.classList.remove("hidden");
    }
    await Promise.all([loadRecommendedJobs(), loadDashboard(), loadJobs(), loadDocuments()]);
    showToast("Recommended job action completed");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleEmailParse() {
  try {
    const data = await api("/api/email/parse", {
      method: "POST",
      body: JSON.stringify({ email_text: dom.emailParserInput.value, job_id: dom.emailJobLink.value || null })
    });
    dom.parsedEmailStatus.textContent = data.parsed?.status || "-";
    dom.parsedEmailReason.textContent = data.parsed?.reason || "-";
    await Promise.all([loadDashboard(), loadJobs()]);
    showToast("Email parsed");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleChat(event) {
  event.preventDefault();
  const message = dom.chatInput.value.trim();
  if (!message) return;
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
    state.chatAvailable = true;
    state.chatHistory = data.history || [];
    dom.chatInput.value = "";
    renderChatHistory();
  } catch (error) {
    state.chatAvailable = false;
    renderChatHistory();
    showToast(error.message);
  }
}

function resetParseState() {
  state.currentIntake = null;
  state.parsing = false;
  state.parseError = "";
  renderParseResults();
}

function openParseModal() {
  resetParseState();
  dom.parseJobModal.classList.remove("hidden");
  dom.jobUrlInput.focus();
}

function closeParseModal() {
  dom.parseJobModal.classList.add("hidden");
}

async function handleParseJob() {
  if (!dom.jobUrlInput.value.trim()) {
    showToast("Enter a job URL first");
    return;
  }
  state.parsing = true;
  state.parseError = "";
  state.currentIntake = null;
  renderParseResults();
  dom.parseJobBtn.disabled = true;
  try {
    const data = await api("/api/jobs/parse-link", {
      method: "POST",
      body: JSON.stringify({ url: dom.jobUrlInput.value.trim() })
    });
    state.currentIntake = data;
    showToast("Job parsed");
  } catch (error) {
    state.parseError = error.message || "Unable to parse job link.";
    showToast(state.parseError);
  } finally {
    state.parsing = false;
    dom.parseJobBtn.disabled = false;
    renderParseResults();
  }
}

async function handleParsedActionClick(event) {
  const button = event.target.closest("[data-action-id]");
  if (!button || !state.currentIntake) return;
  const action = button.dataset.actionId;
  dom.generatedOutput.innerHTML = "Working on your request...";
  try {
    const data = await api("/api/jobs/action", {
      method: "POST",
      body: JSON.stringify({ intake_id: state.currentIntake.intake_id, action })
    });
    if (data.document?.content_text) {
      const parsedJob = state.currentIntake?.parsed_job || {};
      dom.generatedOutput.innerHTML = `Generated <strong>${escapeHtml(data.document.name)}</strong>. Opened editable preview for ${escapeHtml(parsedJob.company || "this job")}.`;
      openDocumentEditor(data.document, `Tailored for ${parsedJob.role || "the parsed role"} at ${parsedJob.company || "the target company"}.`);
    } else if (data.match_analysis) {
      dom.generatedOutput.innerHTML = `
        <strong>Resume match updated</strong>
        <p class="muted">${escapeHtml(data.match_analysis.summary || "Resume comparison generated.")}</p>
        <div class="chip-row">${(data.match_analysis.matched_skills || []).map(skill => `<span class="chip">${escapeHtml(skill)}</span>`).join("")}</div>
      `;
    } else if (data.job) {
      dom.generatedOutput.innerHTML = `Saved <strong>${escapeHtml(data.job.company)}</strong> — ${escapeHtml(data.job.role)} as ${escapeHtml(data.job.status)}.`;
    } else {
      dom.generatedOutput.innerHTML = "Action saved.";
    }
    await Promise.all([loadDashboard(), loadJobs(), loadDocuments()]);
    showToast("Action completed");
  } catch (error) {
    dom.generatedOutput.textContent = error.message;
    showToast(error.message);
  }
}

async function handleJobDetailsSave(event) {
  event.preventDefault();
  if (!state.activeJobDetails) return;
  try {
    const updatedJob = await api(`/api/jobs/${state.activeJobDetails.id}`, {
      method: "PUT",
      body: JSON.stringify({
        company: dom.jobDetailsCompany.value.trim(),
        role: dom.jobDetailsRole.value.trim(),
        status: dom.jobDetailsStatusSelect.value,
        date: dom.jobDetailsDate.value || null,
        location: dom.jobDetailsLocation.value.trim(),
        salary: dom.jobDetailsSalary.value.trim(),
        sponsor: dom.jobDetailsSponsor.value.trim(),
        link: dom.jobDetailsLink.value.trim(),
        notes: dom.jobDetailsNotes.value.trim(),
        job_summary: dom.jobDetailsSummary.value.trim(),
        ai_match_score: dom.jobDetailsMatchScore.value === "" ? null : Number(dom.jobDetailsMatchScore.value)
      })
    });
    state.activeJobDetails = updatedJob;
    disableJobDetailsEditMode();
    await Promise.all([loadJobs(), loadDashboard()]);
    openJobDetailsModal(updatedJob, lastModalTrigger);
    showToast("Job details updated");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleDocumentsClick(event) {
  const button = event.target.closest('[data-action="open-document"]');
  if (!button) return;
  const document = state.documents.find(item => item.id === button.dataset.documentId);
  openDocumentEditor(document);
}

async function handleDocumentSave() {
  if (!state.activeDocument) return;
  try {
    const updated = await api(`/api/documents/${state.activeDocument.id}`, {
      method: "PUT",
      body: JSON.stringify({
        name: dom.documentEditorName.value.trim(),
        content_text: dom.documentEditorText.value
      })
    });
    state.activeDocument = updated;
    await loadDocuments();
    showToast("Document saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleDocumentDownload() {
  const title = dom.documentEditorName.value.trim() || state.activeDocument?.name || "Document";
  const content = dom.documentEditorText.value.trim();
  if (!content) {
    showToast("Document is empty");
    return;
  }
  try {
    await downloadPdf(title, content, `${title.replace(/\s+/g, "_").toLowerCase()}.pdf`);
    showToast("PDF downloaded");
  } catch (error) {
    showToast(error.message);
  }
}

function attachEvents() {
  dom.loginForm.addEventListener("submit", handleLogin);
  dom.logoutBtn.addEventListener("click", handleLogout);
  dom.navButtons.forEach(button => button.addEventListener("click", () => setSection(button.dataset.section)));
  dom.refreshDashboardBtn.addEventListener("click", () => Promise.all([loadDashboard()]));
  dom.jobsRefreshBtn.addEventListener("click", () => Promise.all([loadJobs(), loadDashboard()]));
  dom.discoverJobsBtn.addEventListener("click", handleDiscoverJobs);
  const openAddJobModal = () => dom.addJobModal.classList.remove("hidden");
  dom.openAddJobBtn.addEventListener("click", openAddJobModal);
  dom.openAddJobJobsBtn.addEventListener("click", openAddJobModal);
  dom.closeAddJobModal.addEventListener("click", () => dom.addJobModal.classList.add("hidden"));
  dom.cancelAddJobModal.addEventListener("click", () => dom.addJobModal.classList.add("hidden"));
  dom.addJobForm.addEventListener("submit", handleAddJob);
  dom.openParseJobBtns.forEach(button => button && button.addEventListener("click", openParseModal));
  dom.closeParseJobModal.addEventListener("click", closeParseModal);
  dom.closeJobDetailsModal.addEventListener("click", closeJobDetailsModal);
  dom.editJobDetailsBtn.addEventListener("click", enableJobDetailsEditMode);
  dom.cancelJobDetailsEdit.addEventListener("click", disableJobDetailsEditMode);
  dom.jobDetailsForm.addEventListener("submit", handleJobDetailsSave);
  dom.parseJobBtn.addEventListener("click", handleParseJob);
  dom.jobActions.addEventListener("click", handleParsedActionClick);
  dom.jobsSearchInput.addEventListener("input", renderJobsList);
  dom.jobsStatusFilter.addEventListener("change", renderJobsList);
  dom.jobsList.addEventListener("click", handleJobListClick);
  dom.jobsList.addEventListener("change", handleJobListChange);
  dom.documentsList.addEventListener("click", handleDocumentsClick);
  dom.analyzeResumeBtn.addEventListener("click", handleResumeAnalyze);
  dom.uploadResumeBtn.addEventListener("click", () => dom.resumeUploadInput.click());
  dom.replaceResumeBtn.addEventListener("click", () => dom.resumeUploadInput.click());
  dom.resumeUploadInput.addEventListener("change", handleResumeUpload);
  dom.saveResumeBtn.addEventListener("click", handleResumeSave);
  dom.downloadResumeBtn.addEventListener("click", handleResumeDownload);
  dom.saveKeywordsBtn.addEventListener("click", handleKeywordsSave);
  dom.saveSettingsBtn.addEventListener("click", handleSettingsSave);
  dom.parseEmailBtn.addEventListener("click", handleEmailParse);
  dom.recommendedJobsList.addEventListener("click", handleRecommendedJobClick);
  dom.chatForm.addEventListener("submit", handleChat);
  dom.closeDocumentEditorModal.addEventListener("click", closeActiveDocumentEditor);
  dom.saveDocumentBtn.addEventListener("click", handleDocumentSave);
  dom.downloadDocumentPdfBtn.addEventListener("click", handleDocumentDownload);
  dom.addJobModal.addEventListener("click", event => { if (event.target === dom.addJobModal) dom.addJobModal.classList.add("hidden"); });
  dom.parseJobModal.addEventListener("click", event => { if (event.target === dom.parseJobModal) closeParseModal(); });
  dom.jobDetailsModal.addEventListener("click", event => { if (event.target === dom.jobDetailsModal) closeJobDetailsModal(); });
  dom.documentEditorModal.addEventListener("click", event => { if (event.target === dom.documentEditorModal) closeActiveDocumentEditor(); });
  window.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (!dom.documentEditorModal.classList.contains("hidden")) closeActiveDocumentEditor();
    if (!dom.jobDetailsModal.classList.contains("hidden")) closeJobDetailsModal();
    if (!dom.parseJobModal.classList.contains("hidden")) closeParseModal();
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  attachEvents();
  resetParseState();
  renderChatHistory();
  if (window.lucide) window.lucide.createIcons();
  await checkAuth();
});

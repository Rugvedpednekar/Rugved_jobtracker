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
  currentUser: null,
};

const dom = {
  loginScreen: document.getElementById("login-screen"),
  appShell: document.getElementById("app-shell"),
  sidebar: document.getElementById("sidebar"),
  sidebarBackdrop: document.getElementById("sidebar-backdrop"),
  mobileNavToggle: document.getElementById("mobile-nav-toggle"),
  loginForm: document.getElementById("login-form"),
  loginEmail: document.getElementById("login-email"),
  loginPassword: document.getElementById("login-password"),
  loginError: document.getElementById("login-error"),
  toast: document.getElementById("toast"),
  pageTitle: document.getElementById("page-title"),
  pageEyebrow: document.getElementById("page-eyebrow"),
  pageSubtitle: document.getElementById("page-subtitle"),
  greetingName: document.getElementById("greeting-name"),
  sidebarUserName: document.getElementById("sidebar-user-name"),
  sidebarUserEmail: document.getElementById("sidebar-user-email"),
  sidebarAvatar: document.getElementById("sidebar-avatar"),
  navButtons: document.querySelectorAll(".nav-btn"),
  panels: document.querySelectorAll(".section-panel"),
  logoutBtn: document.getElementById("logout-btn"),
  refreshDashboardBtn: document.getElementById("refresh-dashboard-btn"),
  jobsRefreshBtn: document.getElementById("jobs-refresh-btn"),
  discoverJobsBtn: document.getElementById("discover-jobs-btn"),
  openAddJobBtns: Array.from(document.querySelectorAll("[data-open-add-job], #open-add-job, #open-add-job-jobs")),
  addJobModal: document.getElementById("add-job-modal"),
  addJobForm: document.getElementById("add-job-form"),
  closeAddJobModal: document.getElementById("close-add-job-modal"),
  cancelAddJobModal: document.getElementById("cancel-add-job-modal"),
  openParseJobBtns: Array.from(document.querySelectorAll("[data-open-parse-modal], #open-parse-job, #open-parse-job-jobs")),
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
  jobDetailsTitle: document.getElementById("job-details-title"),
  jobDetailsStatus: document.getElementById("job-details-status"),
  jobDetailsMatch: document.getElementById("job-details-match"),
  jobDetailsGrid: document.getElementById("job-details-grid"),
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
  
  // Chat DOM
  chatFab: document.getElementById("chat-fab"),
  chatWindow: document.getElementById("chat-window"),
  closeChat: document.getElementById("close-chat"),
  chatMessages: document.getElementById("chat-messages"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  
  // Document Editor DOM
  documentEditorModal: document.getElementById("document-editor-modal"),
  closeDocumentEditorModal: document.getElementById("close-document-editor-modal"),
  documentEditorTitle: document.getElementById("document-editor-title"),
  documentEditorSubtitle: document.getElementById("document-editor-subtitle"),
  documentEditorName: document.getElementById("document-editor-name"),
  documentEditorText: document.getElementById("document-editor-text"),
  saveDocumentBtn: document.getElementById("save-document-btn"),
  downloadDocumentPdfBtn: document.getElementById("download-document-pdf-btn"),

  // Edit Job Details DOM
  editJobDetailsBtn: document.getElementById("edit-job-details-btn"),
  jobDetailsViewMode: document.getElementById("job-details-view-mode"),
  jobDetailsEditForm: document.getElementById("job-details-edit-form"),
  cancelEditJobBtn: document.getElementById("cancel-edit-job-btn"),
  jobDetailsCompany: document.getElementById("job-details-company"),
  jobDetailsRole: document.getElementById("job-details-role"),
  jobDetailsStatusSelect: document.getElementById("job-details-status-select"),
  jobDetailsDate: document.getElementById("job-details-date"),
  jobDetailsLocation: document.getElementById("job-details-location"),
  jobDetailsSalary: document.getElementById("job-details-salary"),
  jobDetailsSponsor: document.getElementById("job-details-sponsor"),
  jobDetailsMatchScore: document.getElementById("job-details-match-score"),
  jobDetailsLink: document.getElementById("job-details-link"),
  jobDetailsSummary: document.getElementById("job-details-summary"),
  jobDetailsNotes: document.getElementById("job-details-notes")
};

let lastModalTrigger = null;

function isMobileViewport() {
  return window.matchMedia("(max-width: 1100px)").matches;
}

function setSidebarOpen(isOpen) {
  document.body.classList.toggle("sidebar-open", isOpen);
  if (dom.sidebarBackdrop) dom.sidebarBackdrop.classList.toggle("hidden", !isOpen);
  if (dom.mobileNavToggle) {
    dom.mobileNavToggle.setAttribute("aria-expanded", String(isOpen));
    dom.mobileNavToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
  }
}

function closeSidebar() {
  setSidebarOpen(false);
}

function toggleSidebar() {
  setSidebarOpen(!document.body.classList.contains("sidebar-open"));
}

function showToast(message) {
  if (!dom.toast) return;
  dom.toast.textContent = message;
  dom.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => dom.toast.classList.add("hidden"), 2400);
}

function jobIdEquals(left, right) {
  return String(left ?? "") === String(right ?? "");
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

function emptyState(title, message = "") {
  return `<div class="empty-state"><strong>${title}</strong>${message ? `<p>${message}</p>` : ""}</div>`;
}

function initialsForName(name = "") {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase() || "")
    .join("") || "JT";
}

function setCurrentUser(user = null) {
  state.currentUser = user;
  const fullName = safeText(user?.full_name?.trim(), "Your workspace");
  const email = safeText(user?.email?.trim(), "Signed in");
  const greeting = user?.full_name?.trim() || user?.email?.split("@")[0] || "there";
  if (dom.sidebarUserName) dom.sidebarUserName.textContent = fullName;
  if (dom.sidebarUserEmail) dom.sidebarUserEmail.textContent = email;
  if (dom.greetingName) dom.greetingName.textContent = greeting;
  if (dom.sidebarAvatar) dom.sidebarAvatar.textContent = initialsForName(user?.full_name || user?.email || "JT");
}

function showLogin() {
  closeSidebar();
  setCurrentUser(null);
  if(dom.loginScreen) dom.loginScreen.classList.remove("hidden");
  if(dom.appShell) dom.appShell.classList.add("hidden");
}

function showApp() {
  if(dom.loginScreen) dom.loginScreen.classList.add("hidden");
  if(dom.appShell) dom.appShell.classList.remove("hidden");
  closeSidebar();
}

function openDocumentEditorModal() {
  if (!dom.documentEditorModal) return;
  dom.documentEditorModal.classList.remove("hidden");
  dom.documentEditorModal.setAttribute("aria-hidden", "false");
}

function closeDocumentEditorModal() {
  if (!dom.documentEditorModal) return;
  dom.documentEditorModal.classList.add("hidden");
  dom.documentEditorModal.setAttribute("aria-hidden", "true");
}

function setSection(sectionId) {
  dom.panels.forEach(panel => panel.classList.toggle("hidden", panel.id !== sectionId));
  dom.navButtons.forEach(button => button.classList.toggle("active", button.dataset.section === sectionId));
  const active = Array.from(dom.navButtons).find(button => button.dataset.section === sectionId);
  if (dom.pageTitle) dom.pageTitle.textContent = active ? active.textContent.trim() : "Tracker";
  if (dom.pageEyebrow) dom.pageEyebrow.textContent = sectionId === "tracker" ? "Overview" : "Workspace";
  if (dom.pageSubtitle) {
    const greeting = state.currentUser?.full_name?.trim() || state.currentUser?.email?.split("@")[0] || "there";
    dom.pageSubtitle.textContent = `Welcome back, ${greeting}. ${sectionId === "tracker" ? "Your dashboard is loaded from live account data." : "Everything shown here comes from your private account data."}`;
  }
  if (isMobileViewport()) closeSidebar();
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

// PDF Export Function
async function downloadPdf(title, content_text, file_name) {
  const response = await fetch(`${API_BASE}/api/documents/export-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, content_text, file_name })
  });
  
  if (!response.ok) throw new Error("Failed to generate PDF");
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = file_name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

function normalizeKeywordLines(text) {
  return text.split(/\n|,/).map(item => item.trim()).filter(Boolean);
}

function renderChips(items = []) {
  if (!items.length) return `<span class="muted">No items yet.</span>`;
  return items.map(item => `<span class="chip">${item}</span>`).join("");
}

function renderParsedProfile(profile = {}) {
  if (!dom.parsedProfileOutput) return;
  dom.parsedProfileOutput.textContent = JSON.stringify(profile, null, 2);
}

function setResumeMeta(profile = {}) {
  if (dom.resumeMeta) {
    const resumeDocument = state.currentResumeDocument;
    dom.resumeMeta.textContent = resumeDocument
      ? `${safeText(resumeDocument.name, "Resume")} • Updated ${formatDateTimeValue(resumeDocument.updated_at, "recently")}`
      : "No saved resume document yet.";
  }
  if (dom.resumeUploadStatus) {
    dom.resumeUploadStatus.textContent = profile.resume_text
      ? "Resume content loaded."
      : "Upload a resume or paste your latest resume text.";
  }
}

function openDocumentEditor(document, subtitle = "") {
  if (!document || !dom.documentEditorModal || !dom.documentEditorName || !dom.documentEditorText) return;
  state.activeDocument = document;
  if (dom.documentEditorTitle) dom.documentEditorTitle.textContent = safeText(document.name, "Document");
  if (dom.documentEditorSubtitle) dom.documentEditorSubtitle.textContent = subtitle || safeText(document.doc_type, "Saved document");
  dom.documentEditorName.value = document.name || "";
  dom.documentEditorText.value = document.content_text || "";
  openDocumentEditorModal();
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
  if (!element) return;
  element.innerHTML = items.length
    ? items.map(renderTrackerCard).join("")
    : emptyState(`No ${label.toLowerCase()} jobs yet`, "This column will populate when a real job reaches this stage.");
}

function renderDashboard() {
  if (!dom.totalCount) return;
  const data = state.dashboard || { stats: {}, columns: {}, daily_briefing: {} };
  const stats = data.stats || {};
  if (dom.totalCount) dom.totalCount.textContent = stats.total_jobs || 0;
  if (dom.wishlistCount) dom.wishlistCount.textContent = stats.wishlist_count || 0;
  if (dom.appliedCount) dom.appliedCount.textContent = stats.applied_count || 0;
  if (dom.interviewCount) dom.interviewCount.textContent = stats.interview_count || 0;
  if (dom.offeredCount) dom.offeredCount.textContent = stats.offered_count || 0;
  if (dom.acceptedCount) dom.acceptedCount.textContent = stats.accepted_count || 0;
  
  // Safe checks for badges
  if (dom.wishlistBadge) dom.wishlistBadge.textContent = stats.wishlist_count || 0;
  if (dom.appliedBadge) dom.appliedBadge.textContent = stats.applied_count || 0;
  if (dom.interviewBadge) dom.interviewBadge.textContent = stats.interview_count || 0;
  if (dom.offeredBadge) dom.offeredBadge.textContent = stats.offered_count || 0;
  if (dom.acceptedBadge) dom.acceptedBadge.textContent = stats.accepted_count || 0;
  if (dom.laterBadge) dom.laterBadge.textContent = stats.later_count || 0;
  
  renderBoardColumn(dom.wishlistColumn, data.columns?.Wishlist || [], "Wishlist");
  renderBoardColumn(dom.appliedColumn, data.columns?.Applied || [], "Applied");
  renderBoardColumn(dom.interviewColumn, data.columns?.Interview || [], "Interview");
  renderBoardColumn(dom.offeredColumn, data.columns?.Offered || [], "Offered");
  renderBoardColumn(dom.acceptedColumn, data.columns?.Accepted || [], "Accepted");
  renderBoardColumn(dom.laterColumn, data.columns?.Later || [], "Later");

  const briefing = data.daily_briefing || {};
  if (dom.briefingSummary) dom.briefingSummary.textContent = briefing.summary || "No briefing available yet.";
  if (dom.dailyBriefingText) dom.dailyBriefingText.textContent = briefing.summary || "No briefing available yet.";
  
  if (dom.followupList) {
      dom.followupList.innerHTML = (briefing.follow_up_suggestions || []).length
        ? briefing.follow_up_suggestions.map(item => `<div class="list-item">${item}</div>`).join("")
        : emptyState("No follow-ups yet", "Your actual reminders will appear here after activity is recorded.");
  }
  
  if (dom.focusList) {
      dom.focusList.innerHTML = (briefing.focus_today || []).length
        ? briefing.focus_today.map(item => `<div class="list-item">${item}</div>`).join("")
        : emptyState("No focus items yet", "Once applications move or become stale, the highest-priority next steps will appear here.");
  }
  
  if (dom.recentIntakes) {
      dom.recentIntakes.innerHTML = (data.recent_intakes || []).length
        ? data.recent_intakes.map(item => `<div class="list-item"><strong>${safeText(item.company)}</strong><p class="muted">${safeText(item.role)} • ${safeText(item.location, "Location pending")}</p></div>`).join("")
        : emptyState("No parsed jobs yet", "Parsed job links will appear here after successful intake.");
  }
  
  if (data.recommended_today) {
    state.recommendedJobs = data.recommended_today;
  }
  renderRecommendedJobs();
}

function renderRecommendedJobs() {
  if (!dom.recommendedMeta || !dom.recommendedJobsList) return;
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
  const query = dom.jobsSearchInput?.value?.trim().toLowerCase() || "";
  const statusFilter = dom.jobsStatusFilter?.value || "";
  return state.jobs.filter(job => {
    const haystack = [job.company, job.role, job.notes, job.field, job.location, job.job_summary].join(" ").toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    const matchesStatus = !statusFilter || job.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
}

function renderJobsList() {
  if (!dom.jobsList) return;
  const jobs = filteredJobs();
  if (!jobs.length) {
    const hasJobs = state.jobs.length > 0;
    dom.jobsList.innerHTML = hasJobs
      ? emptyState("No jobs match the current filters", "Try clearing the search or status filter.")
      : emptyState("No jobs saved yet", "Add a job manually or parse a live job link to start tracking.");
    return;
  }
  dom.jobsList.innerHTML = `
    <div class="table-head table-row header">
      <span>Company / Role</span>
      <span>Status</span>
      <span>Location</span>
      <span>Match</span>
      <span>Actions</span>
    </div>
    ${jobs.map(job => `
      <div class="table-row" data-job-id="${job.id}">
        <div>
          <button class="btn btn-ghost" style="padding:0; text-align:left; display:block;" data-action="open-details" type="button" aria-label="Open details for ${escapeHtml(safeText(job.company, "job"))}">
            <strong style="color:var(--color-text-main); font-size:1rem;">${safeText(job.company)}</strong>
            <p class="muted">${safeText(job.role)}</p>
          </button>
        </div>
        <div>
          <select class="field" data-action="status">
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

function toggleJobDetailsEditMode(editMode) {
  state.jobDetailsEditMode = editMode;
  if(dom.jobDetailsViewMode && dom.jobDetailsEditForm) {
      if (editMode) {
        dom.jobDetailsViewMode.classList.add("hidden");
        dom.jobDetailsEditForm.classList.remove("hidden");
      } else {
        dom.jobDetailsViewMode.classList.remove("hidden");
        dom.jobDetailsEditForm.classList.add("hidden");
      }
  }
}

function openJobDetailsModal(job, trigger = null) {
  if (!job || !dom.jobDetailsModal) return;
  state.activeJobDetails = job;
  lastModalTrigger = trigger || document.activeElement;
  
  if (dom.jobDetailsTitle) dom.jobDetailsTitle.textContent = [job.company, job.role].filter(Boolean).join(" — ") || "Job details";
  if (dom.jobDetailsStatus) dom.jobDetailsStatus.textContent = safeText(job.status, "Not specified");
  if (dom.jobDetailsMatch) dom.jobDetailsMatch.textContent = job.ai_match_score ? `Match ${job.ai_match_score}%` : "Match not available";
  
  if (dom.jobDetailsGrid) {
      const cards = [
        ["Company name", renderDetailValue(job.company, "Not specified")],
        ["Role title", renderDetailValue(job.role, "Not specified")],
        ["Location", renderDetailValue(job.location, "Not specified")],
        ["Salary", renderDetailValue(job.salary, "Not specified")],
        ["Sponsorship info", renderDetailValue(job.sponsor || job.sponsorship, "Not specified")],
        ["Job link", renderDetailLink(job.link, "Not specified")],
        ["Skills", renderDetailList(job.skills, "No skills parsed"), "full-span"],
        ["Notes", renderDetailValue(job.notes, "No notes added"), "full-span"],
        ["Summary / parsed description", renderDetailValue(job.job_summary, "Not specified"), "full-span"]
      ];
      dom.jobDetailsGrid.innerHTML = cards.map(([label, valueHtml, span]) => `
        <div class="panel stack-md${span ? ` ${span}` : ""}">
          <div class="label">${label}</div>
          ${valueHtml}
        </div>
      `).join("");
  }
  
  if(dom.jobDetailsCompany) {
    dom.jobDetailsCompany.value = job.company || "";
    dom.jobDetailsRole.value = job.role || "";
    if(dom.jobDetailsStatusSelect) dom.jobDetailsStatusSelect.value = job.status || "Applied";
    if(dom.jobDetailsDate) dom.jobDetailsDate.value = job.date || "";
    if(dom.jobDetailsLocation) dom.jobDetailsLocation.value = job.location || "";
    if(dom.jobDetailsSalary) dom.jobDetailsSalary.value = job.salary || "";
    if(dom.jobDetailsSponsor) dom.jobDetailsSponsor.value = job.sponsor || job.sponsorship || "";
    if(dom.jobDetailsMatchScore) dom.jobDetailsMatchScore.value = job.ai_match_score || "";
    if(dom.jobDetailsLink) dom.jobDetailsLink.value = job.link || "";
    if(dom.jobDetailsSummary) dom.jobDetailsSummary.value = job.job_summary || "";
    if(dom.jobDetailsNotes) dom.jobDetailsNotes.value = job.notes || "";
  }

  toggleJobDetailsEditMode(false);
  dom.jobDetailsModal.classList.remove("hidden");
  dom.jobDetailsModal.setAttribute("aria-hidden", "false");
}

function closeJobDetailsModal() {
  if (!dom.jobDetailsModal) return;
  dom.jobDetailsModal.classList.add("hidden");
  dom.jobDetailsModal.setAttribute("aria-hidden", "true");
  if (lastModalTrigger && typeof lastModalTrigger.focus === "function") {
    lastModalTrigger.focus();
  }
}

function renderProfile() {
  if (!dom.resumeBox && !dom.parsedProfileOutput) return;
  renderParsedProfile(state.parsedProfile || {});
  setResumeMeta({});
}

function renderSettings() {
  if (!dom.syncWindow) return;
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
  if (!dom.documentsList) return;
  dom.documentsList.innerHTML = state.documents.length
    ? state.documents.map(doc => `
      <div class="panel stack-md">
        <div class="section-head compact">
          <div>
            <strong>${safeText(doc.name)}</strong>
            <p class="muted">${safeText(doc.doc_type)} • Updated ${formatDateTimeValue(doc.updated_at, "recently")}</p>
          </div>
          <button class="btn btn-secondary btn-icon-only" type="button" data-action="open-document" data-document-id="${doc.id}"><i data-lucide="arrow-right"></i></button>
        </div>
      </div>
    `).join("")
    : emptyState("No saved documents yet", "Generated resumes and cover letters will appear here.");
  if (window.lucide) window.lucide.createIcons();
}

function renderChatHistory() {
  if (!dom.chatMessages) return;
  if (!state.chatAvailable) {
    dom.chatMessages.innerHTML = emptyState("Assistant unavailable", "The chat backend is not connected.");
    return;
  }
  dom.chatMessages.innerHTML = state.chatHistory.length
    ? state.chatHistory.map(item => `
      <div class="chat-msg ${item.role === "assistant" ? "ai" : "user"}">
        ${item.message}
      </div>
    `).join("")
    : `<div class="chat-msg ai">Hi Rugved! How can I help with your job hunt today?</div>`;
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

function populateEmailJobDropdown() {
  if (!dom.emailJobLink) return;
  dom.emailJobLink.innerHTML = `<option value="">Optionally link to a job</option>${state.jobs.map(job => `<option value="${job.id}">${job.company} — ${job.role}</option>`).join("")}`;
}

// -------------------------------------------------------------
// THIS IS THE CRITICAL FIX: SAFE DOM CHECKS
// -------------------------------------------------------------
function renderParseResults() {
  if (!dom.parseLoading || !dom.parseError || !dom.parseEmpty || !dom.parseJobResults || !dom.generatedOutput) return;
  const intake = state.currentIntake;
  
  dom.parseLoading.classList.toggle("hidden", !state.parsing);
  dom.parseError.classList.toggle("hidden", !state.parseError);
  dom.parseError.textContent = state.parseError || "";
  
  const showEmpty = !state.parsing && !state.parseError && !intake;
  dom.parseEmpty.classList.toggle("hidden", !showEmpty);
  
  if (!intake) {
    dom.parseJobResults.classList.add("hidden");
    return;
  }
  
  const parsed = intake.parsed_job || {};
  const match = intake.match_analysis || {};
  dom.parseJobResults.classList.remove("hidden");
  
  // Safe updates to text fields
  if (dom.parsedCompany) dom.parsedCompany.textContent = safeText(parsed.company);
  if (dom.parsedRole) dom.parsedRole.textContent = safeText(parsed.role);
  if (dom.parsedLocation) dom.parsedLocation.textContent = safeText(parsed.location);
  if (dom.parsedMatchScore) dom.parsedMatchScore.textContent = match.score ? `${match.score}%` : "—";
  
  if (dom.parsedSkills) dom.parsedSkills.innerHTML = renderChips(parsed.skills || []);
  if (dom.parsedMatchSummary) dom.parsedMatchSummary.textContent = safeText(match.summary, "No match summary yet.");
  
  // Notice we safely skip parsedSummary because it was removed from index.html
  if (dom.parsedSummary) dom.parsedSummary.textContent = safeText(parsed.summary);
  
  const tailoringNotes = match.tailoring_notes || [];
  if (dom.parsedTailoringNotes) {
    dom.parsedTailoringNotes.classList.toggle("hidden", !tailoringNotes.length);
    dom.parsedTailoringNotes.innerHTML = tailoringNotes.length
      ? `<p class="label">Tailoring guidance</p><div class="chip-row">${tailoringNotes.map(note => `<span class="chip">${escapeHtml(note)}</span>`).join("")}</div>`
      : "";
  }

  if (dom.jobActions) {
      dom.jobActions.innerHTML = (intake.suggested_actions || []).length ? (intake.suggested_actions || []).map(action => `
        <button class="btn btn-secondary" type="button" data-action-id="${action.id}">
          ${action.label}
        </button>
      `).join("") : emptyState("No actions available", "No follow-up actions returned by backend.");
  }
}

async function loadDashboard() {
  state.dashboard = await api("/api/dashboard/simple");
  if (dom.gmailSyncStatus) dom.gmailSyncStatus.textContent = state.dashboard.gmail_sync?.message || "Not configured";
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
  if (dom.resumeBox) dom.resumeBox.value = profile.resume_text || "";
  state.parsedProfile = profile.parsed_profile || {};
  state.chatHistory = profile.chat_history || [];
  state.chatAvailable = true;
  state.documents = profile.documents || [];
  state.currentResumeDocument = profile.current_resume_document || null;
  renderProfile();
  setResumeMeta(profile);
  renderChatHistory();
  renderDocuments();
  if (dom.keywordBox) {
    const keywords = await api("/api/keywords");
    dom.keywordBox.value = (keywords.keywords || []).join("\n");
  }
}

async function loadSettings() {
  const data = await api("/api/settings");
  state.settings = data.settings || {};
  if (dom.gmailSyncStatus) dom.gmailSyncStatus.textContent = data.gmail_sync?.message || "Not configured";
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
    const me = await api("/api/auth/me");
    setCurrentUser(me);
    showApp();
    await loadAllData();
  } catch {
    showLogin();
  }
}

async function handleLogin(event) {
  event.preventDefault();
  dom.loginError?.classList.add("hidden");
  try {
    const auth = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: dom.loginEmail.value.trim(), password: dom.loginPassword.value })
    });
    setCurrentUser(auth);
    showApp();
    await loadAllData();
    setSection("tracker");
    showToast("Logged in successfully");
  } catch (error) {
    if (dom.loginError) {
      dom.loginError.textContent = error.message;
      dom.loginError.classList.remove("hidden");
    }
  }
}

async function handleLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch {
    // ignore
  }
  
  state.jobs = [];
  state.recommendedJobs = [];
  state.documents = [];
  state.parsedProfile = {};
  state.dashboard = null;
  state.chatHistory = [];
  state.currentIntake = null;
  state.activeJobDetails = null;
  state.activeDocument = null;
  state.currentUser = null;

  if (dom.loginForm) dom.loginForm.reset();
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
    const job = state.jobs.find(item => jobIdEquals(item.id, row.dataset.jobId));
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

// Handlers for the Edit Mode
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
    await Promise.all([loadJobs(), loadDashboard()]);
    openJobDetailsModal(updatedJob, lastModalTrigger); // Reloads view with new data
    showToast("Job details updated");
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
    if(dom.resumeUploadStatus) {
        dom.resumeUploadStatus.textContent = `Loaded ${data.filename} using ${data.parser.toUpperCase()} extraction. Review and save when ready.`;
    }
    showToast("Resume uploaded");
  } catch (error) {
    if(dom.resumeUploadStatus) dom.resumeUploadStatus.textContent = error.message;
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
    if(dom.resumeUploadStatus) dom.resumeUploadStatus.textContent = "Resume saved to your profile workspace.";
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
    if(dom.gmailSyncStatus) dom.gmailSyncStatus.textContent = data.gmail_sync?.message || "Not configured";
    showToast("Settings saved");
  } catch (error) {
    showToast(error.message);
  }
}

async function handleDiscoverJobs() {
  const button = dom.discoverJobsBtn;
  button.disabled = true;
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
      if (dom.parseJobModal) dom.parseJobModal.classList.remove("hidden");
      if (dom.generatedOutput) {
        dom.generatedOutput.classList.remove("hidden");
        dom.generatedOutput.innerHTML = `Generated <strong>${escapeHtml(data.document.name)}</strong>. Review and edit it before exporting.`;
      }
      openDocumentEditor(data.document, `Tailored for ${card.querySelector("h3")?.textContent || "this role"}.`);
    } else if (data.match_analysis) {
      if (dom.generatedOutput) {
        dom.generatedOutput.classList.remove("hidden");
        dom.generatedOutput.innerHTML = `<strong>Match summary</strong><p class="muted">${escapeHtml(data.match_analysis.summary || "Resume comparison ready.")}</p>`;
      }
      if (dom.parseJobModal) dom.parseJobModal.classList.remove("hidden");
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
    if (dom.parsedEmailStatus) dom.parsedEmailStatus.textContent = data.parsed?.status || "-";
    if (dom.parsedEmailReason) dom.parsedEmailReason.textContent = data.parsed?.reason || "-";
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
  
  // Optimistic UI update
  dom.chatMessages.innerHTML += `<div class="chat-msg user">${escapeHtml(message)}</div>`;
  dom.chatInput.value = "";
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;

  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
    state.chatAvailable = true;
    state.chatHistory = data.history || [];
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
  if(dom.parseJobModal) dom.parseJobModal.classList.remove("hidden");
  if(dom.jobUrlInput) dom.jobUrlInput.focus();
}

function closeParseModal() {
  if(dom.parseJobModal) dom.parseJobModal.classList.add("hidden");
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
  
  if (dom.generatedOutput) {
    dom.generatedOutput.classList.remove("hidden");
    dom.generatedOutput.innerHTML = "Working on your request...";
  }
  
  try {
    const data = await api("/api/jobs/action", {
      method: "POST",
      body: JSON.stringify({ intake_id: state.currentIntake.intake_id, action })
    });
    if (data.document?.content_text) {
      const parsedJob = state.currentIntake?.parsed_job || {};
      if(dom.generatedOutput) {
        dom.generatedOutput.innerHTML = `Generated <strong>${escapeHtml(data.document.name)}</strong>. Opened editable preview for ${escapeHtml(parsedJob.company || "this job")}.`;
      }
      openDocumentEditor(data.document, `Tailored for ${parsedJob.role || "the parsed role"} at ${parsedJob.company || "the target company"}.`);
    } else if (data.match_analysis) {
      if(dom.generatedOutput) {
        dom.generatedOutput.innerHTML = `
          <strong>Resume match updated</strong>
          <p class="muted">${escapeHtml(data.match_analysis.summary || "Resume comparison generated.")}</p>
          <div class="chip-row">${(data.match_analysis.matched_skills || []).map(skill => `<span class="chip">${escapeHtml(skill)}</span>`).join("")}</div>
        `;
      }
    } else if (data.job) {
      if(dom.generatedOutput) {
        dom.generatedOutput.innerHTML = `Saved <strong>${escapeHtml(data.job.company)}</strong> — ${escapeHtml(data.job.role)} as ${escapeHtml(data.job.status)}.`;
      }
    } else {
      if(dom.generatedOutput) {
        dom.generatedOutput.innerHTML = "Action saved.";
      }
    }
    await Promise.all([loadDashboard(), loadJobs(), loadDocuments()]);
    showToast("Action completed");
  } catch (error) {
    if(dom.generatedOutput) dom.generatedOutput.textContent = error.message;
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
  dom.loginForm?.addEventListener("submit", handleLogin);
  dom.logoutBtn?.addEventListener("click", handleLogout);
  dom.navButtons.forEach(button => button.addEventListener("click", () => setSection(button.dataset.section)));
  dom.mobileNavToggle?.addEventListener("click", toggleSidebar);
  dom.sidebarBackdrop?.addEventListener("click", closeSidebar);
  
  dom.refreshDashboardBtn?.addEventListener("click", () => Promise.all([loadDashboard()]));
  dom.jobsRefreshBtn?.addEventListener("click", () => Promise.all([loadJobs(), loadDashboard()]));
  dom.discoverJobsBtn?.addEventListener("click", handleDiscoverJobs);
  
  const openAddJobModal = () => { if(dom.addJobModal) dom.addJobModal.classList.remove("hidden"); };
  dom.openAddJobBtns.forEach(button => button?.addEventListener("click", openAddJobModal));
  
  const closeAllModals = () => {
      if(dom.addJobModal) dom.addJobModal.classList.add("hidden");
      if(dom.parseJobModal) dom.parseJobModal.classList.add("hidden");
      if(dom.jobDetailsModal) dom.jobDetailsModal.classList.add("hidden");
      if(dom.documentEditorModal) dom.documentEditorModal.classList.add("hidden");
  };
  
  document.querySelectorAll(".close-modal-btn").forEach(btn => btn.addEventListener("click", closeAllModals));
  
  dom.addJobForm?.addEventListener("submit", handleAddJob);
  
  dom.openParseJobBtns.forEach(button => button && button.addEventListener("click", openParseModal));
  dom.parseJobBtn?.addEventListener("click", handleParseJob);
  dom.jobActions?.addEventListener("click", handleParsedActionClick);
  
  dom.editJobDetailsBtn?.addEventListener("click", () => toggleJobDetailsEditMode(true));
  dom.cancelEditJobBtn?.addEventListener("click", () => toggleJobDetailsEditMode(false));
  dom.jobDetailsEditForm?.addEventListener("submit", handleJobDetailsSave);
  
  dom.jobsSearchInput?.addEventListener("input", renderJobsList);
  dom.jobsStatusFilter?.addEventListener("change", renderJobsList);
  dom.jobsList?.addEventListener("click", handleJobListClick);
  dom.jobsList?.addEventListener("change", handleJobListChange);
  
  dom.documentsList?.addEventListener("click", handleDocumentsClick);
  dom.saveDocumentBtn?.addEventListener("click", handleDocumentSave);
  dom.downloadDocumentPdfBtn?.addEventListener("click", handleDocumentDownload);
  
  dom.analyzeResumeBtn?.addEventListener("click", handleResumeAnalyze);
  dom.uploadResumeBtn?.addEventListener("click", () => dom.resumeUploadInput?.click());
  dom.replaceResumeBtn?.addEventListener("click", () => dom.resumeUploadInput?.click());
  dom.resumeUploadInput?.addEventListener("change", handleResumeUpload);
  dom.saveResumeBtn?.addEventListener("click", handleResumeSave);
  dom.downloadResumeBtn?.addEventListener("click", handleResumeDownload);
  dom.saveKeywordsBtn?.addEventListener("click", handleKeywordsSave);
  dom.saveSettingsBtn?.addEventListener("click", handleSettingsSave);
  dom.parseEmailBtn?.addEventListener("click", handleEmailParse);
  dom.recommendedJobsList?.addEventListener("click", handleRecommendedJobClick);
  
  dom.chatFab?.addEventListener("click", () => {
    if(!dom.chatWindow) return;
    dom.chatWindow.classList.toggle("hidden");
    if (!dom.chatWindow.classList.contains("hidden")) dom.chatInput?.focus();
  });
  dom.closeChat?.addEventListener("click", () => dom.chatWindow?.classList.add("hidden"));
  dom.chatForm?.addEventListener("submit", handleChat);
  
  window.addEventListener("keydown", event => {
    if (event.key !== "Escape") return;
    if (document.body.classList.contains("sidebar-open")) closeSidebar();
    closeAllModals();
  });
  window.addEventListener("resize", () => {
    if (!isMobileViewport()) closeSidebar();
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  attachEvents();
  resetParseState();
  renderChatHistory();
  if (window.lucide) window.lucide.createIcons();
  await checkAuth();
});

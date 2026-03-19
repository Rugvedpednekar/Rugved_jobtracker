const API_BASE = "";
const STATUS_ORDER = ["Wishlist", "Applied", "Interview", "Offered", "Accepted", "Rejected", "Archived"];

const state = {
  jobs: [],
  parsedProfile: {},
  settings: {},
  dashboard: null,
  chatHistory: []
};

const dom = {
  loginScreen: document.getElementById("login-screen"),
  appShell: document.getElementById("app-shell"),
  loginForm: document.getElementById("login-form"),
  loginEmail: document.getElementById("login-email"),
  loginPassword: document.getElementById("login-password"),
  loginError: document.getElementById("login-error"),
  toast: document.getElementById("toast"),
  navButtons: document.querySelectorAll(".nav-btn"),
  panels: document.querySelectorAll(".section-panel"),
  logoutBtn: document.getElementById("logout-btn"),
  refreshDashboardBtn: document.getElementById("refresh-dashboard-btn"),
  jobsRefreshBtn: document.getElementById("jobs-refresh-btn"),
  openAddJobBtn: document.getElementById("open-add-job"),
  addJobModal: document.getElementById("add-job-modal"),
  addJobForm: document.getElementById("add-job-form"),
  closeAddJobModal: document.getElementById("close-add-job-modal"),
  cancelAddJobModal: document.getElementById("cancel-add-job-modal"),
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
  wishlistColumn: document.getElementById("wishlist-column"),
  appliedColumn: document.getElementById("applied-column"),
  interviewColumn: document.getElementById("interview-column"),
  offeredColumn: document.getElementById("offered-column"),
  acceptedColumn: document.getElementById("accepted-column"),
  resumeBox: document.getElementById("resume-box"),
  parsedProfileOutput: document.getElementById("parsed-profile-output"),
  analyzeResumeBtn: document.getElementById("analyze-resume-btn"),
  saveResumeBtn: document.getElementById("save-resume-btn"),
  keywordBox: document.getElementById("keyword-box"),
  saveKeywordsBtn: document.getElementById("save-keywords-btn"),
  syncWindow: document.getElementById("sync-window"),
  preferredLocation: document.getElementById("preferred-location"),
  userNotes: document.getElementById("user-notes"),
  saveSettingsBtn: document.getElementById("save-settings-btn"),
  gmailSyncStatus: document.getElementById("gmail-sync-status"),
  resumeUpload: document.getElementById("resume-upload"),
  resumeUploadBtn: document.getElementById("resume-upload-btn"),
  resumeUploadStatus: document.getElementById("resume-upload-status"),
  coverLetterUpload: document.getElementById("cover-letter-upload"),
  coverLetterUploadBtn: document.getElementById("cover-letter-upload-btn"),
  coverLetterUploadStatus: document.getElementById("cover-letter-upload-status"),
  emailParserInput: document.getElementById("email-parser-input"),
  emailJobLink: document.getElementById("email-job-link"),
  parsedEmailStatus: document.getElementById("parsed-email-status"),
  parsedEmailReason: document.getElementById("parsed-email-reason"),
  parseEmailBtn: document.getElementById("parse-email-btn"),
  chatMessages: document.getElementById("chat-messages"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input")
};

function showToast(message) {
  if (!dom.toast) return;
  dom.toast.textContent = message;
  dom.toast.classList.remove("hidden");
  setTimeout(() => dom.toast.classList.add("hidden"), 2400);
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
  dom.panels.forEach(panel => panel.classList.toggle("active", panel.id === sectionId));
  dom.navButtons.forEach(button => button.classList.toggle("active", button.dataset.section === sectionId));
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

function formatDate(dateText) {
  if (!dateText) return "—";
  return dateText;
}

function emptyState(message) {
  return `<div class="panel empty-state">${message}</div>`;
}

function normalizeKeywordLines(text) {
  return text
    .split(/\n|,/)
    .map(item => item.trim())
    .filter(Boolean);
}

function renderTrackerCard(job) {
  return `
    <article class="job-card-mini">
      <div>
        <h4>${job.company || "Unknown company"}</h4>
        <p>${job.role || "Unknown role"}</p>
      </div>
      <span class="status-pill">${job.status || "Applied"}</span>
      <small>${formatDate(job.date)}</small>
    </article>
  `;
}

function renderDashboard() {
  const data = state.dashboard || { stats: {}, columns: {} };
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

  const columns = {
    Wishlist: dom.wishlistColumn,
    Applied: dom.appliedColumn,
    Interview: dom.interviewColumn,
    Offered: dom.offeredColumn,
    Accepted: dom.acceptedColumn
  };

  Object.entries(columns).forEach(([status, element]) => {
    const items = data.columns?.[status] || [];
    element.innerHTML = items.length ? items.map(renderTrackerCard).join("") : emptyState(`No ${status.toLowerCase()} jobs yet.`);
  });
}

function filteredJobs() {
  const query = dom.jobsSearchInput.value.trim().toLowerCase();
  const statusFilter = dom.jobsStatusFilter.value;
  return state.jobs.filter(job => {
    const matchesQuery = !query || [job.company, job.role, job.notes, job.field, job.sponsor].some(value => (value || "").toLowerCase().includes(query));
    const matchesStatus = !statusFilter || job.status === statusFilter;
    return matchesQuery && matchesStatus;
  });
}

function renderJobsList() {
  const jobs = filteredJobs();
  if (!jobs.length) {
    dom.jobsList.innerHTML = emptyState("No jobs match the current filters.");
    return;
  }

  dom.jobsList.innerHTML = `
    <div class="table-head table-row">
      <span>Company / Role</span>
      <span>Status</span>
      <span>Date</span>
      <span>Details</span>
      <span>Actions</span>
    </div>
    ${jobs.map(job => `
      <div class="table-row" data-job-id="${job.id}">
        <div>
          <strong>${job.company}</strong>
          <p>${job.role}</p>
        </div>
        <div>
          <select class="field job-status-select" data-action="status">
            ${STATUS_ORDER.map(status => `<option value="${status}" ${job.status === status ? "selected" : ""}>${status}</option>`).join("")}
          </select>
        </div>
        <div>${formatDate(job.date)}</div>
        <div class="table-details">
          <p>${job.field || "—"}</p>
          <p>${job.salary || "—"}</p>
        </div>
        <div class="inline-actions">
          <button class="btn btn-ghost" data-action="delete" type="button">Delete</button>
        </div>
      </div>
    `).join("")}
  `;
}

function renderProfile() {
  dom.parsedProfileOutput.textContent = JSON.stringify(state.parsedProfile || {}, null, 2);
}

function renderSettings() {
  dom.syncWindow.value = String(state.settings.sync_window_hours || 24);
  dom.preferredLocation.value = state.settings.preferred_location || "";
  dom.userNotes.value = state.settings.user_notes || "";
}

function renderChatHistory() {
  dom.chatMessages.innerHTML = state.chatHistory.length
    ? state.chatHistory.map(item => `
        <div class="chat-bubble ${item.role === "assistant" ? "assistant" : "user"}">
          <span>${item.role}</span>
          <p>${item.message}</p>
        </div>
      `).join("")
    : `<div class="panel empty-state">Ask the assistant about jobs, resume data, keywords, or settings.</div>`;
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

function populateEmailJobDropdown() {
  dom.emailJobLink.innerHTML = `<option value="">Optionally link to a job</option>${state.jobs.map(job => `<option value="${job.id}">${job.company} — ${job.role}</option>`).join("")}`;
}

function setUploadStatus(input, target) {
  const file = input.files?.[0];
  target.textContent = file ? `Selected: ${file.name}` : "No file selected.";
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

async function loadProfile() {
  const profile = await api("/api/profile");
  dom.resumeBox.value = profile.resume_text || "";
  state.parsedProfile = profile.parsed_profile || {};
  state.chatHistory = profile.chat_history || [];
  renderProfile();
  renderChatHistory();

  const keywords = await api("/api/keywords");
  dom.keywordBox.value = (keywords.keywords || []).join("\n");
}

async function loadSettings() {
  const data = await api("/api/settings");
  state.settings = data.settings || {};
  dom.gmailSyncStatus.textContent = data.gmail_sync?.message || "Not configured";
  renderSettings();
}

async function loadAllData() {
  await Promise.all([loadDashboard(), loadJobs(), loadProfile(), loadSettings()]);
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
    // ignore logout failure
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
  const jobId = row.dataset.jobId;

  if (event.target.dataset.action === "delete") {
    try {
      await api(`/api/jobs/${jobId}`, { method: "DELETE" });
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

async function handleResumeSave() {
  try {
    await api("/api/resume/save", {
      method: "POST",
      body: JSON.stringify({ resume_text: dom.resumeBox.value, parsed_profile: state.parsedProfile })
    });
    showToast("Profile saved");
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
        user_notes: dom.userNotes.value
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
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message: dom.chatInput.value })
    });
    state.chatHistory = data.history || [];
    dom.chatInput.value = "";
    renderChatHistory();
  } catch (error) {
    showToast(error.message);
  }
}

function attachEvents() {
  dom.loginForm.addEventListener("submit", handleLogin);
  dom.logoutBtn.addEventListener("click", handleLogout);
  dom.navButtons.forEach(button => button.addEventListener("click", () => setSection(button.dataset.section)));
  dom.refreshDashboardBtn.addEventListener("click", loadDashboard);
  dom.jobsRefreshBtn.addEventListener("click", loadJobs);
  dom.openAddJobBtn.addEventListener("click", () => dom.addJobModal.classList.remove("hidden"));
  dom.closeAddJobModal.addEventListener("click", () => dom.addJobModal.classList.add("hidden"));
  dom.cancelAddJobModal.addEventListener("click", () => dom.addJobModal.classList.add("hidden"));
  dom.addJobForm.addEventListener("submit", handleAddJob);
  dom.jobsSearchInput.addEventListener("input", renderJobsList);
  dom.jobsStatusFilter.addEventListener("change", renderJobsList);
  dom.jobsList.addEventListener("click", handleJobListClick);
  dom.jobsList.addEventListener("change", handleJobListChange);
  dom.analyzeResumeBtn.addEventListener("click", handleResumeAnalyze);
  dom.saveResumeBtn.addEventListener("click", handleResumeSave);
  dom.saveKeywordsBtn.addEventListener("click", handleKeywordsSave);
  dom.saveSettingsBtn.addEventListener("click", handleSettingsSave);
  dom.parseEmailBtn.addEventListener("click", handleEmailParse);
  dom.chatForm.addEventListener("submit", handleChat);
  dom.resumeUploadBtn.addEventListener("click", () => dom.resumeUpload.click());
  dom.coverLetterUploadBtn.addEventListener("click", () => dom.coverLetterUpload.click());
  dom.resumeUpload.addEventListener("change", () => setUploadStatus(dom.resumeUpload, dom.resumeUploadStatus));
  dom.coverLetterUpload.addEventListener("change", () => setUploadStatus(dom.coverLetterUpload, dom.coverLetterUploadStatus));
  dom.addJobModal.addEventListener("click", event => {
    if (event.target === dom.addJobModal) dom.addJobModal.classList.add("hidden");
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  attachEvents();
  if (window.lucide) {
    window.lucide.createIcons();
  }
  await checkAuth();
});

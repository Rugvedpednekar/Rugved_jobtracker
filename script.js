// ================================
// JobTracker Frontend Script
// ================================

const API_BASE = "";
let allJobs = [];
let parsedProfile = {};
let appSettings = {};
let dashboardData = null;

// --------------------
// DOM
// --------------------
const loginScreen = document.getElementById("login-screen");
const appShell = document.getElementById("app-shell");
const loginForm = document.getElementById("login-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const loginError = document.getElementById("login-error");

const toast = document.getElementById("toast");

const navButtons = document.querySelectorAll(".nav-btn");
const sectionPanels = document.querySelectorAll(".section-panel");

const mobileMenuBtn = document.getElementById("mobile-menu-btn");
const mobileMenu = document.getElementById("mobile-menu");

const logoutBtn = document.getElementById("logout-btn");
const mobileLogoutBtn = document.getElementById("mobile-logout-btn");

const addJobModal = document.getElementById("add-job-modal");
const addJobForm = document.getElementById("add-job-form");

const openAddJobBtn = document.getElementById("open-add-job");
const jobsAddBtn = document.getElementById("jobs-add-btn");
const closeAddJobModal = document.getElementById("close-add-job-modal");
const cancelAddJobModal = document.getElementById("cancel-add-job-modal");

const refreshDashboardBtn = document.getElementById("refresh-dashboard-btn");
const jobsRefreshBtn = document.getElementById("jobs-refresh-btn");

const analyzeResumeBtn = document.getElementById("analyze-resume-btn");
const analyzeResumeTopBtn = document.getElementById("analyze-resume-top-btn");
const saveResumeBtn = document.getElementById("save-resume-btn");
const saveKeywordsBtn = document.getElementById("save-keywords-btn");
const saveSettingsBtn = document.getElementById("save-settings-btn");
const parseEmailBtn = document.getElementById("parse-email-btn");

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

const jobsSearchInput = document.getElementById("jobs-search-input");
const jobsStatusFilter = document.getElementById("jobs-status-filter");
const jobsCompanyFilter = document.getElementById("jobs-company-filter");

const resumeBox = document.getElementById("resume-box");
const parsedProfileOutput = document.getElementById("parsed-profile-output");
const keywordBox = document.getElementById("keyword-box");

const syncWindow = document.getElementById("sync-window");
const preferredLocation = document.getElementById("preferred-location");
const userNotes = document.getElementById("user-notes");

const emailParserInput = document.getElementById("email-parser-input");
const emailJobLink = document.getElementById("email-job-link");
const parsedEmailStatus = document.getElementById("parsed-email-status");
const parsedEmailReason = document.getElementById("parsed-email-reason");

// Tracker stats
const wishlistCount = document.getElementById("wishlist-count");
const appliedCount = document.getElementById("applied-count");
const interviewCount = document.getElementById("interview-count");
const offeredCount = document.getElementById("offered-count");
const acceptedCount = document.getElementById("accepted-count");

const wishlistBadge = document.getElementById("wishlist-badge");
const appliedBadge = document.getElementById("applied-badge");
const interviewBadge = document.getElementById("interview-badge");
const offeredBadge = document.getElementById("offered-badge");
const acceptedBadge = document.getElementById("accepted-badge");

const wishlistColumn = document.getElementById("wishlist-column");
const appliedColumn = document.getElementById("applied-column");
const interviewColumn = document.getElementById("interview-column");
const offeredColumn = document.getElementById("offered-column");
const acceptedColumn = document.getElementById("accepted-column");

const recentJobsList = document.getElementById("recent-jobs-list");
const jobsList = document.getElementById("jobs-list");

// --------------------
// Helpers
// --------------------
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => toast.classList.add("hidden"), 2500);
}

function showLogin() {
  loginScreen.classList.remove("hidden");
  appShell.classList.add("hidden");
}

function showApp() {
  loginScreen.classList.add("hidden");
  appShell.classList.remove("hidden");
}

function activateSection(sectionId) {
  sectionPanels.forEach(panel => panel.classList.remove("active"));
  document.getElementById(sectionId)?.classList.add("active");

  navButtons.forEach(btn => {
    const active = btn.dataset.section === sectionId;
    btn.classList.toggle("active", active);
    btn.classList.toggle("bg-blue-800", active);
  });

  mobileMenu?.classList.add("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function safeJSON(res) {
  return res.json().catch(() => ({}));
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    },
    ...options
  });

  const data = await safeJSON(res);

  if (!res.ok) {
    const msg = data?.detail || data?.message || "Request failed";
    throw new Error(msg);
  }

  return data;
}

function formatStatusChip(status) {
  const map = {
    Wishlist: "chip chip-blue",
    Applied: "chip chip-blue",
    Interview: "chip chip-yellow",
    Offered: "chip chip-green",
    Accepted: "chip chip-green",
    Rejected: "chip chip-red"
  };
  return map[status] || "chip chip-blue";
}

function emptyState(text) {
  return `
    <div class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500 text-center">
      ${text}
    </div>
  `;
}

// --------------------
// Auth
// --------------------
async function checkAuth() {
  try {
    await api("/api/auth/me");
    showApp();
    await loadInitialData();
  } catch {
    showLogin();
  }
}

async function handleLogin(e) {
  e.preventDefault();
  loginError.classList.add("hidden");
  loginError.textContent = "";

  try {
    await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: loginEmail.value.trim(),
        password: loginPassword.value
      })
    });

    showToast("Login successful");
    showApp();
    await loadInitialData();
  } catch (err) {
    loginError.textContent = err.message || "Login failed";
    loginError.classList.remove("hidden");
  }
}

async function handleLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch {}
  showLogin();
  loginForm.reset();
  showToast("Logged out");
}

// --------------------
// Data loading
// --------------------
async function loadInitialData() {
  await Promise.all([
    loadDashboard(),
    loadJobs(),
    loadProfile(),
    loadSettings()
  ]);
}

async function loadDashboard() {
  dashboardData = await api("/api/dashboard/simple");
  renderDashboardSimple(dashboardData);
}

async function loadJobs() {
  allJobs = await api("/api/jobs");
  renderJobsList();
  populateEmailJobDropdown();
}

async function loadProfile() {
  const data = await api("/api/profile");
  resumeBox.value = data.resume_text || "";
  parsedProfile = data.parsed_profile || {};
  parsedProfileOutput.textContent = JSON.stringify(parsedProfile, null, 2);

  const keywordData = await api("/api/keywords");
  keywordBox.value = (keywordData.keywords || []).join("\n");
}

async function loadSettings() {
  const data = await api("/api/settings");
  appSettings = data.settings || {};
  syncWindow.value = String(appSettings.sync_window_hours || 24);
  preferredLocation.value = appSettings.preferred_location || "";
  userNotes.value = appSettings.user_notes || "";
}

// --------------------
// Rendering
// --------------------
function createTrackerCard(job) {
  return `
    <div class="job-card">
      <div class="flex items-start justify-between gap-3">
        <div>
          <p class="font-extrabold text-slate-900">${job.company || "Unknown Company"}</p>
          <p class="text-sm text-slate-600 mt-1">${job.role || "Unknown Role"}</p>
        </div>
        <span class="${formatStatusChip(job.status)}">${job.status || "Applied"}</span>
      </div>
      <div class="mt-3 text-xs text-slate-500">
        ${job.date || ""}
      </div>
    </div>
  `;
}

function renderDashboardSimple(data) {
  const stats = data?.stats || {};
  const columns = data?.columns || {};

  wishlistCount.textContent = stats.wishlist_count || 0;
  appliedCount.textContent = stats.applied_count || 0;
  interviewCount.textContent = stats.interview_count || 0;
  offeredCount.textContent = stats.offered_count || 0;
  acceptedCount.textContent = stats.accepted_count || 0;

  wishlistBadge.textContent = stats.wishlist_count || 0;
  appliedBadge.textContent = stats.applied_count || 0;
  interviewBadge.textContent = stats.interview_count || 0;
  offeredBadge.textContent = stats.offered_count || 0;
  acceptedBadge.textContent = stats.accepted_count || 0;

  wishlistColumn.innerHTML = (columns.Wishlist || []).length
    ? columns.Wishlist.map(createTrackerCard).join("")
    : emptyState("No wishlist jobs");

  appliedColumn.innerHTML = (columns.Applied || []).length
    ? columns.Applied.map(createTrackerCard).join("")
    : emptyState("No applied jobs");

  interviewColumn.innerHTML = (columns.Interview || []).length
    ? columns.Interview.map(createTrackerCard).join("")
    : emptyState("No interview jobs");

  offeredColumn.innerHTML = (columns.Offered || []).length
    ? columns.Offered.map(createTrackerCard).join("")
    : emptyState("No offered jobs");

  acceptedColumn.innerHTML = (columns.Accepted || []).length
    ? columns.Accepted.map(createTrackerCard).join("")
    : emptyState("No accepted jobs");

  const recentJobs = allJobs.slice(0, 6);
  recentJobsList.innerHTML = recentJobs.length
    ? recentJobs.map(job => `
        <div class="job-card">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="font-extrabold">${job.company}</p>
              <p class="text-sm text-slate-600 mt-1">${job.role}</p>
              <p class="text-xs text-slate-500 mt-2">${job.date || ""}</p>
            </div>
            <span class="${formatStatusChip(job.status)}">${job.status}</span>
          </div>
        </div>
      `).join("")
    : emptyState("No jobs added yet.");
}

function renderJobsList() {
  let filtered = [...allJobs];

  const search = (jobsSearchInput?.value || "").trim().toLowerCase();
  const status = jobsStatusFilter?.value || "all";
  const company = (jobsCompanyFilter?.value || "").trim().toLowerCase();

  if (search) {
    filtered = filtered.filter(job =>
      (job.company || "").toLowerCase().includes(search) ||
      (job.role || "").toLowerCase().includes(search)
    );
  }

  if (status !== "all") {
    filtered = filtered.filter(job => (job.status || "") === status);
  }

  if (company) {
    filtered = filtered.filter(job => (job.company || "").toLowerCase().includes(company));
  }

  jobsList.innerHTML = filtered.length ? filtered.map(job => `
    <div class="job-card">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div class="min-w-0">
          <p class="text-xl font-extrabold">${job.role || "Untitled Role"}</p>
          <p class="text-sm text-slate-700 font-semibold mt-1">${job.company || "Unknown Company"}</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span class="${formatStatusChip(job.status)}">${job.status || "Applied"}</span>
            ${job.field ? `<span class="chip chip-blue">${job.field}</span>` : ""}
            ${job.sponsor ? `<span class="chip chip-blue">${job.sponsor}</span>` : ""}
          </div>
          <div class="mt-3 text-sm text-slate-500 space-y-1">
            ${job.date ? `<p>Date: ${job.date}</p>` : ""}
            ${job.salary ? `<p>Salary: ${job.salary}</p>` : ""}
            ${job.notes ? `<p>Notes: ${job.notes}</p>` : ""}
          </div>
        </div>

        <div class="flex flex-col gap-2 lg:w-56">
          <select class="field job-status-change" data-id="${job.id}">
            <option value="Wishlist" ${job.status === "Wishlist" ? "selected" : ""}>Wishlist</option>
            <option value="Applied" ${job.status === "Applied" ? "selected" : ""}>Applied</option>
            <option value="Interview" ${job.status === "Interview" ? "selected" : ""}>Interview</option>
            <option value="Offered" ${job.status === "Offered" ? "selected" : ""}>Offered</option>
            <option value="Accepted" ${job.status === "Accepted" ? "selected" : ""}>Accepted</option>
            <option value="Rejected" ${job.status === "Rejected" ? "selected" : ""}>Rejected</option>
          </select>
          ${job.link ? `<a href="${job.link}" target="_blank" class="btn-soft text-center">Open Link</a>` : ""}
          <button class="btn-soft job-delete-btn" data-id="${job.id}">Delete</button>
        </div>
      </div>
    </div>
  `).join("") : emptyState("No tracked jobs yet.");

  document.querySelectorAll(".job-status-change").forEach(el => {
    el.addEventListener("change", async (e) => {
      const id = e.target.dataset.id;
      const status = e.target.value;
      await updateJobStatus(id, status);
    });
  });

  document.querySelectorAll(".job-delete-btn").forEach(el => {
    el.addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      await deleteJob(id);
    });
  });
}

function populateEmailJobDropdown() {
  emailJobLink.innerHTML = `<option value="">Link parsed status to tracked job</option>` +
    allJobs.map(job => `
      <option value="${job.id}">${job.company} — ${job.role}</option>
    `).join("");
}

// --------------------
// Jobs
// --------------------
async function createJob(e) {
  e.preventDefault();

  const payload = {
    company: document.getElementById("job-company").value.trim(),
    role: document.getElementById("job-role").value.trim(),
    status: document.getElementById("job-status").value,
    date: document.getElementById("job-date").value || new Date().toISOString().split("T")[0],
    field: document.getElementById("job-field").value.trim() || "Tech",
    salary: document.getElementById("job-salary").value.trim(),
    sponsor: document.getElementById("job-sponsor").value.trim() || "Unknown",
    link: document.getElementById("job-link").value.trim(),
    notes: document.getElementById("job-notes").value.trim()
  };

  try {
    await api("/api/jobs", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    addJobModal.classList.add("hidden");
    addJobForm.reset();
    showToast("Job added");
    await loadJobs();
    await loadDashboard();
    activateSection("tracker");
  } catch (err) {
    showToast(err.message || "Failed to add job");
  }
}

async function updateJobStatus(id, status) {
  try {
    await api(`/api/jobs/${id}`, {
      method: "PUT",
      body: JSON.stringify({ status })
    });
    showToast("Status updated");
    await loadJobs();
    await loadDashboard();
  } catch (err) {
    showToast(err.message || "Failed to update");
  }
}

async function deleteJob(id) {
  try {
    await api(`/api/jobs/${id}`, { method: "DELETE" });
    showToast("Job deleted");
    await loadJobs();
    await loadDashboard();
  } catch (err) {
    showToast(err.message || "Delete failed");
  }
}

// --------------------
// Profile / Settings
// --------------------
async function analyzeResume() {
  try {
    const data = await api("/api/resume/analyze", {
      method: "POST",
      body: JSON.stringify({ resume_text: resumeBox.value })
    });
    parsedProfileOutput.textContent = JSON.stringify(data.parsed_profile || {}, null, 2);
    showToast("Resume analyzed");
  } catch (err) {
    showToast(err.message || "Analyze failed");
  }
}

async function saveResume() {
  try {
    const parsed = JSON.parse(parsedProfileOutput.textContent || "{}");
    await api("/api/resume/save", {
      method: "POST",
      body: JSON.stringify({
        resume_text: resumeBox.value,
        parsed_profile: parsed
      })
    });
    showToast("Resume saved");
  } catch (err) {
    showToast(err.message || "Save failed");
  }
}

async function saveKeywords() {
  try {
    const keywords = keywordBox.value
      .split("\n")
      .map(x => x.trim())
      .filter(Boolean);

    await api("/api/keywords", {
      method: "POST",
      body: JSON.stringify({ keywords })
    });
    showToast("Keywords saved");
  } catch (err) {
    showToast(err.message || "Keyword save failed");
  }
}

async function saveSettings() {
  try {
    await api("/api/settings", {
      method: "POST",
      body: JSON.stringify({
        sync_window_hours: Number(syncWindow.value || 24),
        preferred_location: preferredLocation.value.trim(),
        user_notes: userNotes.value.trim()
      })
    });
    showToast("Settings saved");
  } catch (err) {
    showToast(err.message || "Settings save failed");
  }
}

// --------------------
// Email parser
// --------------------
async function parseEmail() {
  try {
    const data = await api("/api/email/parse", {
      method: "POST",
      body: JSON.stringify({
        email_text: emailParserInput.value,
        job_id: emailJobLink.value || null
      })
    });

    parsedEmailStatus.textContent = data.status || "No signal detected";
    parsedEmailReason.textContent = data.reason || "No explanation available";
    showToast("Email parsed");

    await loadJobs();
    await loadDashboard();
  } catch (err) {
    showToast(err.message || "Email parsing failed");
  }
}

// --------------------
// Chat
// --------------------
function appendChatBubble(text, role = "assistant") {
  const bubble = document.createElement("div");
  bubble.className = role === "user"
    ? "rounded-2xl bg-blue-600 text-white p-3 text-sm ml-8"
    : "rounded-2xl bg-white border border-slate-200 p-3 text-sm mr-8 text-slate-700";
  bubble.textContent = text;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function handleChat(e) {
  e.preventDefault();
  const message = chatInput.value.trim();
  if (!message) return;

  appendChatBubble(message, "user");
  chatInput.value = "";

  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message })
    });
    appendChatBubble(data.answer || "No response from AI.", "assistant");
  } catch (err) {
    appendChatBubble(err.message || "Chat failed", "assistant");
  }
}

// --------------------
// Events
// --------------------
loginForm?.addEventListener("submit", handleLogin);
logoutBtn?.addEventListener("click", handleLogout);
mobileLogoutBtn?.addEventListener("click", handleLogout);

navButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const section = btn.dataset.section;
    if (section) activateSection(section);
  });
});

mobileMenuBtn?.addEventListener("click", () => {
  mobileMenu?.classList.toggle("hidden");
});

openAddJobBtn?.addEventListener("click", () => addJobModal.classList.remove("hidden"));
jobsAddBtn?.addEventListener("click", () => addJobModal.classList.remove("hidden"));
closeAddJobModal?.addEventListener("click", () => addJobModal.classList.add("hidden"));
cancelAddJobModal?.addEventListener("click", () => addJobModal.classList.add("hidden"));

addJobForm?.addEventListener("submit", createJob);

refreshDashboardBtn?.addEventListener("click", async () => {
  await loadDashboard();
  await loadJobs();
  showToast("Dashboard refreshed");
});

jobsRefreshBtn?.addEventListener("click", async () => {
  await loadJobs();
  showToast("Jobs refreshed");
});

jobsSearchInput?.addEventListener("input", renderJobsList);
jobsStatusFilter?.addEventListener("change", renderJobsList);
jobsCompanyFilter?.addEventListener("input", renderJobsList);

analyzeResumeBtn?.addEventListener("click", analyzeResume);
analyzeResumeTopBtn?.addEventListener("click", analyzeResume);
saveResumeBtn?.addEventListener("click", saveResume);
saveKeywordsBtn?.addEventListener("click", saveKeywords);
saveSettingsBtn?.addEventListener("click", saveSettings);
parseEmailBtn?.addEventListener("click", parseEmail);

chatForm?.addEventListener("submit", handleChat);

// --------------------
// Init
// --------------------
window.addEventListener("DOMContentLoaded", async () => {
  lucide.createIcons();
  await checkAuth();
});

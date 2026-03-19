// Initialize Lucide Icons
lucide.createIcons();

// ── Config ──
const API_BASE = "http://127.0.0.1:8000"; // Pointing to your FastAPI server
const GOOGLE_CLIENT_ID = "532659628621-les06562lchufnus0e4d3dm8rcuofnl6.apps.googleusercontent.com";
const COLUMNS = ["Applied", "Interview", "Offer", "Rejected"];

// ── State ──
let jobs = [];
let googleUser = null;

// ── DOM Elements ──
const boardEl = document.getElementById('board');
const statsEl = document.getElementById('stats-container');
const addModal = document.getElementById('add-modal');
const addForm = document.getElementById('add-job-form');
const toastEl = document.getElementById('toast');

// ── Toast Notifications ──
function showToast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.remove('hidden');
    setTimeout(() => toastEl.classList.add('hidden'), 3000);
}

// ── API Calls ──
async function fetchJobs() {
    try {
        const res = await fetch(`${API_BASE}/api/jobs`);
        jobs = await res.json();
        renderApp();
    } catch (e) {
        showToast("Database Offline. Start FastAPI.");
        console.error(e);
    }
}

async function handleAddJob(e) {
    e.preventDefault();
    const company = document.getElementById('job-company').value;
    const role = document.getElementById('job-role').value;
    const status = document.getElementById('job-status').value;

    const newJob = {
        id: Math.random().toString(36).slice(2, 9),
        company, role, status, 
        date: new Date().toISOString().split('T')[0],
        field: "Tech", sponsor: "Unknown", notes: "", link: "", salary: ""
    };

    // Optimistic UI update
    jobs.push(newJob);
    renderApp();
    addModal.classList.add('hidden');
    addForm.reset();

    try {
        await fetch(`${API_BASE}/api/jobs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newJob)
        });
        showToast("Saved to Database!");
    } catch (e) { showToast("Failed to save."); }
}

async function updateStatus(id, newStatus) {
    const job = jobs.find(j => j.id === id);
    if(job) job.status = newStatus;
    renderApp();

    try {
        await fetch(`${API_BASE}/api/jobs/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
    } catch (e) { showToast("Update failed."); }
}

async function deleteJob(id) {
    jobs = jobs.filter(j => j.id !== id);
    renderApp();
    try {
        await fetch(`${API_BASE}/api/jobs/${id}`, { method: 'DELETE' });
        showToast("Job deleted.");
    } catch (e) { showToast("Delete failed."); }
}

// ── Rendering ──
function renderApp() {
    renderStats();
    renderBoard();
    lucide.createIcons(); // Re-initialize icons for new DOM elements
}

function renderStats() {
    const total = jobs.length;
    const interviews = jobs.filter(j => j.status === 'Interview' || j.status === 'Offer').length;
    
    statsEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-val">${total}</div>
            <div class="stat-label">Applied</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="color: #10b981;">${interviews}</div>
            <div class="stat-label">Interviews</div>
        </div>
    `;
}

function renderBoard() {
    boardEl.innerHTML = '';
    
    COLUMNS.forEach(col => {
        const colJobs = jobs.filter(j => j.status === col);
        const colDiv = document.createElement('div');
        colDiv.className = 'board-col';
        
        let cardsHtml = colJobs.map(job => `
            <div class="job-card">
                <div class="job-company">${job.company}</div>
                <div class="job-role">${job.role}</div>
                <select class="job-status-select" onchange="updateStatus('${job.id}', this.value)">
                    ${COLUMNS.map(c => `<option value="${c}" ${job.status === c ? 'selected' : ''}>${c}</option>`).join('')}
                </select>
                <div class="card-actions">
                    <span style="font-size:11px; color:#64748b;">${job.date}</span>
                    <button class="delete-btn" onclick="deleteJob('${job.id}')"><i data-lucide="trash-2" style="width:16px; height:16px;"></i></button>
                </div>
            </div>
        `).join('');

        colDiv.innerHTML = `
            <div class="col-header">
                <span>${col}</span>
                <span class="col-count">${colJobs.length}</span>
            </div>
            ${cardsHtml}
        `;
        boardEl.appendChild(colDiv);
    });
}

// ── Google Auth ──
window.onload = function () {
    google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse
    });
    
    document.getElementById('login-btn').onclick = () => {
        google.accounts.id.prompt();
    };
};

function handleCredentialResponse(response) {
    // Decode JWT token
    const payload = JSON.parse(atob(response.credential.split('.')[1]));
    googleUser = payload;
    
    document.getElementById('login-btn').classList.add('hidden');
    document.getElementById('user-profile').classList.remove('hidden');
    document.getElementById('user-avatar').src = payload.picture;
    showToast(`Signed in as ${payload.given_name}`);
}

document.getElementById('logout-btn').onclick = () => {
    googleUser = null;
    document.getElementById('login-btn').classList.remove('hidden');
    document.getElementById('user-profile').classList.add('hidden');
    showToast("Signed out.");
};

// ── Event Listeners ──
document.getElementById('add-btn').onclick = () => addModal.classList.remove('hidden');
document.getElementById('close-modal').onclick = () => addModal.classList.add('hidden');
addForm.onsubmit = handleAddJob;

// Start App
fetchJobs();
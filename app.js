const API_URL = 'http://127.0.0.1:8000';
let currentToken = localStorage.getItem('token');
let previewModalInstance = null;
let statusModalInstance = null;
let currentModalMode = '';

// --- US Date Formatter ---
function formatToUSDate(dateString) {
    if (!dateString) return '';
    if (dateString.includes('-')) {
        const [year, month, day] = dateString.split('-');
        return `${month}/${day}/${year}`;
    }
    if (dateString.includes('/')) {
        const [day, month, year] = dateString.split('/');
        return `${month}/${day}/${year}`;
    }
    return dateString;
}

// --- JWT Role Decoder ---
function getUserRole() {
    if (!currentToken) return null;
    try {
        const payload = JSON.parse(atob(currentToken.split('.')[1]));
        return payload.role || null;
    } catch (e) { return null; }
}

// --- Navbar Update ---
function updateNavbar() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.textContent.trim().toUpperCase() === 'LOGIN') {
            if (currentToken) {
                const payload = JSON.parse(atob(currentToken.split('.')[1]));
                const username = payload.sub || 'User';
                link.textContent = `LOGOUT (${username})`;
                link.href = '#';
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    localStorage.removeItem('token');
                    currentToken = null;
                    window.location.href = 'index.html';
                });
            }
        }
    });
}
document.addEventListener('DOMContentLoaded', updateNavbar);

// --- Form Submission ---
const leadForm = document.getElementById('leadForm');
if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!leadForm.checkValidity()) {
            e.stopPropagation();
            leadForm.classList.add('was-validated');
            return;
        }
        leadForm.classList.remove('was-validated');

        const stakeholders = document.getElementById('stakeholders').value;
        const data = {
            title: document.getElementById('title').value,
            organization: document.getElementById('organization').value,
            background: document.getElementById('background').value,
            challenge: document.getElementById('challenge').value,
            scope: document.getElementById('scope').value,
            requirements: document.getElementById('requirements').value,
            risks: document.getElementById('risks').value || null,
            time_plan: document.getElementById('time_plan').value,
            active_wbs: document.getElementById('active_wbs').value || null,
            contact_email: document.getElementById('contact_email').value,
            owner_email: document.getElementById('owner_email').value,
            stakeholders: stakeholders ? stakeholders.split(',').map(s => s.trim()) : []
        };

        try {
            const res = await fetch(`${API_URL}/leads`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            const resultDiv = document.getElementById('submitResult');
            resultDiv.classList.remove('d-none', 'alert-success', 'alert-danger');

            if (res.ok) {
                const result = await res.json();
                resultDiv.classList.add('alert-success');
                resultDiv.innerHTML = `Success! Tracking ID: <strong>${result.tracking_id}</strong>`;
                leadForm.reset();
            } else {
                resultDiv.classList.add('alert-danger');
                resultDiv.innerText = 'Error submitting lead. Check if backend is running.';
            }
        } catch (err) { console.error(err); alert('Cannot connect to the server.'); }
    });
}

// --- Track Status ---
const trackForm = document.getElementById('trackForm');
if (trackForm) {
    trackForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const trackingId = document.getElementById('trackingId').value;
        const resDiv = document.getElementById('trackResult');
        const errDiv = document.getElementById('trackError');

        try {
            const res = await fetch(`${API_URL}/track/${trackingId}`);
            if (res.ok) {
                const data = await res.json();
                document.getElementById('trackTitle').innerText = data.title;
                document.getElementById('trackStatus').innerText = data.status;
                document.getElementById('trackVerifier').innerText = data.assigned_verifier || 'None';
                document.getElementById('trackComments').innerText = data.verifier_comments || 'No comments';
                resDiv.classList.remove('d-none');
                errDiv.classList.add('d-none');
            } else {
                resDiv.classList.add('d-none');
                errDiv.classList.remove('d-none');
                errDiv.innerText = 'Lead not found. Please check your Tracking ID.';
            }
        } catch (err) { console.error(err); }
    });
}

// --- Authentication & Dashboard ---
const loginForm = document.getElementById('loginForm');
const dashboardSec = document.getElementById('dashboardSection');
const loginSec = document.getElementById('loginSection');

if (dashboardSec) {
    if (currentToken) showDashboard();

    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new URLSearchParams();
        formData.append('username', document.getElementById('username').value);
        formData.append('password', document.getElementById('password').value);

        try {
            const res = await fetch(`${API_URL}/auth`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('token', data.access_token);
                currentToken = data.access_token;
                window.location.reload();
            } else {
                document.getElementById('loginError').classList.remove('d-none');
            }
        } catch (err) { console.error(err); }
    });

    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        localStorage.removeItem('token');
        currentToken = null;
        window.location.reload();
    });
}

function showDashboard() {
    loginSec.classList.add('d-none');
    dashboardSec.classList.remove('d-none');
    loadLeads();
    loadLeaders();
}

async function loadLeads() {
    try {
        const res = await fetch(`${API_URL}/leads`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (res.ok) {
            const leads = await res.json();
            const tbody = document.getElementById('leadsTableBody');
            tbody.innerHTML = '';
            
            const role = getUserRole();
            
            leads.forEach(lead => {
                let actionBtn = '';
                if (role === 'verifier') {
                    actionBtn = `<button class="btn btn-sm btn-status-outline" onclick="openAssignModal(${lead.id})">Assign Coordinator</button>`;
                } else if (role === 'leader') {
                    actionBtn = `<button class="btn btn-sm btn-status-outline" onclick="openStatusModal(${lead.id}, '${lead.status}')">Update Status</button>`;
                }

                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${lead.id}</td>
                    <td>${lead.title}</td>
                    <td>${lead.organization}</td>
                    <td>${formatToUSDate(lead.time_plan)}</td>
                    <td><span class="badge bg-secondary">${lead.status}</span></td>
                    <td>
                        <div class="btn-group shadow-sm" role="group">
                            <button class="btn btn-sm btn-preview" onclick="openPreviewModal(${lead.id})">Preview</button>
                            ${actionBtn}
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) { console.error(err); }
}

async function loadLeaders() {
    const role = getUserRole();
    if (role !== 'verifier') return;

    try {
        const res = await fetch(`${API_URL}/leaders`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (res.ok) {
            const leaders = await res.json();
            document.getElementById('leadersSection').classList.remove('d-none');
            const tbody = document.getElementById('leadersTableBody');
            tbody.innerHTML = '';
            
            leaders.forEach(leader => {
                if (leader.lead_ids && leader.lead_ids.length > 0) {
                    leader.lead_ids.forEach((leadId, index) => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td>${leader.username}</td>
                            <td>${leadId}</td>
                            <td>${leader.lead_titles[index]}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" style="border-radius:0; font-weight:700;" onclick="unassignLeader(${leadId})">UNASSIGN</button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
            });
        }
    } catch (err) { console.error(err); }
}

async function unassignLeader(leadId) {
    if(!confirm(`Are you sure you want to unassign the coordinator from lead ID: ${leadId}?`)) return;
    try {
        const res = await fetch(`${API_URL}/leads/${leadId}/unassign-leader`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${currentToken}` }
        });
        if (res.ok) {
            loadLeads();
            loadLeaders();
        } else {
            const errorData = await res.json();
            alert(`Error: ${errorData.detail}`);
        }
    } catch (err) { console.error(err); }
}

// --- Preview Modal ---
async function openPreviewModal(leadId) {
    try {
        const res = await fetch(`${API_URL}/leads/${leadId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (!res.ok) throw new Error('Error fetching lead details.');
        
        const lead = await res.json();
        
        document.getElementById('previewId').innerText = lead.id;
        document.getElementById('previewTitle').value = lead.title;
        document.getElementById('previewOrg').value = lead.organization;
        document.getElementById('previewBackground').value = lead.background;
        document.getElementById('previewChallenge').value = lead.challenge;
        document.getElementById('previewScope').value = lead.scope;
        document.getElementById('previewRequirements').value = lead.requirements;
        document.getElementById('previewRisks').value = lead.risks || 'No risks provided';
        document.getElementById('previewTime').value = formatToUSDate(lead.time_plan);
        document.getElementById('previewWbs').value = lead.active_wbs || 'None';
        document.getElementById('previewContact').value = lead.contact_email;
        document.getElementById('previewOwner').value = lead.owner_email;
        document.getElementById('previewStakeholders').value = lead.stakeholders?.join(', ') || 'None';

        const modalEl = document.getElementById('previewModal');
        if(!previewModalInstance) previewModalInstance = new bootstrap.Modal(modalEl);
        previewModalInstance.show();

        modalEl.addEventListener('shown.bs.modal', () => {
            modalEl.querySelectorAll('textarea.auto-resize').forEach(ta => {
                ta.style.height = 'auto'; 
                ta.style.height = (ta.scrollHeight + 3) + 'px'; 
            });
        }, { once: true });
        
    } catch (err) { console.error(err); alert('Critical connection error.'); }
}

// --- Modal Management (Split Logic) ---
function openAssignModal(leadId) {
    currentModalMode = 'assign';
    document.getElementById('modalLeadId').value = leadId;
    document.getElementById('modalLeaderEmail').value = '';

    document.querySelector('#statusModal .modal-title').innerText = 'Assign Leads Coordinator';
    document.getElementById('modalLeaderEmail').parentElement.classList.remove('d-none');
    document.getElementById('modalStatus').parentElement.classList.add('d-none');
    document.getElementById('modalComments').parentElement.classList.add('d-none');

    if(!statusModalInstance) statusModalInstance = new bootstrap.Modal(document.getElementById('statusModal'));
    statusModalInstance.show();
}

function openStatusModal(leadId, currentStatus) {
    currentModalMode = 'status';
    document.getElementById('modalLeadId').value = leadId;
    document.getElementById('modalStatus').value = currentStatus;
    document.getElementById('modalComments').value = '';

    document.querySelector('#statusModal .modal-title').innerText = 'Update Status';
    document.getElementById('modalLeaderEmail').parentElement.classList.add('d-none');
    document.getElementById('modalStatus').parentElement.classList.remove('d-none');
    document.getElementById('modalComments').parentElement.classList.remove('d-none');

    if(!statusModalInstance) statusModalInstance = new bootstrap.Modal(document.getElementById('statusModal'));
    statusModalInstance.show();
}

document.getElementById('saveStatusBtn')?.addEventListener('click', async () => {
    const leadId = document.getElementById('modalLeadId').value;

    if (currentModalMode === 'assign') {
        const leaderEmail = document.getElementById('modalLeaderEmail').value;
        try {
            const res = await fetch(`${API_URL}/leads/${leadId}/assign-leader`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify({ project_leader_email: leaderEmail })
            });

            if (res.ok) {
                statusModalInstance.hide();
                loadLeads();
                loadLeaders();
            } else {
                const errorData = await res.json();
                alert(`Error: ${errorData.detail}`);
            }
        } catch (err) { console.error(err); }

    } else if (currentModalMode === 'status') {
        const data = {
            status: document.getElementById('modalStatus').value,
            verifier_comments: document.getElementById('modalComments').value || null
        };

        try {
            const res = await fetch(`${API_URL}/leads/${leadId}/status`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                statusModalInstance.hide();
                loadLeads();
            } else {
                const errorData = await res.json();
                alert(`Error: ${errorData.detail}`);
            }
        } catch (err) { console.error(err); }
    }
});

// --- Change Password ---
document.getElementById('savePwdBtn')?.addEventListener('click', async () => {
    const old_password = document.getElementById('oldPassword').value;
    const new_password = document.getElementById('newPassword').value;
    const resDiv = document.getElementById('pwdResult');
    
    try {
        const res = await fetch(`${API_URL}/auth/change-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentToken}` },
            body: JSON.stringify({ old_password, new_password })
        });
        
        resDiv.classList.remove('d-none', 'alert-success', 'alert-danger');
        if (res.ok) {
            resDiv.classList.add('alert-success');
            resDiv.innerText = 'Password updated successfully!';
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('passwordModal')).hide();
                document.getElementById('oldPassword').value = '';
                document.getElementById('newPassword').value = '';
                resDiv.classList.add('d-none');
            }, 1500);
        } else {
            resDiv.classList.add('alert-danger');
            resDiv.innerText = 'Failed to update password. Check your old password.';
        }
    } catch (err) { console.error(err); }
});
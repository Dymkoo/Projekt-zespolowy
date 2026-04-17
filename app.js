const API_URL = 'http://127.0.0.1:8000';
let currentToken = localStorage.getItem('token');
let previewModalInstance = null;
let statusModalInstance = null;

// --- 1. Form Submission (index.html) ---
const leadForm = document.getElementById('leadForm');
if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Custom HTML5 Validation
        if (!leadForm.checkValidity()) {
            e.stopPropagation();
            leadForm.classList.add('was-validated');
            const firstInvalid = leadForm.querySelector(':invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
            }
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
            spoc_email: document.getElementById('spoc_email').value,
            business_owner_email: document.getElementById('business_owner_email').value,
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
                resultDiv.innerText = 'Error submitting lead. Please try again.';
            }
        } catch (err) { console.error('Submission error:', err); }
    });
}

// --- 2. Lead Tracking (track.html) ---
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
        } catch (err) { console.error('Tracking error:', err); }
    });
}

// --- 3. Authentication & Dashboard Table (dashboard.html) ---
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
                showDashboard();
            } else {
                document.getElementById('loginError').classList.remove('d-none');
            }
        } catch (err) { console.error('Login error:', err); }
    });

    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        localStorage.removeItem('token');
        currentToken = null;
        loginSec.classList.remove('d-none');
        dashboardSec.classList.add('d-none');
    });
}

function showDashboard() {
    loginSec.classList.add('d-none');
    dashboardSec.classList.remove('d-none');
    loadLeads();
}

async function loadLeads() {
    try {
        const res = await fetch(`${API_URL}/leads`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (res.ok) {
            const leads = await res.json();
            const tbody = document.getElementById('leadsTableBody');
            tbody.innerHTML = '';
            
            leads.forEach(lead => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${lead.id}</td>
                    <td>${lead.title}</td>
                    <td>${lead.organization}</td>
                    <td>${lead.time_plan}</td>
                    <td><span class="badge bg-secondary">${lead.status}</span></td>
                    <td>
                        <div class="btn-group shadow-sm" role="group">
                            <button class="btn btn-sm btn-preview" onclick="openPreviewModal(${lead.id})">Preview</button>
                            <button class="btn btn-sm btn-status-outline" onclick="openStatusModal(${lead.id}, '${lead.status}')">Update Status</button>
                        </div>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) { console.error('Fetch leads error:', err); }
}

// --- 4. Preview Modal ---
async function openPreviewModal(leadId) {
    try {
        const res = await fetch(`${API_URL}/leads/${leadId}`, { headers: { 'Authorization': `Bearer ${currentToken}` } });
        if (!res.ok) throw new Error('Error fetching lead details.');
        
        const lead = await res.json();
        
        // Populate fields
        document.getElementById('previewId').innerText = lead.id;
        document.getElementById('previewTitle').value = lead.title;
        document.getElementById('previewOrg').value = lead.organization;
        document.getElementById('previewBackground').value = lead.background;
        document.getElementById('previewChallenge').value = lead.challenge;
        document.getElementById('previewScope').value = lead.scope;
        document.getElementById('previewRequirements').value = lead.requirements;
        document.getElementById('previewRisks').value = lead.risks || 'No risks provided';
        document.getElementById('previewTime').value = lead.time_plan;
        document.getElementById('previewWbs').value = lead.active_wbs || 'None';
        document.getElementById('previewSpoc').value = lead.spoc_email;
        document.getElementById('previewOwner').value = lead.business_owner_email;
        document.getElementById('previewStakeholders').value = lead.stakeholders?.join(', ') || 'None';

        // Open modal
        const modalEl = document.getElementById('previewModal');
        if(!previewModalInstance) previewModalInstance = new bootstrap.Modal(modalEl);
        previewModalInstance.show();

        // Auto-resize textareas on modal load
        modalEl.addEventListener('shown.bs.modal', () => {
            modalEl.querySelectorAll('textarea.auto-resize').forEach(ta => {
                ta.style.height = 'auto'; 
                ta.style.height = (ta.scrollHeight + 3) + 'px'; 
            });
        }, { once: true });
        
    } catch (err) {
        console.error(err);
        alert('Critical connection error.');
    }
}

// --- 5. Status Update Modal ---
function openStatusModal(leadId, currentStatus) {
    document.getElementById('modalLeadId').value = leadId;
    document.getElementById('modalStatus').value = currentStatus;
    document.getElementById('modalComments').value = '';
    
    if(!statusModalInstance) statusModalInstance = new bootstrap.Modal(document.getElementById('statusModal'));
    statusModalInstance.show();
}

document.getElementById('saveStatusBtn')?.addEventListener('click', async () => {
    const leadId = document.getElementById('modalLeadId').value;
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
        }
    } catch (err) { console.error('Status update error:', err); }
});
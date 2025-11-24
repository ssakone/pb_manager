// Admin User Management for PocketBase Instances

let currentAdminInstanceId = null;

// Open admin manager
function openAdminManager(instanceId) {
    currentAdminInstanceId = instanceId;
    
    const modal = document.getElementById('adminManagerModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    loadAdmins();
}

// Close admin manager
function closeAdminManager() {
    const modal = document.getElementById('adminManagerModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentAdminInstanceId = null;
}

// Load admins for current instance
async function loadAdmins() {
    if (!currentAdminInstanceId) return;
    
    try {
        const response = await fetch(`/api/instances/${currentAdminInstanceId}/admins`);
        const result = await response.json();
        
        if (result.success) {
            renderAdminList(result.admins);
        } else {
            showNotification('Error loading admins: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Render admin list
function renderAdminList(admins) {
    const container = document.getElementById('adminList');
    
    if (admins.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <i class="fas fa-user-shield text-6xl mb-4"></i>
                <p class="font-mono">No admin users found</p>
                <p class="text-sm mt-2">Add your first admin user using the form below</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = admins.map(admin => {
        const createdDate = new Date(admin.created).toLocaleString();
        const updatedDate = new Date(admin.updated).toLocaleString();
        const isOnlyAdmin = admins.length === 1;
        const verifiedBadge = admin.verified ? '<span class="text-xs bg-green-600 text-white px-2 py-1 ml-2 font-bold">✓ VERIFIED</span>' : '';
        
        return `
            <div class="border-2 border-black p-4 hover:bg-gray-50 transition-colors">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-2 flex-wrap">
                            <i class="fas fa-user-shield text-lg"></i>
                            <span class="font-bold font-mono">${admin.email}</span>
                            ${isOnlyAdmin ? '<span class="text-xs bg-yellow-400 text-black px-2 py-1 ml-2 font-bold">ONLY ADMIN</span>' : ''}
                            ${verifiedBadge}
                        </div>
                        <div class="text-xs text-gray-600 font-mono space-y-1">
                            <div><strong>ID:</strong> ${admin.id}</div>
                            <div><strong>Created:</strong> ${createdDate}</div>
                            <div><strong>Updated:</strong> ${updatedDate}</div>
                            <div><strong>Email Visibility:</strong> ${admin.emailVisibility ? 'Yes' : 'No'}</div>
                        </div>
                    </div>
                    <button onclick="deleteAdmin('${admin.id}', '${admin.email}', ${isOnlyAdmin})" 
                            class="btn btn-danger text-xs ${isOnlyAdmin ? 'opacity-50 cursor-not-allowed' : ''}"
                            ${isOnlyAdmin ? 'disabled' : ''}>
                        <i class="fas fa-trash mr-1"></i> DELETE
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Open add admin dialog
function openAddAdminDialog() {
    const email = document.getElementById('newAdminEmail');
    const password = document.getElementById('newAdminPassword');
    
    // Clear form
    email.value = '';
    password.value = '';
    
    // Show form
    document.getElementById('addAdminForm').classList.remove('hidden');
}

// Close add admin dialog
function closeAddAdminDialog() {
    document.getElementById('addAdminForm').classList.add('hidden');
}

// Add new admin
async function addAdmin(event) {
    event.preventDefault();
    
    const email = document.getElementById('newAdminEmail').value;
    const password = document.getElementById('newAdminPassword').value;
    
    if (!email || !password) {
        showNotification('Email and password are required', 'error');
        return;
    }
    
    try {
        showNotification('Adding admin user...', 'info');
        
        const response = await fetch(`/api/instances/${currentAdminInstanceId}/admins`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            closeAddAdminDialog();
            loadAdmins();
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Delete admin
async function deleteAdmin(adminId, email, isOnlyAdmin) {
    if (isOnlyAdmin) {
        showNotification('Cannot delete the last admin user', 'error');
        return;
    }
    
    const message = `Are you sure you want to delete admin user "${email}"?\n\nThis action cannot be undone.`;
    
    if (!confirm(message)) return;
    
    try {
        showNotification('Deleting admin user...', 'info');
        
        const response = await fetch(`/api/instances/${currentAdminInstanceId}/admins/${adminId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadAdmins();
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Refresh admin list
function refreshAdmins() {
    loadAdmins();
    showNotification('Refreshed', 'info');
}

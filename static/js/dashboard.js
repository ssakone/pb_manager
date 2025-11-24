// Dashboard functionality

let currentLogsInstanceId = null;
let refreshInterval = null;
const REFRESH_RATE = 2000; // 2 seconds

// Start auto-refresh
document.addEventListener('DOMContentLoaded', () => {
    refreshInstances();
    refreshInterval = setInterval(refreshInstances, REFRESH_RATE);
});

// Modal functions (Create Instance)
async function loadCreateVersions() {
    console.log('loadCreateVersions called');
    const select = document.querySelector('#createForm select[name="version"]');
    
    console.log('Select element:', select);
    console.log('Select exists:', !!select);
    
    if (!select) {
        console.error('Version select not found');
        console.log('Looking for all selects:', document.querySelectorAll('select'));
        return;
    }
    
    console.log('Select initial innerHTML:', select.innerHTML);
    console.log('Select initial options count:', select.options.length);
    
    select.innerHTML = '<option value="">Chargement des versions...</option>';
    select.disabled = true;
    
    try {
        const response = await fetch('/api/versions');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        console.log('Versions loaded (create modal):', result);
        console.log('Versions count (create modal):', result.versions?.length);
        
        if (result.success && result.versions && result.versions.length > 0) {
            console.log('Before clearing (create modal), options:', select.options.length);
            select.innerHTML = '<option value="">Sélectionnez une version...</option>';
            console.log('After clearing (create modal), options:', select.options.length);
            
            result.versions.forEach((version, index) => {
                const option = document.createElement('option');
                option.value = version.version;
                option.textContent = `v${version.version} (${version.name})`;
                select.appendChild(option);
                console.log(`Added option (create modal) ${index + 1}:`, option.textContent);
            });
            
            select.disabled = false;
            console.log('Final options count (create modal):', select.options.length);
            console.log('Final select innerHTML length (create modal):', select.innerHTML.length);
        } else {
            select.innerHTML = '<option value="">Aucune version disponible</option>';
            showNotification('Erreur: ' + (result.error || 'Aucune version trouvée'), 'error');
        }
    } catch (error) {
        console.error('Failed to load versions:', error);
        select.innerHTML = '<option value="">Erreur de chargement</option>';
        showNotification('Impossible de charger les versions PocketBase. Vérifiez votre connexion.', 'error');
    }
}

function openCreateModal() {
    document.getElementById('createModal').classList.remove('hidden');
    document.getElementById('createModal').classList.add('flex');
    
    // Wait for modal to render before loading versions
    setTimeout(() => {
        loadCreateVersions();
    }, 100);
}

function closeCreateModal() {
    document.getElementById('createModal').classList.add('hidden');
    document.getElementById('createModal').classList.remove('flex');
    document.getElementById('createForm').reset();
}

function closeLogsModal() {
    document.getElementById('logsModal').classList.add('hidden');
    document.getElementById('logsModal').classList.remove('flex');
    currentLogsInstanceId = null;
}

// Change domain
async function changeDomain(instanceId) {
    const newDomain = prompt('Entrez le nouveau domaine (laissez vide pour supprimer):');
    
    if (newDomain === null) return; // User cancelled
    
    try {
        showNotification('Mise à jour du domaine...', 'info');
        
        const response = await fetch(`/api/instances/${instanceId}/domain`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain: newDomain || null })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            refreshInstances();
        } else {
            showNotification('Erreur: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Erreur réseau: ' + error.message, 'error');
    }
}

// Render Instance Card HTML
function renderInstanceCard(instance) {
    const isOnline = instance.pm2_status === 'online';
    const isStopped = instance.pm2_status === 'stopped';
    const isDev = instance.dev_mode;
    const baseUrl = instance.domain ? `https://${instance.domain}` : `http://localhost:${instance.port}`;
    const displayUrl = instance.domain || `localhost:${instance.port}`;
    
    return `
    <div class="card relative group hover:bg-gray-50 transition-colors duration-200" id="instance-card-${instance.id}">
        <!-- Header -->
        <div class="flex justify-between items-start mb-6">
            <div>
                <h3 class="text-xl font-bold">${instance.name}</h3>
                <p class="text-sm font-mono mt-1">v${instance.version}</p>
            </div>
            <span class="status-badge status-${instance.pm2_status}">
                ${instance.pm2_status}
            </span>
        </div>

        <!-- Info -->
        <div class="space-y-3 mb-6 font-mono text-sm border-t-2 border-b-2 border-black py-4">
            <div class="flex justify-between items-center">
                <span class="font-bold">${instance.domain ? 'URL' : 'PORT'}</span>
                <a href="${baseUrl}" target="_blank" class="hover:underline decoration-2 underline-offset-2 flex items-center gap-1">
                    ${displayUrl} <i class="fas fa-external-link-alt text-xs"></i>
                </a>
            </div>
            ${instance.pid ? `
            <div class="flex justify-between items-center">
                <span class="font-bold">PID</span>
                <span>${instance.pid}</span>
            </div>` : ''}
            ${isOnline ? `
            <div class="flex justify-between items-center">
                <span class="font-bold">ADMIN</span>
                <a href="${baseUrl}/_/" target="_blank" class="hover:underline decoration-2 underline-offset-2">
                    OPEN DASHBOARD
                </a>
            </div>` : ''}
            <div class="flex justify-between items-center">
                <span class="font-bold">DEV MODE</span>
                <span class="${isDev ? 'font-bold bg-black text-white px-1' : ''}">
                    ${isDev ? 'ON' : 'OFF'}
                </span>
            </div>
            <div class="flex justify-between items-center">
                <span class="font-bold">DOMAIN</span>
                <button onclick="changeDomain(${instance.id})" class="text-xs hover:underline decoration-2 underline-offset-2">
                    ${instance.domain || 'None'} <i class="fas fa-edit ml-1"></i>
                </button>
            </div>
        </div>

        <!-- Actions -->
        <div class="grid grid-cols-3 gap-2 mb-2">
            ${isStopped ? `
            <button onclick="startInstance(${instance.id})" 
                    class="btn btn-secondary text-xs" title="Start">
                <i class="fas fa-play"></i>
            </button>` : `
            <button class="btn btn-secondary text-xs opacity-50 cursor-not-allowed" disabled title="Start">
                <i class="fas fa-play"></i>
            </button>`}
            
            ${isOnline ? `
            <button onclick="stopInstance(${instance.id})" 
                    class="btn btn-secondary text-xs" title="Stop">
                <i class="fas fa-stop"></i>
            </button>` : `
            <button class="btn btn-secondary text-xs opacity-50 cursor-not-allowed" disabled title="Stop">
                <i class="fas fa-stop"></i>
            </button>`}
            
            <button onclick="restartInstance(${instance.id})" 
                    class="btn btn-secondary text-xs" title="Restart">
                <i class="fas fa-redo"></i>
            </button>
        </div>
        
        <div class="grid grid-cols-3 gap-2 mb-2">
            <button onclick="toggleDevMode(${instance.id})" 
                    class="btn btn-secondary text-xs w-full ${isDev ? 'bg-gray-100' : ''} ${!isStopped ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${!isStopped ? 'disabled' : ''}>
                <i class="fas fa-bug mr-1"></i> DEV
            </button>
            <button onclick="viewLogs(${instance.id})" 
                    class="btn btn-secondary text-xs w-full">
                <i class="fas fa-file-alt mr-1"></i> LOGS
            </button>
            <button onclick="openVersionManager(${instance.id}, '${instance.name}', '${instance.version}')" 
                    class="btn btn-secondary text-xs w-full ${!isStopped ? 'opacity-50 cursor-not-allowed' : ''}"
                    ${!isStopped ? 'disabled' : ''}>
                <i class="fas fa-code-branch mr-1"></i> VER
            </button>
        </div>
        
        <div class="grid grid-cols-2 gap-2">
            <button onclick="openFileManager(${instance.id})" 
                    class="btn btn-secondary text-xs w-full">
                <i class="fas fa-folder mr-1"></i> FILES
            </button>
            <button onclick="openAdminManager(${instance.id})" 
                    class="btn btn-secondary text-xs w-full">
                <i class="fas fa-user-shield mr-1"></i> ADMIN
            </button>
        </div>
        
        <div class="mt-2">
             <button onclick="deleteInstance(${instance.id})" 
                    class="btn btn-danger text-xs w-full">
                <i class="fas fa-trash mr-1"></i> DELETE
            </button>
        </div>
    </div>
    `;
}

function renderEmptyState() {
    return `
    <div class="col-span-full card p-12 text-center border-dashed">
        <i class="fas fa-cube text-6xl mb-6"></i>
        <h3 class="text-2xl font-bold mb-2">NO INSTANCES</h3>
        <p class="text-gray-600 mb-6 font-mono">Create your first PocketBase instance to get started</p>
        <button onclick="openCreateModal()" class="btn btn-primary inline-flex">
            <i class="fas fa-plus mr-2"></i>
            CREATE INSTANCE
        </button>
    </div>
    `;
}

// Create instance
document.getElementById('createForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name'),
        version: formData.get('version'),
        dev_mode: formData.get('dev_mode') === 'on',
        port: formData.get('port') || null,
        admin_email: formData.get('admin_email') || null,
        admin_password: formData.get('admin_password') || null,
        domain: formData.get('domain') || null
    };

    const submitBtn = e.target.querySelector('button[type="submit"]');
    let originalHtml = '';
    if (submitBtn) {
        originalHtml = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>CREATING...';
    }
    
    try {
        const response = await fetch('/api/instances', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Instance created successfully!', 'success');
            closeCreateModal();
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to create instance', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            submitBtn.innerHTML = originalHtml || 'CREATE';
        }
    }
});

// Start instance
async function startInstance(id) {
    try {
        showNotification('Starting instance...', 'info');
        const response = await fetch(`/api/instances/${id}/start`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('Instance started!', 'success');
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to start instance', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Stop instance
async function stopInstance(id) {
    try {
        showNotification('Stopping instance...', 'info');
        const response = await fetch(`/api/instances/${id}/stop`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('Instance stopped!', 'success');
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to stop instance', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Restart instance
async function restartInstance(id) {
    try {
        showNotification('Restarting instance...', 'info');
        const response = await fetch(`/api/instances/${id}/restart`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('Instance restarted!', 'success');
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to restart instance', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Delete instance
async function deleteInstance(id) {
    if (!confirm(`Are you sure you want to delete this instance? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/instances/${id}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification('Instance deleted!', 'success');
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to delete instance', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Toggle dev mode
async function toggleDevMode(id) {
    try {
        const response = await fetch(`/api/instances/${id}/dev`, {
            method: 'POST'
        });
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            refreshInstances();
        } else {
            showNotification(result.error || 'Failed to toggle dev mode', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// View logs
async function viewLogs(id) {
    currentLogsInstanceId = id;
    const modal = document.getElementById('logsModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    await loadLogs();
}

async function loadLogs() {
    if (!currentLogsInstanceId) return;
    
    try {
        const response = await fetch(`/api/instances/${currentLogsInstanceId}/logs?lines=200`);
        const result = await response.json();
        
        if (result.success) {
            const logsContent = document.getElementById('logsContent');
            // Preserve scroll position if at bottom
            const isAtBottom = logsContent.scrollHeight - logsContent.scrollTop === logsContent.clientHeight;
            
            logsContent.textContent = result.logs || 'No logs available';
            
            if (isAtBottom) {
                logsContent.scrollTop = logsContent.scrollHeight;
            }
        } else {
            document.getElementById('logsContent').textContent = 'Error loading logs: ' + result.error;
        }
    } catch (error) {
        document.getElementById('logsContent').textContent = 'Network error: ' + error.message;
    }
}

function refreshLogs() {
    loadLogs();
}

// Refresh instances status
async function refreshInstances() {
    try {
        const response = await fetch('/api/instances');
        const result = await response.json();
        
        if (result.success) {
            const container = document.getElementById('instancesContainer');
            
            if (result.instances.length === 0) {
                if (!container.querySelector('.border-dashed')) {
                     container.innerHTML = renderEmptyState();
                }
                return;
            }
            
            const existingCards = new Map();
            document.querySelectorAll('[id^="instance-card-"]').forEach(el => {
                const id = el.id.replace('instance-card-', '');
                existingCards.set(parseInt(id), el);
            });
            
            const newInstanceIds = new Set(result.instances.map(i => i.id));
            
            // Remove deleted instances
            existingCards.forEach((el, id) => {
                if (!newInstanceIds.has(id)) {
                    el.remove();
                }
            });
            
            // Add or Update instances
            result.instances.forEach(instance => {
                const existingCard = existingCards.get(instance.id);
                const newCardHTML = renderInstanceCard(instance);
                
                if (existingCard) {
                    // Update logic: check if HTML changed
                    // Creating a temp element to compare
                    // Simple comparison after normalization
                    const normOld = existingCard.outerHTML.replace(/\s+/g, ' ').trim();
                    const normNew = newCardHTML.replace(/\s+/g, ' ').trim();
                    
                    if (normOld !== normNew) {
                         existingCard.outerHTML = newCardHTML;
                    }
                } else {
                    // New instance
                    // If we had "No instances" message, clear it
                    if (container.querySelector('.border-dashed')) {
                        container.innerHTML = '';
                    }
                    // Append to container
                    container.insertAdjacentHTML('beforeend', newCardHTML);
                }
            });
            
            // Double check empty state
            if (result.instances.length === 0 && container.innerHTML.trim() === '') {
                 container.innerHTML = renderEmptyState();
            }
            
        }
    } catch (error) {
        console.error('Failed to refresh instances:', error);
    }
}

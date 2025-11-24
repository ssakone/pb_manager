// Version Manager for PocketBase Instances

let currentVersionInstanceId = null;
let currentVersionInstanceName = '';
let currentVersionCurrent = '';

// Open version manager
async function openVersionManager(instanceId, instanceName, currentVersion) {
    currentVersionInstanceId = instanceId;
    currentVersionInstanceName = instanceName;
    currentVersionCurrent = currentVersion;
    
    const modal = document.getElementById('versionManagerModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    // Update modal title
    document.getElementById('versionModalTitle').textContent = `Changer Version - ${instanceName}`;
    document.getElementById('versionCurrent').textContent = `v${currentVersion}`;
    
    await loadVersions();
}

// Close version manager
function closeVersionManager() {
    const modal = document.getElementById('versionManagerModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentVersionInstanceId = null;
    currentVersionInstanceName = '';
    currentVersionCurrent = '';
}

// Load available versions
async function loadVersions() {
    try {
        const response = await fetch('/api/versions');
        const result = await response.json();
        
        if (result.success) {
            renderVersionList(result.versions);
        } else {
            showNotification('Erreur lors du chargement des versions: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Erreur réseau: ' + error.message, 'error');
    }
}

// Render version list
function renderVersionList(versions) {
    const container = document.getElementById('versionList');
    
    if (versions.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-gray-500">
                <i class="fas fa-code-branch text-6xl mb-4"></i>
                <p class="font-mono">Aucune version disponible</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = versions.map(version => {
        const isCurrent = version.version === currentVersionCurrent;
        const publishedDate = new Date(version.published_at).toLocaleDateString('fr-FR');
        
        return `
            <div class="border-2 border-black p-4 hover:bg-gray-50 transition-colors ${isCurrent ? 'bg-gray-100' : ''}">
                <div class="flex justify-between items-center">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <i class="fas fa-code-branch"></i>
                            <span class="font-bold font-mono">v${version.version}</span>
                            ${isCurrent ? '<span class="text-xs bg-green-600 text-white px-2 py-1 ml-2 font-bold">VERSION ACTUELLE</span>' : ''}
                        </div>
                        <div class="text-sm text-gray-600">
                            <div class="font-mono">${version.name}</div>
                            <div class="text-xs mt-1">Publié: ${publishedDate}</div>
                        </div>
                    </div>
                    ${!isCurrent ? `
                    <button onclick="changeVersion('${version.version}')" 
                            class="btn btn-primary text-xs">
                        <i class="fas fa-download mr-1"></i> INSTALLER
                    </button>
                    ` : `
                    <button class="btn btn-secondary text-xs opacity-50 cursor-not-allowed" disabled>
                        INSTALLÉE
                    </button>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

// Change version
async function changeVersion(newVersion) {
    const message = `Êtes-vous sûr de vouloir changer la version de "${currentVersionInstanceName}" vers v${newVersion}?\n\nL'instance doit être arrêtée. Un backup de l'ancienne version sera créé.`;
    
    if (!confirm(message)) return;
    
    try {
        showNotification(`Changement de version vers v${newVersion}...`, 'info');
        
        const response = await fetch(`/api/instances/${currentVersionInstanceId}/version`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ version: newVersion })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            closeVersionManager();
            refreshInstances();
        } else {
            showNotification('Erreur: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Erreur réseau: ' + error.message, 'error');
    }
}

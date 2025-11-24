// File Manager for PocketBase Instances

let currentInstanceId = null;
let currentPath = '';
let selectedItems = new Set();
let clipboardItem = null;
let clipboardOperation = null; // 'copy' or 'cut'

// Open file manager
function openFileManager(instanceId) {
    currentInstanceId = instanceId;
    currentPath = '';
    selectedItems.clear();
    clipboardItem = null;
    clipboardOperation = null;
    
    const modal = document.getElementById('fileManagerModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    loadFiles();
}

// Close file manager
function closeFileManager() {
    const modal = document.getElementById('fileManagerModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentInstanceId = null;
    currentPath = '';
    selectedItems.clear();
}

// Load files for current path
async function loadFiles() {
    if (!currentInstanceId) return;
    
    try {
        const pathParam = currentPath ? `?path=${encodeURIComponent(currentPath)}` : '';
        const response = await fetch(`/api/instances/${currentInstanceId}/files${pathParam}`);
        const result = await response.json();
        
        if (result.success) {
            renderFileList(result.items, result.current_path);
            updateBreadcrumb(result.current_path);
            updateToolbar();
        } else {
            showNotification('Error loading files: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Render file list
function renderFileList(items, currentPathStr) {
    const container = document.getElementById('fileList');
    
    if (items.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12 text-gray-500">
                <i class="fas fa-folder-open text-6xl mb-4"></i>
                <p class="font-mono">Empty folder</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = items.map(item => {
        const icon = getFileIcon(item);
        const isSelected = selectedItems.has(item.path);
        const sizeStr = item.type === 'file' ? formatFileSize(item.size) : '-';
        const modifiedStr = new Date(item.modified).toLocaleString();
        const protectedBadge = item.protected ? '<span class="text-xs bg-yellow-400 text-black px-1 ml-2 font-bold">PROTECTED</span>' : '';
        
        return `
            <div class="file-item ${isSelected ? 'selected' : ''} ${item.type}" 
                 data-path="${item.path}" 
                 data-type="${item.type}"
                 data-name="${item.name}">
                <div class="flex items-center gap-3 flex-1 min-w-0">
                    <input type="checkbox" 
                           class="file-checkbox border-2 border-black rounded-none" 
                           ${isSelected ? 'checked' : ''}
                           onclick="toggleSelection('${item.path}', event)">
                    <i class="${icon} text-xl flex-shrink-0"></i>
                    <span class="font-mono font-medium truncate flex-1" ondblclick="handleItemDoubleClick('${item.path}', '${item.type}')">
                        ${item.name}${protectedBadge}
                    </span>
                </div>
                <div class="flex items-center gap-6 text-sm font-mono text-gray-600">
                    <span class="w-24 text-right">${sizeStr}</span>
                    <span class="w-40 text-right hidden md:block">${modifiedStr}</span>
                    <div class="flex gap-1">
                        ${item.type === 'file' ? `
                            <button onclick="downloadFile('${item.path}')" 
                                    class="btn-icon" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                        ` : ''}
                        <button onclick="deleteItem('${item.path}', '${item.name}', ${item.protected})" 
                                class="btn-icon text-red-600" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Get file icon based on type
function getFileIcon(item) {
    if (item.type === 'directory') {
        return 'fas fa-folder text-yellow-600';
    }
    
    const ext = item.extension || '';
    const iconMap = {
        '.js': 'fab fa-js-square text-yellow-500',
        '.json': 'fas fa-file-code text-yellow-600',
        '.py': 'fab fa-python text-blue-500',
        '.html': 'fab fa-html5 text-orange-600',
        '.css': 'fab fa-css3-alt text-blue-600',
        '.md': 'fab fa-markdown text-gray-700',
        '.txt': 'fas fa-file-alt text-gray-600',
        '.pdf': 'fas fa-file-pdf text-red-600',
        '.zip': 'fas fa-file-archive text-gray-700',
        '.tar': 'fas fa-file-archive text-gray-700',
        '.gz': 'fas fa-file-archive text-gray-700',
        '.png': 'fas fa-file-image text-purple-600',
        '.jpg': 'fas fa-file-image text-purple-600',
        '.jpeg': 'fas fa-file-image text-purple-600',
        '.gif': 'fas fa-file-image text-purple-600',
        '.svg': 'fas fa-file-image text-purple-600',
        '.db': 'fas fa-database text-green-600',
    };
    
    return iconMap[ext] || 'fas fa-file text-gray-500';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Update breadcrumb navigation
function updateBreadcrumb(path) {
    const breadcrumb = document.getElementById('breadcrumb');
    const parts = path ? path.split('/').filter(p => p) : [];
    
    let html = `<button onclick="navigateToPath('')" class="breadcrumb-item"><i class="fas fa-home"></i></button>`;
    
    let currentFullPath = '';
    parts.forEach((part, index) => {
        currentFullPath += (currentFullPath ? '/' : '') + part;
        const isLast = index === parts.length - 1;
        html += `
            <span class="mx-2">/</span>
            <button onclick="navigateToPath('${currentFullPath}')" 
                    class="breadcrumb-item ${isLast ? 'font-bold' : ''}">
                ${part}
            </button>
        `;
    });
    
    breadcrumb.innerHTML = html;
}

// Navigate to path
function navigateToPath(path) {
    currentPath = path;
    selectedItems.clear();
    loadFiles();
}

// Handle double-click on item
function handleItemDoubleClick(path, type) {
    if (type === 'directory') {
        navigateToPath(path);
    } else {
        downloadFile(path);
    }
}

// Toggle item selection
function toggleSelection(path, event) {
    event.stopPropagation();
    
    if (selectedItems.has(path)) {
        selectedItems.delete(path);
    } else {
        selectedItems.add(path);
    }
    
    updateToolbar();
    
    // Update visual state
    const item = document.querySelector(`[data-path="${path}"]`);
    if (item) {
        item.classList.toggle('selected');
    }
}

// Update toolbar based on selection
function updateToolbar() {
    const count = selectedItems.size;
    const deleteBtn = document.getElementById('deleteSelectedBtn');
    
    if (deleteBtn) {
        deleteBtn.disabled = count === 0;
        deleteBtn.textContent = count > 0 ? `DELETE (${count})` : 'DELETE';
    }
}

// Upload files
function openUploadDialog() {
    document.getElementById('fileInput').click();
}

async function handleFileUpload(event) {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;
    
    await uploadFiles(files);
    event.target.value = ''; // Reset input
}

async function uploadFiles(files) {
    const formData = new FormData();
    formData.append('path', currentPath);
    formData.append('replace', 'true');
    
    files.forEach(file => {
        formData.append('files', file);
    });
    
    try {
        showNotification(`Uploading ${files.length} file(s)...`, 'info');
        
        const response = await fetch(`/api/instances/${currentInstanceId}/files/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadFiles();
        } else {
            showNotification('Upload failed: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Drag and drop handlers
function setupDragAndDrop() {
    const dropZone = document.getElementById('fileManagerContent');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });
    
    dropZone.addEventListener('drop', handleDrop);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = Array.from(dt.files);
    
    if (files.length > 0) {
        uploadFiles(files);
    }
}

// Create new folder
function openNewFolderDialog() {
    const name = prompt('Enter folder name:');
    if (!name) return;
    
    createFolder(name);
}

async function createFolder(name) {
    try {
        const response = await fetch(`/api/instances/${currentInstanceId}/files/mkdir`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                path: currentPath,
                name: name
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadFiles();
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Download file
function downloadFile(path) {
    window.open(`/api/instances/${currentInstanceId}/files/download?path=${encodeURIComponent(path)}`, '_blank');
}

// Delete item
async function deleteItem(path, name, isProtected) {
    const warning = isProtected ? '\n\n⚠️ WARNING: This is a protected file!' : '';
    const message = `Are you sure you want to delete "${name}"?${warning}\n\nThis action cannot be undone.`;
    
    if (!confirm(message)) return;
    
    try {
        const response = await fetch(`/api/instances/${currentInstanceId}/files/delete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ path: path })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            selectedItems.delete(path);
            loadFiles();
        } else {
            showNotification('Error: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

// Delete selected items
async function deleteSelected() {
    if (selectedItems.size === 0) return;
    
    const message = `Are you sure you want to delete ${selectedItems.size} item(s)?\n\nThis action cannot be undone.`;
    
    if (!confirm(message)) return;
    
    const itemsToDelete = Array.from(selectedItems);
    let successCount = 0;
    
    try {
        for (const path of itemsToDelete) {
            const response = await fetch(`/api/instances/${currentInstanceId}/files/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ path: path })
            });
            
            const result = await response.json();
            if (result.success) {
                successCount++;
                selectedItems.delete(path);
            }
        }
        
        showNotification(`Deleted ${successCount} of ${itemsToDelete.length} item(s)`, 'success');
        loadFiles();
    } catch (error) {
        showNotification('Error during deletion: ' + error.message, 'error');
    }
}

// Refresh file list
function refreshFiles() {
    loadFiles();
    showNotification('Refreshed', 'info');
}

// Initialize when modal opens
document.addEventListener('DOMContentLoaded', () => {
    setupDragAndDrop();
});

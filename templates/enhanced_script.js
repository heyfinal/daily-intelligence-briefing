/**
 * Enhanced AI Intelligence Briefing System - JavaScript
 * Handles all interactive features and API communication
 */

// Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api';
const POLLING_INTERVAL = 5000; // 5 seconds
const API_STATUS_INTERVAL = 30000; // 30 seconds

// Global state
let selectedItems = new Set();
let currentBatchId = null;
let pollTimer = null;
let apiStatusTimer = null;

// API Communication
class APIClient {
    static async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint);
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// API Status Management
async function checkAPIStatus() {
    const statusBtn = document.getElementById('api-status');
    if (!statusBtn) return;

    try {
        await APIClient.get('/health');
        statusBtn.classList.remove('unhealthy');
        statusBtn.classList.add('healthy');
        statusBtn.innerHTML = '<i class="fas fa-circle"></i> API Healthy';
    } catch (error) {
        statusBtn.classList.remove('healthy');
        statusBtn.classList.add('unhealthy');
        statusBtn.innerHTML = '<i class="fas fa-circle"></i> API Offline';
    }
}

// Projects Management
async function loadProjects() {
    const loadingEl = document.getElementById('projects-loading');
    const summaryEl = document.getElementById('projects-summary');
    const listEl = document.getElementById('projects-list');
    const errorEl = document.getElementById('projects-error');
    const countEl = document.getElementById('projects-count');

    // Show loading state
    loadingEl.style.display = 'block';
    summaryEl.style.display = 'none';
    listEl.style.display = 'none';
    errorEl.style.display = 'none';

    try {
        const response = await APIClient.get('/projects');
        const { projects, summary } = response;

        // Update header count
        if (countEl) {
            countEl.textContent = `${projects.length} Projects Scanned`;
        }

        // Update summary cards
        if (summary) {
            updateProjectsSummary(summary);
        }

        // Render projects list
        renderProjectsList(projects);

        // Show content
        loadingEl.style.display = 'none';
        summaryEl.style.display = 'block';
        listEl.style.display = 'block';

    } catch (error) {
        console.error('Failed to load projects:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
        
        if (countEl) {
            countEl.textContent = 'Projects: Error';
        }
    }
}

function updateProjectsSummary(summary) {
    document.getElementById('total-projects').textContent = summary.total_projects || 0;
    document.getElementById('avg-health').textContent = `${summary.average_health_score || 0}/100`;
    document.getElementById('needs-attention').textContent = summary.needs_attention || 0;
    document.getElementById('git-repos').textContent = summary.git_repos || 0;
}

function renderProjectsList(projects) {
    const listEl = document.getElementById('projects-list');
    
    if (!projects || projects.length === 0) {
        listEl.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>No Projects Found</h3>
                <p>No Claude Code projects were found in the scanned directories.</p>
            </div>
        `;
        return;
    }

    listEl.innerHTML = projects.map(project => `
        <div class="project-card ${getHealthClass(project.health_score)} fade-in">
            <div class="project-header">
                <h4 class="project-name">${escapeHtml(project.name)}</h4>
                <span class="project-type">${escapeHtml(project.type)}</span>
            </div>
            
            <div class="project-health">
                <div class="health-score ${getHealthClass(project.health_score)}">${project.health_score}</div>
                <div class="health-label">Health Score</div>
            </div>
            
            <div class="project-details">
                <div class="project-detail">
                    <div class="detail-number">${project.dependencies?.total_count || 0}</div>
                    <div class="detail-label">Dependencies</div>
                </div>
                <div class="project-detail">
                    <div class="detail-number">${project.todos?.length || 0}</div>
                    <div class="detail-label">TODOs</div>
                </div>
                <div class="project-detail">
                    <div class="detail-number">${project.size_mb || 0}MB</div>
                    <div class="detail-label">Size</div>
                </div>
                <div class="project-detail">
                    <div class="detail-number">${project.git_info?.is_repo ? 'Yes' : 'No'}</div>
                    <div class="detail-label">Git Repo</div>
                </div>
            </div>
            
            ${project.git_info?.uncommitted_changes ? `
                <div class="git-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    Uncommitted changes detected
                </div>
            ` : ''}
            
            <div class="project-recommendations">
                <h5>Recommendations (${project.recommendations?.length || 0})</h5>
                ${renderRecommendations(project.recommendations || [])}
            </div>
        </div>
    `).join('');
}

function renderRecommendations(recommendations) {
    if (!recommendations.length) {
        return '<p class="text-muted">No recommendations at this time.</p>';
    }

    return recommendations.slice(0, 3).map(rec => `
        <div class="recommendation-item ${rec.priority}">
            <div class="recommendation-title">${escapeHtml(rec.title)}</div>
            <div class="recommendation-description">${escapeHtml(rec.description)}</div>
            ${rec.action ? `<div class="recommendation-action"><code>${escapeHtml(rec.action)}</code></div>` : ''}
        </div>
    `).join('');
}

function getHealthClass(score) {
    if (score >= 80) return 'high-health';
    if (score >= 60) return 'medium-health';
    return 'low-health';
}

async function refreshProjects() {
    await loadProjects();
}

async function scanDeeper() {
    // Show loading with different message
    const loadingEl = document.getElementById('projects-loading');
    loadingEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deep scanning projects (this may take longer)...';
    
    try {
        const response = await APIClient.get('/projects?depth=6');
        const { projects, summary } = response;

        updateProjectsSummary(summary);
        renderProjectsList(projects);

        // Reset loading message
        loadingEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning local projects...';
        
    } catch (error) {
        console.error('Deep scan failed:', error);
        loadingEl.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning local projects...';
    }
}

// Installation Management
async function loadInstallableItems() {
    const loadingEl = document.getElementById('installable-items-loading');
    const categoriesEl = document.getElementById('installable-categories');
    const errorEl = document.getElementById('installable-items-error');

    loadingEl.style.display = 'block';
    categoriesEl.style.display = 'none';
    errorEl.style.display = 'none';

    try {
        const response = await APIClient.get('/installable-items');
        const { items, categories } = response;

        // Update tab counts
        updateInstallationTabCounts(items.length, 0, 0);

        // Render categories
        renderInstallableCategories(categories);

        loadingEl.style.display = 'none';
        categoriesEl.style.display = 'block';

    } catch (error) {
        console.error('Failed to load installable items:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
    }
}

function renderInstallableCategories(categories) {
    const categoriesEl = document.getElementById('installable-categories');
    
    const categoryOrder = ['mcp_servers', 'cli_tools', 'dev_tools', 'python_packages', 'nodejs_packages', 'homebrew_formulae', 'other'];
    const categoryIcons = {
        'mcp_servers': 'fas fa-plug',
        'cli_tools': 'fas fa-terminal',
        'dev_tools': 'fas fa-wrench',
        'python_packages': 'fab fa-python',
        'nodejs_packages': 'fab fa-node-js',
        'homebrew_formulae': 'fas fa-beer',
        'rust_crates': 'fab fa-rust',
        'go_modules': 'fab fa-golang',
        'other': 'fas fa-cube'
    };
    
    const categoryNames = {
        'mcp_servers': 'MCP Servers',
        'cli_tools': 'CLI Tools',
        'dev_tools': 'Development Tools',
        'python_packages': 'Python Packages',
        'nodejs_packages': 'Node.js Packages',
        'homebrew_formulae': 'Homebrew Formulae',
        'rust_crates': 'Rust Crates',
        'go_modules': 'Go Modules',
        'other': 'Other'
    };

    const sortedCategories = categoryOrder.filter(cat => categories[cat] && categories[cat].length > 0);
    
    categoriesEl.innerHTML = sortedCategories.map(categoryKey => {
        const items = categories[categoryKey];
        const iconClass = categoryIcons[categoryKey] || 'fas fa-cube';
        const categoryName = categoryNames[categoryKey] || categoryKey;
        
        return `
            <div class="category-section">
                <div class="category-header">
                    <h4 class="category-title">
                        <i class="${iconClass}"></i>
                        ${categoryName}
                    </h4>
                    <span class="category-count">${items.length}</span>
                </div>
                <div class="installable-items">
                    ${items.map(item => renderInstallableItem(item)).join('')}
                </div>
            </div>
        `;
    }).join('');

    // Add event listeners to checkboxes
    attachInstallableItemListeners();
}

function renderInstallableItem(item) {
    return `
        <div class="installable-item" data-item-id="${item.id}">
            <div class="item-header">
                <div class="item-content">
                    <div class="item-name">${escapeHtml(item.name)}</div>
                    <div class="item-description">${escapeHtml(item.description)}</div>
                    <div class="item-meta">
                        <span class="item-manager">${escapeHtml(item.package_manager)}</span>
                        ${item.version ? `<span>v${escapeHtml(item.version)}</span>` : ''}
                        ${item.estimated_size_mb ? `<span>${item.estimated_size_mb}MB</span>` : ''}
                    </div>
                </div>
                <input type="checkbox" class="item-checkbox" data-item='${JSON.stringify(item).replace(/'/g, "&#39;")}'>
            </div>
        </div>
    `;
}

function attachInstallableItemListeners() {
    document.querySelectorAll('.item-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const itemData = JSON.parse(this.dataset.item);
            const itemEl = this.closest('.installable-item');
            
            if (this.checked) {
                selectedItems.add(itemData.id);
                itemEl.classList.add('selected');
            } else {
                selectedItems.delete(itemData.id);
                itemEl.classList.remove('selected');
            }
            
            updateSelectedCount();
        });
    });
}

function updateSelectedCount() {
    const countEl = document.getElementById('selected-count');
    const installBtn = document.getElementById('install-selected-btn');
    
    countEl.textContent = `${selectedItems.size} selected`;
    installBtn.disabled = selectedItems.size === 0;
}

function selectAll() {
    document.querySelectorAll('.item-checkbox').forEach(checkbox => {
        if (!checkbox.checked) {
            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change'));
        }
    });
}

function selectNone() {
    document.querySelectorAll('.item-checkbox:checked').forEach(checkbox => {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event('change'));
    });
}

function selectByCategory() {
    // Simple implementation - could be enhanced with a modal
    const category = prompt('Enter category name (e.g., cli_tools, mcp_servers):');
    if (!category) return;
    
    document.querySelectorAll('.category-section').forEach(section => {
        const title = section.querySelector('.category-title').textContent.toLowerCase();
        if (title.includes(category.toLowerCase())) {
            section.querySelectorAll('.item-checkbox').forEach(checkbox => {
                if (!checkbox.checked) {
                    checkbox.checked = true;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        }
    });
}

async function installSelected() {
    if (selectedItems.size === 0) return;
    
    const installBtn = document.getElementById('install-selected-btn');
    installBtn.disabled = true;
    installBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Installing...';
    
    try {
        // Collect selected item data
        const selectedItemsData = [];
        document.querySelectorAll('.item-checkbox:checked').forEach(checkbox => {
            selectedItemsData.push(JSON.parse(checkbox.dataset.item));
        });
        
        // Send installation request
        const response = await APIClient.post('/install', { items: selectedItemsData });
        
        if (response.batch_id) {
            currentBatchId = response.batch_id;
            showNotification('Installation queued successfully!', 'success');
            
            // Switch to queue tab
            showInstallationTab('queue');
            
            // Start monitoring progress
            startProgressMonitoring();
        }
        
    } catch (error) {
        console.error('Installation failed:', error);
        showNotification('Installation failed: ' + error.message, 'error');
    } finally {
        installBtn.disabled = false;
        installBtn.innerHTML = '<i class="fas fa-download"></i> Install Selected';
    }
}

function startProgressMonitoring() {
    if (pollTimer) {
        clearInterval(pollTimer);
    }
    
    pollTimer = setInterval(async () => {
        await refreshInstallationProgress();
    }, POLLING_INTERVAL);
    
    // Initial load
    refreshInstallationProgress();
}

async function refreshInstallationProgress() {
    if (!currentBatchId) return;
    
    try {
        const progress = await APIClient.get(`/installation-progress/${currentBatchId}`);
        
        updateInstallationQueue(progress.active);
        updateInstallationCompleted(progress.completed);
        updateInstallationFailed(progress.failed);
        
        // Update tab counts
        updateInstallationTabCounts(
            selectedItems.size,
            Object.keys(progress.active).length,
            Object.keys(progress.completed).length + Object.keys(progress.failed).length
        );
        
        // Stop polling if nothing is active
        if (Object.keys(progress.active).length === 0 && pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
        
    } catch (error) {
        console.error('Failed to refresh installation progress:', error);
    }
}

function updateInstallationQueue(activeItems) {
    const queueEl = document.getElementById('installation-queue');
    
    if (Object.keys(activeItems).length === 0) {
        queueEl.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clock"></i>
                <h3>No installations in queue</h3>
                <p>Select items from the Available tab to start installing.</p>
            </div>
        `;
        return;
    }
    
    queueEl.innerHTML = Object.values(activeItems).map(installation => `
        <div class="progress-item">
            <div class="progress-header">
                <span class="progress-name">${escapeHtml(installation.item.name)}</span>
                <span class="progress-status installing">Installing</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 50%"></div>
            </div>
            <div class="progress-details">
                Started: ${new Date(installation.start_time).toLocaleTimeString()}
            </div>
        </div>
    `).join('');
}

function updateInstallationCompleted(completedItems) {
    const completedEl = document.getElementById('installation-completed');
    
    if (Object.keys(completedItems).length === 0) {
        completedEl.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <h3>No completed installations</h3>
                <p>Completed installations will appear here.</p>
            </div>
        `;
        return;
    }
    
    completedEl.innerHTML = Object.values(completedItems).map(installation => `
        <div class="progress-item">
            <div class="progress-header">
                <span class="progress-name">${escapeHtml(installation.item.name)}</span>
                <span class="progress-status ${installation.result.success ? 'completed' : 'failed'}">
                    ${installation.result.success ? 'Completed' : 'Failed'}
                </span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 100%"></div>
            </div>
            <div class="progress-details">
                Duration: ${installation.result.duration_seconds}s
                ${installation.result.installed_version ? ` | Version: ${installation.result.installed_version}` : ''}
                ${installation.result.error ? ` | Error: ${installation.result.error}` : ''}
            </div>
        </div>
    `).join('');
}

function updateInstallationTabCounts(available, queue, completed) {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs[0].innerHTML = `<i class="fas fa-package"></i> Available (${available})`;
    tabs[1].innerHTML = `<i class="fas fa-clock"></i> Queue (${queue})`;
    tabs[2].innerHTML = `<i class="fas fa-check-circle"></i> Completed (${completed})`;
}

function showInstallationTab(tabName) {
    // Remove active from all tabs and content
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active to selected tab and content
    document.querySelector(`[onclick="showInstallationTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

async function refreshInstallableItems() {
    await loadInstallableItems();
}

async function viewInstallationHistory() {
    try {
        const response = await APIClient.get('/installation-history');
        
        // Simple alert for now - could be enhanced with a modal
        const recentInstalls = response.history.slice(0, 10);
        const summary = recentInstalls.map(install => 
            `${install.package_name} (${install.success ? 'Success' : 'Failed'})`
        ).join('\n');
        
        alert('Recent Installations:\n\n' + summary);
        
    } catch (error) {
        console.error('Failed to load installation history:', error);
        showNotification('Failed to load installation history', 'error');
    }
}

// System Health Management
async function loadSystemHealth() {
    const loadingEl = document.getElementById('system-health-loading');
    const contentEl = document.getElementById('system-health-content');
    const errorEl = document.getElementById('system-health-error');

    loadingEl.style.display = 'block';
    contentEl.style.display = 'none';
    errorEl.style.display = 'none';

    try {
        const health = await APIClient.get('/system-health');

        // Update health status
        updateHealthStatus(health);
        
        // Update metrics
        updateHealthMetrics(health);
        
        // Update recommendations
        updateSystemRecommendations(health.recommendations || []);

        loadingEl.style.display = 'none';
        contentEl.style.display = 'block';

    } catch (error) {
        console.error('Failed to load system health:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
    }
}

function updateHealthStatus(health) {
    const statusEl = document.getElementById('overall-health-status');
    const uptimeEl = document.getElementById('system-uptime');
    
    if (statusEl) {
        statusEl.className = `health-status ${health.overall_health}`;
        statusEl.innerHTML = `<i class="fas fa-circle"></i> <span>${health.overall_health.charAt(0).toUpperCase() + health.overall_health.slice(1)}</span>`;
    }
    
    if (uptimeEl) {
        uptimeEl.textContent = `${health.uptime_hours}h`;
    }
}

function updateHealthMetrics(health) {
    document.getElementById('recent-updates').textContent = health.recent_updates || 0;
    document.getElementById('cache-hit-rate').textContent = `${Math.round(health.cache_hit_rate || 0)}%`;
    document.getElementById('install-success-rate').textContent = `${Math.round(health.installation_success_rate || 0)}%`;
    document.getElementById('disk-usage').textContent = `${health.disk_usage_mb || 0} MB`;
}

function updateSystemRecommendations(recommendations) {
    const listEl = document.getElementById('system-recommendations-list');
    
    if (!recommendations.length) {
        listEl.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-check-circle"></i>
                <h3>All Good!</h3>
                <p>No system recommendations at this time.</p>
            </div>
        `;
        return;
    }
    
    listEl.innerHTML = recommendations.map(rec => `
        <div class="recommendation-card ${rec.priority}">
            <div class="rec-header">
                <span class="rec-title">${escapeHtml(rec.title)}</span>
                <span class="rec-priority ${rec.priority}">${rec.priority}</span>
            </div>
            <div class="rec-description">${escapeHtml(rec.description)}</div>
            ${rec.action ? `<div class="rec-action">${escapeHtml(rec.action)}</div>` : ''}
        </div>
    `).join('');
}

async function refreshSystemHealth() {
    await loadSystemHealth();
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Simple notification system - could be enhanced
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.5rem;
        box-shadow: 0 4px 20px var(--shadow);
        z-index: 1000;
        color: var(--text-color);
    `;
    
    if (type === 'success') {
        notification.style.borderColor = 'var(--success)';
        notification.style.color = 'var(--success)';
    } else if (type === 'error') {
        notification.style.borderColor = 'var(--error)';
        notification.style.color = 'var(--error)';
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Initialize periodic tasks
function startPeriodicTasks() {
    // Check API status periodically
    if (apiStatusTimer) {
        clearInterval(apiStatusTimer);
    }
    apiStatusTimer = setInterval(checkAPIStatus, API_STATUS_INTERVAL);
}

// Cleanup function
function cleanup() {
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
    if (apiStatusTimer) {
        clearInterval(apiStatusTimer);
        apiStatusTimer = null;
    }
}

// Event listeners
window.addEventListener('beforeunload', cleanup);
window.addEventListener('unload', cleanup);

// Make functions available globally
window.loadProjects = loadProjects;
window.refreshProjects = refreshProjects;
window.scanDeeper = scanDeeper;
window.loadInstallableItems = loadInstallableItems;
window.refreshInstallableItems = refreshInstallableItems;
window.viewInstallationHistory = viewInstallationHistory;
window.selectAll = selectAll;
window.selectNone = selectNone;
window.selectByCategory = selectByCategory;
window.installSelected = installSelected;
window.showInstallationTab = showInstallationTab;
window.loadSystemHealth = loadSystemHealth;
window.refreshSystemHealth = refreshSystemHealth;
window.checkAPIStatus = checkAPIStatus;
window.startPeriodicTasks = startPeriodicTasks;

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startPeriodicTasks);
} else {
    startPeriodicTasks();
}
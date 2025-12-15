// Main application utilities

// Show notification toast
function showNotification(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        newContainer.className = 'toast-container';
        document.body.appendChild(newContainer);
        return showNotification(message, type);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const title = type === 'success' ? 'Success' : type === 'error' ? 'Error' : 'Info';
    
    toast.innerHTML = `
        <div class="toast-header">
            <span class="toast-title">${title}</span>
        </div>
        <div class="toast-message">${message}</div>
    `;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s reverse';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Show/hide loading overlay
function showLoading(show = true) {
    let overlay = document.getElementById('loading-overlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(overlay);
    }

    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Modal management
class Modal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.overlay = this.modal?.closest('.modal-overlay');
        
        if (this.overlay) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) {
                    this.close();
                }
            });
        }

        const closeBtn = this.modal?.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
    }

    open() {
        this.overlay?.classList.add('active');
    }

    close() {
        this.overlay?.classList.remove('active');
    }

    setTitle(title) {
        const titleEl = this.modal?.querySelector('.modal-title');
        if (titleEl) titleEl.textContent = title;
    }
}

// Form utilities
function getFormData(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        // Convert numeric strings to numbers
        if (!isNaN(value) && value !== '') {
            data[key] = Number(value);
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

function setFormData(formId, data) {
    const form = document.getElementById(formId);
    
    for (const [key, value] of Object.entries(data)) {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = value;
            } else {
                input.value = value;
            }
        }
    }
}

function clearForm(formId) {
    const form = document.getElementById(formId);
    form.reset();
}

function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('[required]');
    let isValid = true;

    inputs.forEach(input => {
        input.classList.remove('error');
        const errorEl = input.parentElement.querySelector('.form-error');
        if (errorEl) errorEl.remove();

        if (!input.value.trim()) {
            isValid = false;
            input.classList.add('error');
            const error = document.createElement('div');
            error.className = 'form-error';
            error.textContent = 'This field is required';
            input.parentElement.appendChild(error);
        }
    });

    return isValid;
}

// Table utilities
function createTable(data, columns, actions = []) {
    console.log('[createTable] Creating table with:', {
        rows: data.length,
        columns: columns.length,
        actions: actions.length
    });
    
    const table = document.createElement('table');
    
    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.label;
        if (col.sortable) {
            th.classList.add('sortable');
            th.dataset.key = col.key;
        }
        headerRow.appendChild(th);
    });
    
    if (actions.length > 0) {
        const th = document.createElement('th');
        th.textContent = 'Actions';
        headerRow.appendChild(th);
    }
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body
    const tbody = document.createElement('tbody');
    
    if (data.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = columns.length + (actions.length > 0 ? 1 : 0);
        cell.textContent = 'No data available';
        cell.style.textAlign = 'center';
        cell.style.color = 'var(--text-secondary)';
        row.appendChild(cell);
        tbody.appendChild(row);
    } else {
        data.forEach(item => {
            const row = document.createElement('tr');
            
            columns.forEach(col => {
                const cell = document.createElement('td');
                let value = item[col.key];
                
                if (col.format) {
                    value = col.format(value, item);
                }
                
                if (typeof value === 'boolean') {
                    value = value ? 'Yes' : 'No';
                }
                
                cell.innerHTML = value ?? '-';
                row.appendChild(cell);
            });
            
            if (actions.length > 0) {
                const cell = document.createElement('td');
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'table-actions';
                
                actions.forEach(action => {
                    const btn = document.createElement('button');
                    btn.className = `btn btn-sm ${action.className || 'btn-primary'}`;
                    btn.textContent = action.label;
                    btn.type = 'button'; // Prevent form submission
                    btn.onclick = (e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log(`[Table Action] ${action.label} clicked for item:`, item);
                        action.handler(item);
                    };
                    actionsDiv.appendChild(btn);
                });
                
                cell.appendChild(actionsDiv);
                row.appendChild(cell);
            }
            
            tbody.appendChild(row);
        });
    }
    
    table.appendChild(tbody);
    return table;
}

// Pagination
class Pagination {
    constructor(data, itemsPerPage = 10) {
        this.allData = data;
        this.itemsPerPage = itemsPerPage;
        this.currentPage = 1;
    }

    get totalPages() {
        return Math.ceil(this.allData.length / this.itemsPerPage);
    }

    get currentData() {
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        return this.allData.slice(start, end);
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            return true;
        }
        return false;
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            return true;
        }
        return false;
    }

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            return true;
        }
        return false;
    }

    renderControls(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="pagination">
                <button id="prev-page" ${this.currentPage === 1 ? 'disabled' : ''}>Previous</button>
                <span class="page-info">Page ${this.currentPage} of ${this.totalPages}</span>
                <button id="next-page" ${this.currentPage === this.totalPages ? 'disabled' : ''}>Next</button>
            </div>
        `;

        document.getElementById('prev-page')?.addEventListener('click', () => {
            if (this.prevPage()) {
                this.onPageChange && this.onPageChange();
            }
        });

        document.getElementById('next-page')?.addEventListener('click', () => {
            if (this.nextPage()) {
                this.onPageChange && this.onPageChange();
            }
        });
    }
}

// Search/Filter utilities
function filterData(data, searchTerm, keys) {
    if (!searchTerm) return data;
    
    const term = searchTerm.toLowerCase();
    return data.filter(item => {
        return keys.some(key => {
            const value = item[key];
            return value && value.toString().toLowerCase().includes(term);
        });
    });
}

// Sort utilities
function sortData(data, key, ascending = true) {
    return [...data].sort((a, b) => {
        const aVal = a[key];
        const bVal = b[key];
        
        if (aVal === bVal) return 0;
        
        const result = aVal < bVal ? -1 : 1;
        return ascending ? result : -result;
    });
}

// Confirmation dialog helper (renamed to avoid conflict with window.confirm)
function showConfirmDialog(message, onConfirm, onCancel) {
    if (window.confirm(message)) {
        onConfirm && onConfirm();
    } else {
        onCancel && onCancel();
    }
}

// Format date/time
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatTime(timeString) {
    if (!timeString) return '-';
    return timeString.slice(0, 5); // HH:MM
}

// Update navigation
function updateNavigation() {
    const userInfo = Auth.getUserInfo();
    const navMenu = document.querySelector('.navbar-menu');
    
    if (!navMenu) return;

    if (userInfo) {
        const isAdmin = userInfo.is_admin;
        const links = [];

        if (isAdmin) {
            links.push(
                { href: '/static/dashboard.html', text: 'Dashboard' },
                { href: '/static/buildings.html', text: 'Buildings' },
                { href: '/static/courses.html', text: 'Courses' },
                { href: '/static/instructors.html', text: 'Instructors' },
                { href: '/static/tas.html', text: 'TAs' },
                { href: '/static/levels.html', text: 'Levels' },
                { href: '/static/schedule.html', text: 'Schedule' }
            );
        } else {
            links.push({ href: '/static/schedule.html', text: 'My Schedule' });
        }

        navMenu.innerHTML = links.map(link => 
            `<a href="${link.href}" class="navbar-link">${link.text}</a>`
        ).join('') + `
            <a href="#" onclick="Auth.logout(); return false;" class="navbar-link">Logout</a>
        `;

        // Highlight active link
        const currentPath = window.location.pathname;
        document.querySelectorAll('.navbar-link').forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
}

// Initialize common elements
document.addEventListener('DOMContentLoaded', () => {
    // Create toast container if it doesn't exist
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Update navigation if user is logged in
    if (Auth.isAuthenticated()) {
        updateNavigation();
    }
});

// Export utilities for global use
window.showNotification = showNotification;
window.showLoading = showLoading;
window.Modal = Modal;
window.getFormData = getFormData;
window.setFormData = setFormData;
window.clearForm = clearForm;
window.validateForm = validateForm;
window.createTable = createTable;
window.Pagination = Pagination;
window.filterData = filterData;
window.sortData = sortData;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.updateNavigation = updateNavigation;

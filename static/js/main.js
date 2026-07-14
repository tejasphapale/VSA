// ============== UTILITIES ==============
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============== MODAL HANDLERS ==============
document.addEventListener('click', function(e) {
    // Close modal when clicking outside
    if (e.target.classList.contains('modal')) {
        e.target.style.display = 'none';
    }
});

// Close modals with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
});

// ============== SIDEBAR TOGGLE ==============
const sidebarToggle = document.getElementById('sidebarToggle');
if (sidebarToggle) {
    sidebarToggle.addEventListener('click', function() {
        const sidebar = document.querySelector('.sidebar');
        sidebar.style.display = sidebar.style.display === 'none' ? 'flex' : 'none';
    });
}

// ============== DATE HELPERS ==============
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// ============== LOCAL STORAGE ==============
function getFromStorage(key, defaultValue = null) {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
}

function saveToStorage(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

// ============== EXPORT HELPERS ==============
function exportToCSV(data, filename = 'export.csv') {
    const csv = convertToCSV(data);
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = filename;
    link.click();
}

function convertToCSV(data) {
    if (!Array.isArray(data) || data.length === 0) {
        return '';
    }
    
    const headers = Object.keys(data[0]);
    const csv = [
        headers.join(','),
        ...data.map(row => 
            headers.map(header => {
                const value = row[header];
                if (value === null || value === undefined) return '';
                if (typeof value === 'string' && value.includes(',')) {
                    return `"${value}"`;
                }
                return value;
            }).join(',')
        )
    ];
    
    return csv.join('\n');
}

// ============== VALIDATION ==============
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone.replace(/[\s-]/g, ''));
}

function validateGST(gst) {
    const re = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
    return re.test(gst);
}

// ============== PRINT HELPERS ==============
function printElement(elementId) {
    const element = document.getElementById(elementId);
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(element.innerHTML);
    printWindow.document.close();
    printWindow.print();
}

// ============== SEARCH HELPERS ==============
function searchInArray(array, searchTerm, fields) {
    return array.filter(item => {
        const term = searchTerm.toLowerCase();
        return fields.some(field => {
            const value = item[field];
            return value && value.toString().toLowerCase().includes(term);
        });
    });
}

// ============== PRICE CALCULATION ==============
function calculateProfitMargin(costPrice, sellingPrice) {
    if (costPrice === 0) return 0;
    return ((sellingPrice - costPrice) / costPrice * 100).toFixed(2);
}

function calculateMarkupPrice(costPrice, marginPercent) {
    return (costPrice * (1 + marginPercent / 100)).toFixed(2);
}

// ============== DEBOUNCE ==============
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============== FORMATTING ==============
function formatIndianNumber(number) {
    return new Intl.NumberFormat('en-IN').format(number);
}

function formatTime(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

// ============== INITIALIZATION ==============
document.addEventListener('DOMContentLoaded', function() {
    // Set data attributes for current date/time
    const now = new Date();
    
    // Initialize any data pickers
    const dateInputs = document.querySelectorAll('input[type="date"]:not([value])');
    dateInputs.forEach(input => {
        if (!input.value) {
            input.valueAsDate = now;
        }
    });
});

// ============== CONFIRM DIALOG ==============
function showConfirm(message, onConfirm, onCancel) {
    if (confirm(message)) {
        onConfirm();
    } else if (onCancel) {
        onCancel();
    }
}

// ============== API HELPERS ==============
async function apiCall(url, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ============== ACTIVE NAVIGATION ==============
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});

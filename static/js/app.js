// Stock Screener Web App JavaScript

// Configuration variables from Flask app
const TOP_N = 5; // Number of top stocks per sector

document.addEventListener('DOMContentLoaded', function() {
    // Update current time
    updateTime();
    setInterval(updateTime, 1000);
    
    // Test server connection
    testServerConnection();
    
    // Form submission handler
    const screenForm = document.getElementById('screenForm');
    screenForm.addEventListener('submit', handleFormSubmit);
    
    // Handle "Scan all" checkbox
    const scanAllCheckbox = document.getElementById('scanAll');
    const sectorSelect = document.getElementById('sectorSelect');
    
    scanAllCheckbox.addEventListener('change', function() {
        if (this.checked) {
            sectorSelect.disabled = true;
            sectorSelect.value = '';
        } else {
            sectorSelect.disabled = false;
        }
    });
});

function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = timeString;
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const submitBtn = document.getElementById('submitBtn');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    
    // Validate form
    const sector = formData.get('sector');
    const scanAll = formData.get('scan_all');
    
    if (!sector && !scanAll) {
        showAlert('Please select a sector or choose to scan all sectors', 'warning');
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Scanning...';
    loadingSection.style.display = 'block';
    resultsSection.style.display = 'none';
    
    try {
        // Submit form
        const response = await fetch('/screen', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            showAlert(data.message || 'An error occurred while screening stocks', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        console.error('Error details:', error.message);
        console.error('Error stack:', error.stack);
        
        // More specific error messages
        if (error.message.includes('Failed to fetch')) {
            showAlert('Network error: Unable to connect to the server. Please check if the server is running.', 'danger');
        } else if (error.message.includes('timeout')) {
            showAlert('Request timeout. The server is taking too long to respond. Please try again.', 'danger');
        } else {
            showAlert(`Network error: ${error.message}. Please try again.`, 'danger');
        }
    } finally {
        // Hide loading state
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-play me-2"></i>Screen Stocks';
        loadingSection.style.display = 'none';
    }
}

function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    
    // Create results HTML
    let resultsHTML = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card results-card fade-in">
                    <div class="card-body">
                        <div class="row align-items-center">
                            <div class="col-md-8">
                                <h5 class="card-title mb-2">
                                    <i class="fas fa-chart-line me-2"></i>
                                    Screening Results: ${data.selected_sector}
                                </h5>
                                <p class="text-muted mb-0">
                                    Scanned ${data.sectors_scanned} sector(s) • 
                                    Found ${data.total_stocks} stocks • 
                                    ${data.timestamp}
                                </p>
                            </div>
                            <div class="col-md-4 text-end">
                                <span class="badge bg-success summary-badge me-2">
                                    <i class="fas fa-check-circle me-1"></i>
                                    ${data.sectors_with_hits} sectors with results
                                </span>
                                <span class="badge bg-info summary-badge">
                                    <i class="fas fa-list me-1"></i>
                                    Top ${TOP_N || 5} per sector
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Display results for each sector
    for (const [sector, sectorData] of Object.entries(data.results)) {
        resultsHTML += createSectorTable(sector, sectorData);
    }
    
    resultsSection.innerHTML = resultsHTML;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function createSectorTable(sector, sectorData) {
    const stocks = sectorData.stocks;
    const columns = sectorData.columns;
    
    if (stocks.length === 0) {
        return `
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card results-card">
                        <div class="card-body">
                            <h6 class="card-title">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                ${sector.toUpperCase()}
                            </h6>
                            <p class="text-muted">No stocks found for this sector.</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Create table header
    let tableHTML = `
        <div class="row mb-4">
            <div class="col-12">
                <div class="card results-card slide-up">
                    <div class="card-body">
                        <h6 class="card-title mb-3">
                            <i class="fas fa-chart-bar me-2"></i>
                            ${sector.toUpperCase()} — Top ${stocks.length} stocks
                        </h6>
                        <div class="table-responsive">
                            <table class="table table-hover results-table">
                                <thead>
                                    <tr>
    `;
    
    // Add column headers
    columns.forEach(col => {
        tableHTML += `<th>${col}</th>`;
    });
    
    tableHTML += `
                                    </tr>
                                </thead>
                                <tbody>
    `;
    
    // Add data rows
    stocks.forEach(stock => {
        tableHTML += '<tr>';
        columns.forEach(col => {
            tableHTML += createTableCell(col, stock[col]);
        });
        tableHTML += '</tr>';
    });
    
    tableHTML += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return tableHTML;
}

function createTableCell(column, value) {
    if (value === 'N/A' || value === null || value === undefined) {
        return `<td class="neutral">N/A</td>`;
    }
    
    let cellClass = '';
    let displayValue = value;
    
    // Apply formatting based on column type
    switch (column) {
        case 'Ticker':
            return `<td><span class="ticker-symbol">${value}</span></td>`;
            
        case 'Company':
            return `<td><span class="company-name">${value}</span></td>`;
            
        case 'Price':
            return `<td><span class="price-value">$${value}</span></td>`;
            
        case 'Change':
        case 'EPS Q/Q':
        case 'Sales Q/Q':
        case 'ROE':
        case 'Debt/Eq':
        case 'Perf Week':
            const numValue = parseFloat(value.replace('%', ''));
            cellClass = numValue > 0 ? 'positive' : numValue < 0 ? 'negative' : 'neutral';
            return `<td class="${cellClass}">${value}</td>`;
            
        case 'Volume':
            return `<td><span class="volume-value">${value}</span></td>`;
            
        case 'P/E':
        case 'EPS (ttm)':
        case 'EPS next Y':
            return `<td class="price-value">${value}</td>`;
            
        default:
            return `<td>${value}</td>`;
    }
}

async function testServerConnection() {
    try {
        const response = await fetch('/test');
        const data = await response.json();
        console.log('Server connection test:', data);
        
        if (!response.ok) {
            showAlert('Server connection issue. Please restart the server.', 'warning');
        }
    } catch (error) {
        console.error('Server connection test failed:', error);
        showAlert('Cannot connect to server. Please make sure the Flask app is running on port 8081.', 'danger');
    }
}

function showAlert(message, type) {
    // Remove existing alerts
    const existingAlert = document.querySelector('.alert-container');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // Create alert container
    const alertContainer = document.createElement('div');
    alertContainer.className = 'alert-container position-fixed top-0 start-50 translate-middle-x mt-3';
    alertContainer.style.zIndex = '1050';
    
    // Create alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        <i class="fas fa-exclamation-circle me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    document.body.appendChild(alertContainer);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertContainer.parentNode) {
            alertContainer.remove();
        }
    }, 5000);
}

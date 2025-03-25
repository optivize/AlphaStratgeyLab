// Main JavaScript for the backtesting UI

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form elements
    initializeStrategySelector();
    setupFormSubmission();
    initializeResultsViewer();
    setupAIBacktestForm();
    
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});

// Initialize strategy selection dropdown
function initializeStrategySelector() {
    const strategySelector = document.getElementById('strategy-selector');
    const parameterContainer = document.getElementById('strategy-parameters');
    
    if (!strategySelector) return;
    
    // Fetch available strategies
    fetch('/api/v1/strategies')
        .then(response => response.json())
        .then(strategies => {
            // Populate strategy dropdown
            strategies.forEach(strategy => {
                const option = document.createElement('option');
                option.value = strategy.id;
                option.textContent = strategy.name;
                strategySelector.appendChild(option);
            });
            
            // Set up change listener
            strategySelector.addEventListener('change', function() {
                const selectedStrategy = this.value;
                if (!selectedStrategy) return;
                
                // Fetch strategy details
                fetch(`/api/v1/strategies/${selectedStrategy}`)
                    .then(response => response.json())
                    .then(strategy => {
                        // Render parameters
                        renderStrategyParameters(strategy, parameterContainer);
                    });
            });
            
            // Trigger change for default selection
            if (strategies.length > 0) {
                strategySelector.value = strategies[0].id;
                strategySelector.dispatchEvent(new Event('change'));
            }
        })
        .catch(error => {
            console.error('Error fetching strategies:', error);
        });
}

// Render strategy parameters
function renderStrategyParameters(strategy, container) {
    container.innerHTML = '';
    
    // Create a fieldset for parameters
    const fieldset = document.createElement('fieldset');
    const legend = document.createElement('legend');
    legend.textContent = `${strategy.name} Parameters`;
    fieldset.appendChild(legend);
    
    // Add parameter inputs
    Object.entries(strategy.parameters).forEach(([key, param]) => {
        const formGroup = document.createElement('div');
        formGroup.className = 'form-group mb-3';
        
        const label = document.createElement('label');
        label.setAttribute('for', `param-${key}`);
        label.textContent = param.name || key;
        
        const input = document.createElement('input');
        input.setAttribute('id', `param-${key}`);
        input.setAttribute('name', `strategy-param-${key}`);
        input.className = 'form-control';
        
        // Set input type based on parameter type
        if (param.type === 'integer') {
            input.setAttribute('type', 'number');
            input.setAttribute('step', '1');
        } else if (param.type === 'float') {
            input.setAttribute('type', 'number');
            input.setAttribute('step', '0.01');
        } else {
            input.setAttribute('type', 'text');
        }
        
        // Set default value
        input.value = param.default;
        
        // Add description if available
        let helpText = null;
        if (param.description) {
            helpText = document.createElement('small');
            helpText.className = 'form-text text-muted';
            helpText.textContent = param.description;
        }
        
        formGroup.appendChild(label);
        formGroup.appendChild(input);
        if (helpText) formGroup.appendChild(helpText);
        
        fieldset.appendChild(formGroup);
    });
    
    container.appendChild(fieldset);
}

// Set up backtest form submission
function setupFormSubmission() {
    const backtestForm = document.getElementById('backtest-form');
    
    if (!backtestForm) return;
    
    backtestForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading indicator
        const submitButton = backtestForm.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Running...';
        
        // Get form data
        const formData = new FormData(backtestForm);
        
        // Prepare request payload
        const payload = {
            strategy: {
                name: formData.get('strategy'),
                parameters: {}
            },
            data: {
                symbols: formData.get('symbols').split(',').map(s => s.trim()),
                start_date: formData.get('start-date'),
                end_date: formData.get('end-date'),
                timeframe: formData.get('timeframe'),
                data_source: formData.get('data-source')
            },
            execution: {
                initial_capital: parseFloat(formData.get('initial-capital')),
                position_size: formData.get('position-size'),
                commission: parseFloat(formData.get('commission')),
                slippage: parseFloat(formData.get('slippage'))
            },
            output: {
                metrics: Array.from(formData.getAll('metrics')),
                include_trades: formData.get('include-trades') === 'on',
                include_equity_curve: formData.get('include-equity-curve') === 'on'
            }
        };
        
        // Get strategy parameters
        document.querySelectorAll('[name^="strategy-param-"]').forEach(input => {
            const paramName = input.name.replace('strategy-param-', '');
            const paramValue = input.type === 'number' ? parseFloat(input.value) : input.value;
            payload.strategy.parameters[paramName] = paramValue;
        });
        
        // Submit backtest request
        fetch('/api/v1/backtest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            // Reset button
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            
            if (data.error) {
                alert('Error from server: ' + data.error);
                return;
            }
            
            // Display a message that the job is pending
            const statusContainer = document.getElementById('status-container');
            if (statusContainer) {
                statusContainer.style.display = 'block';
                statusContainer.innerHTML = `
                    <div class="alert alert-info">
                        <div class="d-flex align-items-center">
                            <div class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></div>
                            <div>${data.message || 'Processing backtest...'} (ID: ${data.backtest_id})</div>
                        </div>
                    </div>
                `;
            }
            
            // Start polling for results
            pollBacktestResults(data.backtest_id);
        })
        .catch(error => {
            console.error('Error submitting backtest:', error);
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            
            alert('Error submitting backtest: ' + error.message);
        });
    });
}

// Poll for backtest results
function pollBacktestResults(backtestId) {
    const resultsContainer = document.getElementById('results-container');
    const statusContainer = document.getElementById('status-container');
    
    if (!statusContainer) return;
    
    // Show status container
    statusContainer.style.display = 'block';
    statusContainer.innerHTML = `
        <div class="alert alert-info">
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></div>
                <div>Processing backtest (ID: ${backtestId})...</div>
            </div>
        </div>
    `;
    
    // Poll for results
    const pollInterval = setInterval(() => {
        fetch(`/api/v1/backtest/${backtestId}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed') {
                    // Clear interval and display results
                    clearInterval(pollInterval);
                    statusContainer.style.display = 'none';
                    displayBacktestResults(data);
                } else if (data.status === 'failed') {
                    // Clear interval and show error
                    clearInterval(pollInterval);
                    statusContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Backtest failed:</strong> ${data.error || 'Unknown error'}
                        </div>
                    `;
                }
                // If still pending or running, continue polling
            })
            .catch(error => {
                console.error('Error polling backtest results:', error);
                clearInterval(pollInterval);
                statusContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> Failed to retrieve backtest results
                    </div>
                `;
            });
    }, 2000);
}

// Display backtest results
function displayBacktestResults(data) {
    const resultsContainer = document.getElementById('results-container');
    
    if (!resultsContainer) return;
    
    // Show results container
    resultsContainer.style.display = 'block';
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Create results card
    const card = document.createElement('div');
    card.className = 'card mb-4';
    
    // Create card header
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header bg-primary text-white';
    cardHeader.innerHTML = `
        <h4 class="mb-0">Backtest Results <small class="text-white-50">(ID: ${data.backtest_id})</small></h4>
        <div class="small">Execution time: ${data.execution_time} seconds</div>
    `;
    
    // Create card body
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Add overall metrics
    if (data.results && data.results.overall_metrics) {
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'mb-4';
        
        const metricsTitle = document.createElement('h5');
        metricsTitle.textContent = 'Overall Performance Metrics';
        metricsDiv.appendChild(metricsTitle);
        
        const metricsTable = document.createElement('table');
        metricsTable.className = 'table table-sm table-striped';
        
        const tbody = document.createElement('tbody');
        
        // Add metric rows
        Object.entries(data.results.overall_metrics).forEach(([key, value]) => {
            if (value !== null) {
                const row = document.createElement('tr');
                
                const labelCell = document.createElement('td');
                labelCell.className = 'fw-bold';
                labelCell.textContent = formatMetricName(key);
                
                const valueCell = document.createElement('td');
                valueCell.textContent = formatMetricValue(key, value);
                
                row.appendChild(labelCell);
                row.appendChild(valueCell);
                tbody.appendChild(row);
            }
        });
        
        metricsTable.appendChild(tbody);
        metricsDiv.appendChild(metricsTable);
        cardBody.appendChild(metricsDiv);
    }
    
    // Add equity curve chart if present
    if (data.results && data.results.equity_curve && data.results.equity_curve.length > 0) {
        const chartDiv = document.createElement('div');
        chartDiv.className = 'mb-4';
        
        const chartTitle = document.createElement('h5');
        chartTitle.textContent = 'Equity Curve';
        chartDiv.appendChild(chartTitle);
        
        const canvas = document.createElement('canvas');
        canvas.id = 'equity-curve-chart';
        canvas.style.width = '100%';
        canvas.style.height = '300px';
        
        chartDiv.appendChild(canvas);
        cardBody.appendChild(chartDiv);
        
        // We'll initialize the chart after the element is in the DOM
    }
    
    // Add trades table if present
    if (data.results && data.results.trades && data.results.trades.length > 0) {
        const tradesDiv = document.createElement('div');
        tradesDiv.className = 'mb-4';
        
        const tradesTitle = document.createElement('h5');
        tradesTitle.textContent = 'Trades';
        tradesDiv.appendChild(tradesTitle);
        
        const tradesTable = document.createElement('table');
        tradesTable.className = 'table table-sm table-striped table-hover';
        
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Symbol</th>
                <th>Entry Date</th>
                <th>Exit Date</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>Size</th>
                <th>P&L</th>
            </tr>
        `;
        
        const tbody = document.createElement('tbody');
        
        // Add trade rows (limit to 100 for performance)
        const tradesLimit = Math.min(data.results.trades.length, 100);
        for (let i = 0; i < tradesLimit; i++) {
            const trade = data.results.trades[i];
            const row = document.createElement('tr');
            
            // Set row class based on profit/loss
            if (trade.pnl > 0) {
                row.className = 'table-success';
            } else if (trade.pnl < 0) {
                row.className = 'table-danger';
            }
            
            row.innerHTML = `
                <td>${trade.symbol}</td>
                <td>${formatDate(trade.entry_date)}</td>
                <td>${trade.exit_date ? formatDate(trade.exit_date) : '-'}</td>
                <td>${formatPrice(trade.entry_price)}</td>
                <td>${trade.exit_price ? formatPrice(trade.exit_price) : '-'}</td>
                <td>${trade.position_size}</td>
                <td>${formatPnL(trade.pnl)}</td>
            `;
            
            tbody.appendChild(row);
        }
        
        tradesTable.appendChild(thead);
        tradesTable.appendChild(tbody);
        
        if (data.results.trades.length > tradesLimit) {
            const noteDiv = document.createElement('div');
            noteDiv.className = 'small text-muted mt-2';
            noteDiv.textContent = `Showing ${tradesLimit} of ${data.results.trades.length} trades`;
            tradesDiv.appendChild(noteDiv);
        }
        
        tradesDiv.appendChild(tradesTable);
        cardBody.appendChild(tradesDiv);
    }
    
    // Assemble the card
    card.appendChild(cardHeader);
    card.appendChild(cardBody);
    
    // Add to results container
    resultsContainer.appendChild(card);
    
    // Initialize chart if equity curve is present
    if (data.results && data.results.equity_curve && data.results.equity_curve.length > 0) {
        initEquityCurveChart(data.results.equity_curve);
    }
}

// Initialize the equity curve chart
function initEquityCurveChart(equityCurve) {
    const ctx = document.getElementById('equity-curve-chart').getContext('2d');
    
    // Generate labels (just indices for simplicity)
    const labels = Array.from({ length: equityCurve.length }, (_, i) => i);
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Equity',
                data: equityCurve,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Equity: $${context.raw.toFixed(2)}`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize results viewer
function initializeResultsViewer() {
    // Check if backtest ID is in URL
    const urlParams = new URLSearchParams(window.location.search);
    const backtestId = urlParams.get('backtest_id');
    
    if (backtestId) {
        // Fetch and display backtest results
        fetch(`/api/v1/backtest/${backtestId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Backtest not found');
                }
                return response.json();
            })
            .then(data => {
                displayBacktestResults(data);
            })
            .catch(error => {
                console.error('Error loading backtest:', error);
                
                const statusContainer = document.getElementById('status-container');
                if (statusContainer) {
                    statusContainer.style.display = 'block';
                    statusContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error:</strong> ${error.message}
                        </div>
                    `;
                }
            });
    }
}

// Helper functions
function formatMetricName(key) {
    // Convert camelCase or snake_case to Title Case With Spaces
    return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

function formatMetricValue(key, value) {
    if (typeof value === 'number') {
        if (key.includes('return') || key.includes('drawdown') || key === 'win_rate') {
            return (value * 100).toFixed(2) + '%';
        } else if (key.includes('ratio')) {
            return value.toFixed(2);
        } else if (Number.isInteger(value)) {
            return value.toString();
        } else {
            return value.toFixed(2);
        }
    }
    return value;
}

function formatDate(dateStr) {
    // Format ISO date string to more readable format
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function formatPrice(price) {
    return '$' + price.toFixed(2);
}

function formatPnL(pnl) {
    if (pnl === null) return '-';
    
    if (pnl > 0) {
        return `+$${pnl.toFixed(2)}`;
    } else {
        return `-$${Math.abs(pnl).toFixed(2)}`;
    }
}

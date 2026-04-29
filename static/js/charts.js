/**
 * SPARS — Chart.js Theme Configuration (Light Blue Theme)
 * Bright colour palette for visible, premium charts
 */

// Light theme defaults
Chart.defaults.color = '#374151';
Chart.defaults.borderColor = 'rgba(59, 130, 246, 0.1)';
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.92)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(59, 130, 246, 0.5)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
Chart.defaults.animation.duration = 800;
Chart.defaults.animation.easing = 'easeOutQuart';

// ── Bright Color Palette ──
const SPARS_COLORS = {
    primary:      '#3b82f6',
    primaryLight: '#60a5fa',
    primaryDark:  '#2563eb',
    success:  '#10b981',
    warning:  '#f59e0b',
    danger:   '#ef4444',
    info:     '#8b5cf6',
    bars: [
        'rgba(59, 130, 246, 0.88)',
        'rgba(16, 185, 129, 0.88)',
        'rgba(245, 158, 11, 0.88)',
        'rgba(239, 68, 68, 0.88)',
        'rgba(139, 92, 246, 0.88)'
    ],
    barBorders: [
        '#3b82f6',
        '#10b981',
        '#f59e0b',
        '#ef4444',
        '#8b5cf6'
    ]
};

/**
 * Create a CO Bar Chart
 */
function createCOBarChart(canvasId, values, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !values || values.length === 0) return null;

    // Destroy existing chart if any
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    const ctx = canvas.getContext('2d');

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['CO1', 'CO2', 'CO3', 'CO4', 'CO5'],
            datasets: [{
                label: title || 'CO Average',
                data: values.map(v => Math.round(v * 100) / 100),
                backgroundColor: SPARS_COLORS.bars,
                borderColor: SPARS_COLORS.barBorders,
                borderWidth: 1.5,
                borderRadius: 8,
                borderSkipped: false,
                barPercentage: 0.65,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.6,
            plugins: {
                legend: { display: false },
                title: {
                    display: !!title,
                    text: title,
                    font: { size: 14, weight: '600' },
                    color: '#1e3a5f',
                    padding: { bottom: 16 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed.y.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: {
                        font: { weight: '600', size: 12 },
                        color: '#3b82f6'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(59, 130, 246, 0.08)',
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 11 },
                        color: '#6b7280',
                        padding: 8
                    }
                }
            }
        }
    });
}


/**
 * Create an Attainment Doughnut Chart
 */
function createAttainmentChart(canvasId, data, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    // Destroy existing chart if any
    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    const ctx = canvas.getContext('2d');

    const labels = [];
    const values = [];
    const colors = [];
    const borderColors = [];

    if (data.low > 0) {
        labels.push('Low (< 40%)');
        values.push(data.low);
        colors.push('rgba(239, 68, 68, 0.85)');
        borderColors.push('#ef4444');
    }
    if (data.medium > 0) {
        labels.push('Medium (40–70%)');
        values.push(data.medium);
        colors.push('rgba(245, 158, 11, 0.85)');
        borderColors.push('#f59e0b');
    }
    if (data.high > 0) {
        labels.push('High (> 70%)');
        values.push(data.high);
        colors.push('rgba(16, 185, 129, 0.85)');
        borderColors.push('#10b981');
    }

    if (values.length === 0) return null;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderColor: borderColors,
                borderWidth: 2,
                hoverOffset: 10,
                spacing: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '58%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 14,
                        font: { size: 12 },
                        color: '#374151'
                    }
                },
                title: {
                    display: !!title,
                    text: title,
                    font: { size: 13, weight: '600' },
                    color: '#1e3a5f',
                    padding: { bottom: 12 }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((context.parsed / total) * 100).toFixed(1);
                            return ` ${context.label}: ${context.parsed} students (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}


/**
 * Create a Radar Chart (student CO overview)
 */
function createCORadarChart(canvasId, values, title) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !values || values.length === 0) return null;

    const existing = Chart.getChart(canvas);
    if (existing) existing.destroy();

    const ctx = canvas.getContext('2d');

    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['CO1', 'CO2', 'CO3', 'CO4', 'CO5'],
            datasets: [{
                label: title || 'CO Performance',
                data: values.map(v => Math.round(v * 100) / 100),
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                borderColor: '#3b82f6',
                borderWidth: 2.5,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 1.3,
            plugins: {
                legend: { display: false },
                title: {
                    display: !!title,
                    text: title,
                    font: { size: 14, weight: '600' },
                    color: '#1e3a5f',
                    padding: { bottom: 8 }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    grid: { color: 'rgba(59, 130, 246, 0.12)' },
                    angleLines: { color: 'rgba(59, 130, 246, 0.15)' },
                    pointLabels: {
                        color: '#3b82f6',
                        font: { size: 13, weight: '600' }
                    },
                    ticks: {
                        display: false
                    }
                }
            }
        }
    });
}

// Expose globally
window.SPARSCharts = { createCOBarChart, createAttainmentChart, createCORadarChart, SPARS_COLORS };

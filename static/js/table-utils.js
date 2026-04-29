/**
 * SPARS — Table Utilities
 * Sortable columns, live search/filter, CSV export
 * Auto-initializes on any table with class "data-table"
 */
(function () {
    'use strict';

    /* ================================================================
       SORTABLE TABLE HEADERS
       ================================================================ */
    function initSortable(table) {
        const headers = table.querySelectorAll('th');
        let currentSort = { index: -1, dir: 'none' };

        headers.forEach((th, colIndex) => {
            // Skip columns that shouldn't sort (e.g. action columns)
            if (th.dataset.noSort !== undefined) return;

            th.classList.add('sortable');

            th.addEventListener('click', () => {
                const tbody = table.querySelector('tbody');
                if (!tbody) return;

                const rows = Array.from(tbody.querySelectorAll('tr:not(.hidden-row)'));

                // Determine sort direction
                let dir = 'asc';
                if (currentSort.index === colIndex && currentSort.dir === 'asc') {
                    dir = 'desc';
                }

                // Sort rows
                rows.sort((a, b) => {
                    let aText = getCellValue(a, colIndex);
                    let bText = getCellValue(b, colIndex);

                    // Try numeric comparison
                    const aNum = parseFloat(aText.replace(/[^0-9.\-]/g, ''));
                    const bNum = parseFloat(bText.replace(/[^0-9.\-]/g, ''));

                    if (!isNaN(aNum) && !isNaN(bNum)) {
                        return dir === 'asc' ? aNum - bNum : bNum - aNum;
                    }

                    // String comparison
                    return dir === 'asc'
                        ? aText.localeCompare(bText)
                        : bText.localeCompare(aText);
                });

                // Reorder rows
                rows.forEach(row => tbody.appendChild(row));

                // Update header classes
                headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
                th.classList.add(dir === 'asc' ? 'sort-asc' : 'sort-desc');

                currentSort = { index: colIndex, dir: dir };
            });
        });
    }

    function getCellValue(row, index) {
        const cell = row.cells[index];
        if (!cell) return '';
        // Use data-value attribute if present (for formatted values)
        if (cell.dataset.value) return cell.dataset.value;
        return cell.textContent.trim();
    }

    /* ================================================================
       LIVE TABLE SEARCH / FILTER
       ================================================================ */
    function initTableSearch(searchInput, table) {
        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const countEl = searchInput.closest('.table-header')?.querySelector('.table-count');
        const totalRows = tbody.querySelectorAll('tr').length;

        searchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase().trim();
            const rows = tbody.querySelectorAll('tr');
            let visible = 0;

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const matches = query === '' || text.includes(query);
                row.classList.toggle('hidden-row', !matches);
                if (matches) visible++;
            });

            // Update count
            if (countEl) {
                countEl.textContent = query
                    ? `${visible} of ${totalRows}`
                    : `${totalRows} rows`;
            }
        });
    }

    /* ================================================================
       CSV EXPORT
       ================================================================ */
    function exportCSV(table, filename) {
        const rows = table.querySelectorAll('tr:not(.hidden-row)');
        const csvData = [];

        rows.forEach(row => {
            const rowData = [];
            row.querySelectorAll('th, td').forEach(cell => {
                let text = cell.textContent.trim().replace(/"/g, '""');
                rowData.push(`"${text}"`);
            });
            csvData.push(rowData.join(','));
        });

        const csv = csvData.join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = (filename || 'export') + '.csv';
        link.click();

        URL.revokeObjectURL(url);
    }

    /* ================================================================
       AUTO-INITIALIZE
       ================================================================ */
    function init() {
        // Initialize all data tables
        document.querySelectorAll('table.data-table').forEach(table => {
            initSortable(table);
        });

        // Bind search inputs to their tables
        document.querySelectorAll('[data-table-search]').forEach(input => {
            const tableId = input.dataset.tableSearch;
            const table = document.getElementById(tableId);
            if (table) {
                initTableSearch(input, table);
            }
        });

        // Bind CSV export buttons
        document.querySelectorAll('[data-csv-export]').forEach(btn => {
            btn.addEventListener('click', () => {
                const tableId = btn.dataset.csvExport;
                const table = document.getElementById(tableId);
                const filename = btn.dataset.filename || 'spars_export';
                if (table) exportCSV(table, filename);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose globally for manual use
    window.SPARSTable = { initSortable, initTableSearch, exportCSV };

})();

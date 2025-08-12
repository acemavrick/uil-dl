// minimal javascript for uil-dl 1.0.0-beta (htmx version)
// Using Claude 3.7 Sonnet (Thinking)

document.addEventListener('DOMContentLoaded', function() {
    console.log('uil-dl 1.0.0-beta initialized with htmx');
    
    // Initialize tag-based filter UI
    // initializeCheckboxFilters converts change events via built-in forms; tag UI removed so skip.
    
    // simple select-all functionality - complex UI that benefits from client-side handling
    // Note: selectAllCheckbox is now loaded dynamically via HTMX, so we use event delegation

    /* ---------- sync helpers ---------- */
    function updateRowCheckbox(row) {
        const rowBox = row.querySelector('.row-checkbox');
        if (!rowBox) return;

        const allFileCheckboxes = row.querySelectorAll('.packet-checkbox, .datafile-checkbox');
        const selectable = row.querySelectorAll('.packet-checkbox:not(:disabled), .datafile-checkbox:not(:disabled)');

        if (allFileCheckboxes.length === 0) {
            // No downloadable files in this row.
            rowBox.disabled = true;
            rowBox.checked = false;
        } else if (selectable.length === 0) {
            // All available files are already downloaded.
            rowBox.disabled = true;
            rowBox.checked = true;
        } else {
            // Some files are available for download.
            rowBox.disabled = false;
            rowBox.checked = Array.from(selectable).every(cb => cb.checked);
        }
    }

    function updateSelectAll() {
        const selectAllCheckbox = document.getElementById('select-all');
        if (!selectAllCheckbox) return;

        const allCheckboxes = document.querySelectorAll('.packet-checkbox, .datafile-checkbox');
        const allSelectable = document.querySelectorAll('.packet-checkbox:not(:disabled), .datafile-checkbox:not(:disabled)');
        
        if (allCheckboxes.length === 0) {
            // No downloadable files on the page at all.
            selectAllCheckbox.disabled = true;
            selectAllCheckbox.checked = false;
        } else if (allSelectable.length === 0) {
            // All available files on the page are already downloaded.
            selectAllCheckbox.disabled = true;
            selectAllCheckbox.checked = true;
        } else {
            // There are still some files that can be selected.
            selectAllCheckbox.disabled = false;
            selectAllCheckbox.checked = Array.from(allSelectable).every(cb => cb.checked);
        }
    }

    function updateDownloadButton() {
        const downloadBtn = document.getElementById('download-selected');
        const checkedBoxes = document.querySelectorAll('.packet-checkbox:checked:not(:disabled), .datafile-checkbox:checked:not(:disabled)');
        if (downloadBtn) {
            downloadBtn.disabled = checkedBoxes.length === 0;
        }
    }
    /* ----------------------------------- */
    
    // select all functionality using event delegation (since checkbox is loaded via HTMX)
    document.addEventListener('change', function(e) {
        if (e.target.id === 'select-all') {
            const checkboxes = document.querySelectorAll('.packet-checkbox:not(:disabled), .datafile-checkbox:not(:disabled)');
            checkboxes.forEach(checkbox => { checkbox.checked = e.target.checked; });
            // toggle row-level checkboxes to match global selection
            const rowCheckboxes = document.querySelectorAll('.row-checkbox:not(:disabled)');
            rowCheckboxes.forEach(cb => { cb.checked = e.target.checked; });
            document.querySelectorAll('tbody tr').forEach(updateRowCheckbox);
            updateDownloadButton();
        }
    });
    
    // Tags UI ------------------------------------------------------
    const filterForm = document.getElementById('filter-form');
    const tagsContainer = document.getElementById('filter-tags');

    function renderFilterTags() {
        if (!tagsContainer || !filterForm) return;
        tagsContainer.innerHTML = '';
        const checked = filterForm.querySelectorAll('input[type="checkbox"]:checked');
        checked.forEach(input => {
            const tag = document.createElement('span');
            tag.className = 'bg-emerald-100 text-emerald-800 dark:bg-emerald-800 dark:text-emerald-100 text-xs px-2 py-1 rounded flex items-center space-x-1';
            tag.innerHTML = `<span>${input.value}</span><button type="button" class="remove-tag ml-1" data-name="${input.name}" data-value="${input.value}">&times;</button>`;
            tagsContainer.appendChild(tag);
        });
        tagsContainer.style.display = checked.length ? 'flex' : 'none';
    }

    if (filterForm) {
        filterForm.addEventListener('change', renderFilterTags);
        renderFilterTags();
    }

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-tag')) {
            const name = e.target.getAttribute('data-name');
            const value = e.target.getAttribute('data-value');
            const input = filterForm.querySelector(`input[name="${name}"][value="${CSS.escape(value)}"]`);
            if (input) {
                input.checked = false;
                // trigger change so HTMX updates
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }
    });
    // --------------------------------------------------------------

    // updated listener for individual packet/datafile checkbox changes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('packet-checkbox') || 
            e.target.classList.contains('datafile-checkbox')) {
            const row = e.target.closest('tr');
            if (row) updateRowCheckbox(row);
            updateDownloadButton();
            updateSelectAll();
        }
    });

    // row selection functionality (toggle entire row)
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('row-checkbox')) {
            const row = e.target.closest('tr');
            if (row) {
                const selectable = row.querySelectorAll('.packet-checkbox:not(:disabled), .datafile-checkbox:not(:disabled)');
                selectable.forEach(cb => cb.checked = e.target.checked);
                updateRowCheckbox(row);
            }
            updateDownloadButton();
            updateSelectAll();
        }
    });
    
    // download selected functionality - collect selected files for batch download (backend TBD)
    const downloadSelectedBtn = document.getElementById('download-selected');
    if (downloadSelectedBtn) {
        downloadSelectedBtn.addEventListener('click', function() {
            const selectedBoxes = document.querySelectorAll('.packet-checkbox:checked:not(:disabled), .datafile-checkbox:checked:not(:disabled)');
            if (selectedBoxes.length === 0) return;

            // build payload of selected files
            const payload = Array.from(selectedBoxes).map(cb => ({
                id: cb.getAttribute('data-id'),
                type: cb.getAttribute('data-type')
            }));

            // swap each checkbox UI to spinner
            selectedBoxes.forEach(cb => {
                const cell = cb.closest('td');
                if (cell) {
                    cell.dataset.originalHtml = cell.innerHTML;
                    cell.innerHTML = '<div class="spinner"></div>';
                }
            });

            // send batch request to backend
            downloadSelectedBtn.disabled = true;
            downloadSelectedBtn.textContent = 'Downloading...';

            fetch('/batch-download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ items: payload })
            })
            .then(res => res.json())
            .then(data => {
                console.log('Batch download response', data);

                // replace spinner with checkmark per result
                if (data && Array.isArray(data.results)) {
                    data.results.forEach(result => {
                        if (!result.downloaded) return;
                        const cellId = `${result.link_type}-cell-${result.item_id}`;
                        const cell = document.getElementById(cellId);
                        if (cell) {
                            cell.innerHTML = '<span class="text-green-600">✓</span>';
                        }
                    });
                }

                // refresh cache info
                htmx.ajax('GET', '/cache-stats', '#cache-info div');
                // reload table to ensure other columns (status) update
                htmx.trigger('#filter-form', 'submit');
            })
            .catch(err => {
                console.error('Batch download failed', err);
                // restore original cell HTML on failure
                selectedBoxes.forEach(cb => {
                    const cell = cb.closest('td');
                    if (cell && cell.dataset.originalHtml) {
                        cell.innerHTML = cell.dataset.originalHtml;
                    }
                });
            })
            .finally(() => {
                downloadSelectedBtn.disabled = false;
                downloadSelectedBtn.textContent = 'Download Selected';
                // clear selections
                selectedBoxes.forEach(cb => cb.checked = false);
                document.querySelectorAll('tbody tr').forEach(updateRowCheckbox);
                updateDownloadButton();
                updateSelectAll();
            });
        });
    }
    
    // update form submission when table is reloaded
    document.addEventListener('htmx:afterSwap', function(e) {
        // only update if this was a table swap
        if (e.target.id === 'table-container') {
            document.querySelectorAll('tbody tr').forEach(updateRowCheckbox);
            updateDownloadButton();
            updateSelectAll();
        }
    });
});

// sorting functionality using HTMX
function updateSort(column) {
    const sortByInput = document.querySelector('input[name="sort_by"]');
    const sortDirInput = document.querySelector('input[name="sort_dir"]');
    
    if (sortByInput.value === column) {
        // toggle direction
        sortDirInput.value = sortDirInput.value === 'asc' ? 'desc' : 'asc';
    } else {
        // new column
        sortByInput.value = column;
        sortDirInput.value = 'asc';
    }
    
    // trigger the form to reload data
    htmx.trigger('#filter-form', 'submit');
}

// old tag filter helpers removed – no longer needed 
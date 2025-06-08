// UIL Downloads App - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize variables
    const contestsTableBody = document.getElementById('contests-table-body');
    const selectAllCheckbox = document.getElementById('select-all');
    const selectAllPacketsCheckbox = document.getElementById('select-all-packets');
    const selectAllDatafilesCheckbox = document.getElementById('select-all-datafiles');
    const downloadSelectedBtn = document.getElementById('download-selected');
    const downloadedFilter = document.getElementById('downloaded-filter');
    const reloadCacheBtn = document.getElementById('reload-cache-btn');
    const resetCacheBtn = document.getElementById('reset-cache-btn');
    const cacheFileCount = document.getElementById('cache-file-count');
    const cacheSize = document.getElementById('cache-size');
    
    // Initialize filter variables
    const filterGroups = [
        {
            name: 'subject',
            container: document.getElementById('subject-filter-container'),
            input: document.getElementById('subject-filter-input'),
            dropdown: document.getElementById('subject-filter-dropdown'),
            options: Array.from(document.querySelectorAll('.subject-option')),
            selectAll: document.getElementById('subject-select-all'),
            selectedTags: document.getElementById('subject-selected-tags'),
            selected: new Set()
        },
        {
            name: 'level',
            container: document.getElementById('level-filter-container'),
            input: document.getElementById('level-filter-input'),
            dropdown: document.getElementById('level-filter-dropdown'),
            options: Array.from(document.querySelectorAll('.level-option')),
            selectAll: document.getElementById('level-select-all'),
            selectedTags: document.getElementById('level-selected-tags'),
            selected: new Set()
        },
        {
            name: 'year',
            container: document.getElementById('year-filter-container'),
            input: document.getElementById('year-filter-input'),
            dropdown: document.getElementById('year-filter-dropdown'),
            options: Array.from(document.querySelectorAll('.year-option')),
            selectAll: document.getElementById('year-select-all'),
            selectedTags: document.getElementById('year-selected-tags'),
            selected: new Set()
        }
    ];
    
    // Global sorting state
    let currentSortBy = 'year';
    let currentSortDir = 'desc'; // 'asc' or 'desc'
    
    // Format bytes to human-readable format
    window.formatBytes = function(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    };
    
    // Update cache stats display
    function updateCacheStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error fetching cache stats:', data.error);
                    return;
                }
                
                cacheFileCount.textContent = data.downloaded_files;
                cacheSize.textContent = formatBytes(data.download_size_bytes);
            })
            .catch(error => {
                console.error('Error updating cache stats:', error);
            });
    }
    
    // Initialize multiselect dropdown functionality
    function initializeMultiselect() {
        // Set up event listeners for each filter group
        filterGroups.forEach(group => {
            // Show dropdown when clicking on the input container or dropdown toggle
            const dropdownToggle = group.container.querySelector('.dropdown-toggle');
            if (dropdownToggle) {
                dropdownToggle.addEventListener('click', function(e) {
                    e.stopPropagation();
                    toggleDropdown(group);
                });
            }
            
            group.input.addEventListener('click', function(e) {
                e.stopPropagation();
                openDropdown(group);
            });
            
            // Filter options when typing in the input
            group.input.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                const options = document.querySelectorAll(`#${group.name}-options > div`);
                
                options.forEach(option => {
                    const label = option.querySelector('label').textContent.toLowerCase();
                    if (label.includes(searchTerm)) {
                        option.classList.remove('hidden');
                    } else {
                        option.classList.add('hidden');
                    }
                });
            });
            
            // Handle select all checkbox
            group.selectAll.addEventListener('change', function(e) {
                e.stopPropagation();
                const isChecked = this.checked;
                
                group.options.forEach(option => {
                    option.checked = isChecked;
                    if (isChecked) {
                        group.selected.add(option.value);
                    } else {
                        group.selected.delete(option.value);
                    }
                });
                
                updateSelectedTags(group);
                loadContests();
            });
            
            // Handle individual option checkboxes
            group.options.forEach(option => {
                option.addEventListener('change', function(e) {
                    e.stopPropagation();
                    if (this.checked) {
                        group.selected.add(this.value);
                    } else {
                        group.selected.delete(this.value);
                    }
                    
                    // Update select all checkbox state
                    updateSelectAllState(group);
                    updateSelectedTags(group);
                    loadContests();
                });
                
                // Prevent dropdown from closing when clicking on option labels
                const optionContainer = option.closest('div');
                if (optionContainer) {
                    optionContainer.addEventListener('click', function(e) {
                        e.stopPropagation();
                    });
                }
            });
            
            // Prevent dropdown from closing when clicking inside it
            group.dropdown.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', function() {
            closeAllDropdowns();
        });
    }
    
    // Open a specific dropdown
    function openDropdown(group) {
        // Close all other dropdowns first
        filterGroups.forEach(g => {
            if (g !== group) {
                g.dropdown.classList.add('hidden');
                g.container.classList.remove('dropdown-active');
            }
        });
        
        // Open this dropdown
        group.dropdown.classList.remove('hidden');
        group.container.classList.add('dropdown-active');
    }
    
    // Toggle a dropdown's visibility
    function toggleDropdown(group) {
        if (group.dropdown.classList.contains('hidden')) {
            openDropdown(group);
        } else {
            group.dropdown.classList.add('hidden');
            group.container.classList.remove('dropdown-active');
        }
    }
    
    // Close all dropdown menus
    function closeAllDropdowns() {
        filterGroups.forEach(group => {
            group.dropdown.classList.add('hidden');
            group.container.classList.remove('dropdown-active');
        });
    }
    
    // Update the select all checkbox state based on selected options
    function updateSelectAllState(group) {
        const totalOptions = group.options.length;
        const selectedOptions = group.selected.size;
        
        if (selectedOptions === 0) {
            group.selectAll.checked = false;
            group.selectAll.indeterminate = false;
        } else if (selectedOptions === totalOptions) {
            group.selectAll.checked = true;
            group.selectAll.indeterminate = false;
        } else {
            group.selectAll.checked = false;
            group.selectAll.indeterminate = true;
        }
    }
    
    // Update the selected tags display
    function updateSelectedTags(group) {
        group.selectedTags.innerHTML = '';
        
        group.selected.forEach(value => {
            const tag = document.createElement('span');
            tag.className = 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-100 border border-gray-300 dark:border-gray-500 m-0.5 filter-tag';
            tag.setAttribute('data-value', value);
            
            const tagText = document.createElement('span');
            tagText.textContent = value;
            
            const removeBtn = document.createElement('button');
            removeBtn.className = 'ml-1.5 h-4 w-4 rounded-full inline-flex items-center justify-center bg-gray-300 text-gray-600 dark:bg-gray-500 dark:text-gray-200 focus:outline-none remove-tag';
            removeBtn.innerHTML = '&times;';
            removeBtn.addEventListener('click', function() {
                // Find and uncheck the corresponding checkbox
                const checkbox = document.querySelector(`.${group.name}-option[value="${value}"]`);
                if (checkbox) checkbox.checked = false;
                
                // Remove from selected set
                group.selected.delete(value);
                
                // Update the UI
                tag.remove();
                updateSelectAllState(group);
                loadContests();
            });
            
            tag.appendChild(tagText);
            tag.appendChild(removeBtn);
            group.selectedTags.appendChild(tag);
        });
    }
    
    // Load contest data and populate table
    function loadContests() {
        // Build query string from filters
        const params = new URLSearchParams();
        
        // Add multiselect filter values
        filterGroups.forEach(group => {
            if (group.selected.size > 0) {
                Array.from(group.selected).forEach(value => {
                    params.append(group.name, value);
                });
            }
        });
        
        // Add downloaded filter
        if (downloadedFilter.value) {
            params.append('downloaded', downloadedFilter.value);
        }
        
        // Show loading indicator
        contestsTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center">
                    <div class="flex justify-center">
                        <div class="spinner mr-2"></div>
                        Loading contests...
                    </div>
                </td>
            </tr>
        `;
        
        // Fetch contest data
        fetch(`/api/contests?${params.toString()}`)
            .then(response => response.json())
            .then(data => {
                // Clear existing rows
                contestsTableBody.innerHTML = '';
                
                if (data.error) {
                    contestsTableBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="px-6 py-4 text-center text-red-500">
                                ${data.error}
                            </td>
                        </tr>
                    `;
                    return;
                }
                
                if (data.length === 0) {
                    contestsTableBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                                No contests found matching the current filters.
                            </td>
                        </tr>
                    `;
                    return;
                }
                
                // Sort the data
                sortData(data);
                
                // Populate table with contest data
                data.forEach(contest => {
                    const row = document.createElement('tr');
                    row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700';
                    row.setAttribute('data-id', contest.id);
                    row.setAttribute('data-subject', contest.subject);
                    row.setAttribute('data-level', contest.level);
                    row.setAttribute('data-year', contest.year);
                    
                    // Determine status for sorting
                    let status = 'not_downloaded';
                    let allDownloaded = contest.contest && contest.contest.downloaded;
                    if (contest.data_file) {
                        allDownloaded = allDownloaded && contest.data_file.downloaded;
                    } else {
                        allDownloaded = contest.contest && contest.contest.downloaded;
                    }
                    
                    let partiallyDownloaded = (contest.contest && contest.contest.downloaded) || 
                                              (contest.data_file && contest.data_file.downloaded);
                    
                    if (allDownloaded) {
                        status = 'all_downloaded';
                    } else if (partiallyDownloaded) {
                        status = 'partially_downloaded';
                    }
                    
                    row.setAttribute('data-status', status);
                    
                    // Create the row selection checkbox cell
                    const rowCheckboxCell = document.createElement('td');
                    rowCheckboxCell.className = 'px-3 py-4 whitespace-nowrap';
                    const rowCheckbox = document.createElement('input');
                    rowCheckbox.type = 'checkbox';
                    rowCheckbox.className = 'row-checkbox h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded';
                    rowCheckbox.setAttribute('data-id', contest.id);
                    
                    // Attach event to select both packet and data file checkboxes
                    rowCheckbox.addEventListener('change', function() {
                        const packetCheckbox = row.querySelector('.packet-checkbox');
                        const dataFileCheckbox = row.querySelector('.datafile-checkbox');
                        
                        if (packetCheckbox) {
                            packetCheckbox.checked = this.checked;
                            if (packetCheckbox.disabled) {
                                packetCheckbox.checked = false;
                            }
                        }
                        
                        if (dataFileCheckbox && !dataFileCheckbox.disabled) {
                            dataFileCheckbox.checked = this.checked;
                            if (dataFileCheckbox.disabled) {
                                dataFileCheckbox.checked = false;
                            }
                        }
                        
                        updateSelectAllCheckboxes();
                    });
                    
                    rowCheckboxCell.appendChild(rowCheckbox);
                    row.appendChild(rowCheckboxCell);
                    
                    // Create the subject cell
                    const subjectCell = document.createElement('td');
                    subjectCell.className = 'px-3 py-4 whitespace-nowrap text-gray-800 dark:text-gray-200';
                    subjectCell.textContent = contest.subject;
                    row.appendChild(subjectCell);
                    
                    // Create the level cell
                    const levelCell = document.createElement('td');
                    levelCell.className = 'px-3 py-4 whitespace-nowrap text-gray-800 dark:text-gray-200';
                    levelCell.textContent = contest.level;
                    row.appendChild(levelCell);
                    
                    // Create the year cell
                    const yearCell = document.createElement('td');
                    yearCell.className = 'px-3 py-4 whitespace-nowrap text-gray-800 dark:text-gray-200';
                    yearCell.textContent = contest.year;
                    row.appendChild(yearCell);
                    
                    // Create the packet checkbox cell
                    const packetCell = document.createElement('td');
                    packetCell.className = 'px-3 py-4 whitespace-nowrap text-center';
                    
                    if (contest.contest) {
                        const packetContainer = document.createElement('div');
                        packetContainer.className = 'flex items-center justify-center space-x-2';
                        
                        const packetCheckbox = document.createElement('input');
                        packetCheckbox.type = 'checkbox';
                        packetCheckbox.className = 'packet-checkbox h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded';
                        packetCheckbox.setAttribute('data-id', contest.contest.id);
                        packetCheckbox.setAttribute('data-type', 'contest');
                        
                        if (contest.contest.downloaded) {
                            packetCheckbox.disabled = true;
                            packetCheckbox.title = 'Already downloaded';
                            packetCheckbox.checked = true;
                        }
                        
                        packetCheckbox.addEventListener('change', function() {
                            updateRowCheckboxState(row);
                            updateSelectAllCheckboxes();
                        });
                        
                        packetContainer.appendChild(packetCheckbox);
                        
                        packetCell.appendChild(packetContainer);
                    } else {
                        packetCell.textContent = 'N/A';
                        packetCell.classList.add('text-gray-800', 'dark:text-gray-200');
                    }
                    
                    row.appendChild(packetCell);
                    
                    // Create the data file checkbox cell
                    const dataFileCell = document.createElement('td');
                    dataFileCell.className = 'px-3 py-4 whitespace-nowrap text-center';
                    
                    if (contest.data_file) {
                        const dataFileContainer = document.createElement('div');
                        dataFileContainer.className = 'flex items-center justify-center space-x-2';
                        
                        const dataFileCheckbox = document.createElement('input');
                        dataFileCheckbox.type = 'checkbox';
                        dataFileCheckbox.className = 'datafile-checkbox h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded';
                        dataFileCheckbox.setAttribute('data-id', contest.data_file.id);
                        dataFileCheckbox.setAttribute('data-type', 'data_file');
                        
                        if (contest.data_file.downloaded) {
                            dataFileCheckbox.disabled = true;
                            dataFileCheckbox.title = 'Already downloaded';
                            dataFileCheckbox.checked = true;
                        }
                        
                        dataFileCheckbox.addEventListener('change', function() {
                            updateRowCheckboxState(row);
                            updateSelectAllCheckboxes();
                        });
                        
                        dataFileContainer.appendChild(dataFileCheckbox);
                        
                        dataFileCell.appendChild(dataFileContainer);
                    } else {
                        dataFileCell.textContent = 'N/A';
                        dataFileCell.classList.add('text-gray-800', 'dark:text-gray-200');
                    }
                    
                    row.appendChild(dataFileCell);
                    
                    // Create the status cell
                    const statusCell = document.createElement('td');
                    statusCell.className = 'px-3 py-4 whitespace-nowrap';
                    
                    const statusBadge = document.createElement('span');
                    
                    if (allDownloaded) {
                        statusBadge.className = 'status-badge status-downloaded';
                        statusBadge.textContent = 'All Downloaded';
                    } else if (partiallyDownloaded) {
                        statusBadge.className = 'status-badge status-partial';
                        statusBadge.textContent = 'Partially Downloaded';
                    } else {
                        statusBadge.className = 'status-badge status-pending';
                        statusBadge.textContent = 'Not Downloaded';
                    }
                    
                    statusCell.appendChild(statusBadge);
                    row.appendChild(statusCell);
                    
                    // Add row to table
                    contestsTableBody.appendChild(row);
                });
                
                // Update select all checkbox states
                updateSelectAllCheckboxes();
                
                // Update sort header UI
                updateSortHeaderUI();
            })
            .catch(error => {
                console.error('Error loading contests:', error);
                contestsTableBody.innerHTML = `
                    <tr>
                        <td colspan="7" class="px-6 py-4 text-center text-red-500">
                            Error loading contests. Please try again.
                        </td>
                    </tr>
                `;
            });
    }
    
    // Sort the data based on current sort settings
    function sortData(data) {
        data.sort((a, b) => {
            let valA, valB;
            
            // Get values based on sort column
            switch (currentSortBy) {
                case 'subject':
                    valA = a.subject.toLowerCase();
                    valB = b.subject.toLowerCase();
                    break;
                    
                case 'level':
                    valA = a.level.toLowerCase();
                    valB = b.level.toLowerCase();
                    break;
                    
                case 'year':
                    valA = a.year;
                    valB = b.year;
                    break;
                    
                case 'status':
                    // Determine status values for sorting (3 = all downloaded, 2 = partially, 1 = none)
                    const statusOrderMap = {
                        'all_downloaded': 3,
                        'partially_downloaded': 2,
                        'not_downloaded': 1
                    };
                    
                    // For item A
                    valA = 1; // Default to not downloaded
                    if (a.contest && a.contest.downloaded) {
                        if (!a.data_file || a.data_file.downloaded) {
                            valA = 3; // All downloaded
                        } else {
                            valA = 2; // Partially downloaded
                        }
                    } else if (a.data_file && a.data_file.downloaded) {
                        valA = 2; // Partially downloaded
                    }
                    
                    // For item B
                    valB = 1; // Default to not downloaded
                    if (b.contest && b.contest.downloaded) {
                        if (!b.data_file || b.data_file.downloaded) {
                            valB = 3; // All downloaded
                        } else {
                            valB = 2; // Partially downloaded
                        }
                    } else if (b.data_file && b.data_file.downloaded) {
                        valB = 2; // Partially downloaded
                    }
                    break;
                    
                default:
                    valA = a.year;
                    valB = b.year;
            }
            
            // Compare values based on sort direction
            if (currentSortDir === 'asc') {
                return valA > valB ? 1 : valA < valB ? -1 : 0;
            } else {
                return valA < valB ? 1 : valA > valB ? -1 : 0;
            }
        });
        
        return data;
    }
    
    // Update sort header UI to show current sort state
    function updateSortHeaderUI() {
        // Reset all headers first
        document.querySelectorAll('.sortable').forEach(header => {
            header.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add current sort class to the active header
        const activeHeader = document.querySelector(`.sortable[data-sort-by="${currentSortBy}"]`);
        if (activeHeader) {
            activeHeader.classList.add(`sort-${currentSortDir}`);
        }
    }
    
    // Initialize sorting functionality
    function initializeSorting() {
        document.querySelectorAll('.sortable').forEach(header => {
            header.addEventListener('click', function() {
                const sortBy = this.getAttribute('data-sort-by');
                
                // If clicking on the same column, toggle direction
                if (sortBy === currentSortBy) {
                    currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
                } else {
                    // New column, set to default sort direction
                    currentSortBy = sortBy;
                    currentSortDir = 'asc';
                }
                
                // Reload data with new sort
                loadContests();
            });
        });
    }
    
    // Update row checkbox state based on packet and data file checkboxes
    function updateRowCheckboxState(row) {
        const rowCheckbox = row.querySelector('.row-checkbox');
        const packetCheckbox = row.querySelector('.packet-checkbox');
        const dataFileCheckbox = row.querySelector('.datafile-checkbox');
        
        const packetChecked = packetCheckbox && !packetCheckbox.disabled && packetCheckbox.checked;
        const dataFileChecked = dataFileCheckbox && !dataFileCheckbox.disabled && dataFileCheckbox.checked;
        const packetExists = packetCheckbox && !packetCheckbox.disabled;
        const dataFileExists = dataFileCheckbox && !dataFileCheckbox.disabled;
        
        if (packetExists || dataFileExists) {
            if (packetExists && dataFileExists) {
                // Both file types exist
                rowCheckbox.checked = packetChecked && dataFileChecked;
                rowCheckbox.indeterminate = (packetChecked || dataFileChecked) && !(packetChecked && dataFileChecked);
            } else {
                // Only one file type exists
                rowCheckbox.checked = packetChecked || dataFileChecked;
                rowCheckbox.indeterminate = false;
            }
        } else {
            // No selectable files
            rowCheckbox.checked = false;
            rowCheckbox.indeterminate = false;
            rowCheckbox.disabled = true;
        }
    }
    
    // Update all select-all checkbox states
    function updateSelectAllCheckboxes() {
        // Update the main select all checkbox
        const rowCheckboxes = document.querySelectorAll('.row-checkbox:not(:disabled)');
        const checkedRowCheckboxes = document.querySelectorAll('.row-checkbox:checked:not(:disabled)');
        const indeterminateRowCheckboxes = Array.from(document.querySelectorAll('.row-checkbox:not(:disabled)'))
                                            .filter(cb => cb.indeterminate);
        
        if (rowCheckboxes.length === 0) {
            selectAllCheckbox.disabled = true;
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.disabled = false;
            selectAllCheckbox.checked = checkedRowCheckboxes.length > 0 && 
                                       checkedRowCheckboxes.length === rowCheckboxes.length;
            selectAllCheckbox.indeterminate = (checkedRowCheckboxes.length > 0 || indeterminateRowCheckboxes.length > 0) && 
                                            checkedRowCheckboxes.length < rowCheckboxes.length;
        }
        
        // Update the packets select all checkbox
        const packetCheckboxes = document.querySelectorAll('.packet-checkbox:not(:disabled)');
        const checkedPacketCheckboxes = document.querySelectorAll('.packet-checkbox:checked:not(:disabled)');
        
        if (packetCheckboxes.length === 0) {
            selectAllPacketsCheckbox.disabled = true;
            selectAllPacketsCheckbox.checked = false;
        } else {
            selectAllPacketsCheckbox.disabled = false;
            selectAllPacketsCheckbox.checked = checkedPacketCheckboxes.length > 0 && 
                                            checkedPacketCheckboxes.length === packetCheckboxes.length;
            selectAllPacketsCheckbox.indeterminate = checkedPacketCheckboxes.length > 0 && 
                                                  checkedPacketCheckboxes.length < packetCheckboxes.length;
        }
        
        // Update the data files select all checkbox
        const dataFileCheckboxes = document.querySelectorAll('.datafile-checkbox:not(:disabled)');
        const checkedDataFileCheckboxes = document.querySelectorAll('.datafile-checkbox:checked:not(:disabled)');
        
        if (dataFileCheckboxes.length === 0) {
            selectAllDatafilesCheckbox.disabled = true;
            selectAllDatafilesCheckbox.checked = false;
        } else {
            selectAllDatafilesCheckbox.disabled = false;
            selectAllDatafilesCheckbox.checked = checkedDataFileCheckboxes.length > 0 && 
                                              checkedDataFileCheckboxes.length === dataFileCheckboxes.length;
            selectAllDatafilesCheckbox.indeterminate = checkedDataFileCheckboxes.length > 0 && 
                                                     checkedDataFileCheckboxes.length < dataFileCheckboxes.length;
        }
        
        // Enable/disable download selected button based on any checkbox being checked
        const anyCheckboxChecked = document.querySelectorAll('.packet-checkbox:checked:not(:disabled), .datafile-checkbox:checked:not(:disabled)').length > 0;
        downloadSelectedBtn.disabled = !anyCheckboxChecked;
    }
    
    // Handle main select all checkbox
    selectAllCheckbox.addEventListener('change', function() {
        const rowCheckboxes = document.querySelectorAll('.row-checkbox:not(:disabled)');
        
        rowCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
            
            // Also update packet and data file checkboxes
            const row = checkbox.closest('tr');
            const packetCheckbox = row.querySelector('.packet-checkbox:not(:disabled)');
            const dataFileCheckbox = row.querySelector('.datafile-checkbox:not(:disabled)');
            
            if (packetCheckbox) packetCheckbox.checked = selectAllCheckbox.checked;
            if (dataFileCheckbox) dataFileCheckbox.checked = selectAllCheckbox.checked;
        });
        
        updateSelectAllCheckboxes();
    });
    
    // Handle packet select all checkbox
    selectAllPacketsCheckbox.addEventListener('change', function() {
        const packetCheckboxes = document.querySelectorAll('.packet-checkbox:not(:disabled)');
        
        packetCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllPacketsCheckbox.checked;
            
            // Update row checkbox state
            const row = checkbox.closest('tr');
            updateRowCheckboxState(row);
        });
        
        updateSelectAllCheckboxes();
    });
    
    // Handle data file select all checkbox
    selectAllDatafilesCheckbox.addEventListener('change', function() {
        const dataFileCheckboxes = document.querySelectorAll('.datafile-checkbox:not(:disabled)');
        
        dataFileCheckboxes.forEach(checkbox => {
            checkbox.checked = selectAllDatafilesCheckbox.checked;
            
            // Update row checkbox state
            const row = checkbox.closest('tr');
            updateRowCheckboxState(row);
        });
        
        updateSelectAllCheckboxes();
    });
    
    // Handle reload cache button
    reloadCacheBtn.addEventListener('click', function() {
        // Disable button while processing
        this.disabled = true;
        this.innerHTML = '<span class="spinner mr-1"></span> Reloading...';
        
        fetch('/refresh-cache')
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                this.textContent = 'Reload Cache';
                
                if (data.success) {
                    updateCacheStats();
                    loadContests(); // Reload the contest list to reflect the updated cache
                } else {
                    this.textContent = 'Reload Cache';
                    console.error('Error reloading cache:', data.error);
                }
            })
            .catch(error => {
                this.disabled = false;
                this.textContent = 'Reload Cache';
                console.error('Error reloading cache:', error);
            });
    });
    
    // Handle reset cache button
    resetCacheBtn.addEventListener('click', function() {
        if (!confirm('Are you sure you want to reset the cache? This will forget all downloaded files (but won\'t delete the actual files).')) {
            return;
        }
        
        // Disable button while processing
        this.disabled = true;
        this.innerHTML = '<span class="spinner mr-1"></span> Resetting...';
        
        fetch('/reset-cache')
            .then(response => response.json())
            .then(data => {
                this.disabled = false;
                this.textContent = 'Reset Cache';
                
                if (data.success) {
                    updateCacheStats();
                    loadContests(); // Reload the contest list to reflect the updated cache
                } else {
                    this.textContent = 'Reset Cache';
                    console.error('Error resetting cache:', data.error);
                }
            })
            .catch(error => {
                this.disabled = false;
                this.textContent = 'Reset Cache';
                console.error('Error resetting cache:', error);
            });
    });
    
    // Handle filter changes
    downloadedFilter.addEventListener('change', loadContests);
    
    // Handle download selected button
    downloadSelectedBtn.addEventListener('click', function() {
        const selectedItems = Array.from(
            document.querySelectorAll('.packet-checkbox:checked:not(:disabled), .datafile-checkbox:checked:not(:disabled)')
        ).map(checkbox => ({
            id: checkbox.getAttribute('data-id'),
            type: checkbox.getAttribute('data-type')
        }));
        
        if (selectedItems.length === 0) return;
        
        // Setup download queue
        const queue = [...selectedItems];
        const activeDownloads = new Set();
        const MAX_CONCURRENT = 4;
        
        // Start initial batch of downloads
        startNextDownloads();
        
        // Function to start the next batch of downloads
        function startNextDownloads() {
            // Start new downloads until we reach MAX_CONCURRENT or run out of items
            while (activeDownloads.size < MAX_CONCURRENT && queue.length > 0) {
                const item = queue.shift();
                activeDownloads.add(item.id);
                
                startDownload(item, () => {
                    // On completion, remove from active and start next
                    activeDownloads.delete(item.id);
                    if (queue.length > 0) {
                        startNextDownloads();
                    } else if (activeDownloads.size === 0) {
                        // All downloads complete, refresh the UI
                        updateCacheStats();
                        setTimeout(() => {
                            loadContests();
                        }, 1000);
                    }
                });
            }
        }
    });
    
    // Start a single download
    function startDownload(item, onComplete) {
        const itemId = item.id;
        const itemType = item.type;
        
        // Find the checkbox for this ID to get the row and cell for status updates
        const checkbox = document.querySelector(`.packet-checkbox[data-id="${itemId}"], .datafile-checkbox[data-id="${itemId}"]`);
        if (!checkbox) {
            if (onComplete) onComplete();
            return;
        }
        
        const row = checkbox.closest('tr');
        const isPacket = checkbox.classList.contains('packet-checkbox');
        const cell = isPacket ? 
            row.querySelector('td:nth-child(5)') : // Packet cell
            row.querySelector('td:nth-child(6)');  // Data file cell
        
        // Store original content to restore if download fails
        const originalContent = cell.innerHTML;
        
        // Update UI to show downloading
        cell.innerHTML = `
            <div class="flex justify-center">
                <span class="spinner mr-1"></span>
                <span class="text-xs text-gray-800 dark:text-gray-200">Downloading...</span>
            </div>
        `;
        
        // Start the download
        fetch(`/download/${itemId}/${itemType}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Update the cell to show downloaded
                const downloadedCheckbox = document.createElement('input');
                downloadedCheckbox.type = 'checkbox';
                downloadedCheckbox.className = isPacket ? 
                    'packet-checkbox h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded' :
                    'datafile-checkbox h-5 w-5 text-emerald-600 focus:ring-emerald-500 border-gray-300 rounded';
                downloadedCheckbox.setAttribute('data-id', itemId);
                downloadedCheckbox.setAttribute('data-type', itemType);
                downloadedCheckbox.disabled = true;
                downloadedCheckbox.checked = true;
                downloadedCheckbox.title = 'Already downloaded';
                
                const container = document.createElement('div');
                container.className = 'flex items-center justify-center';
                container.appendChild(downloadedCheckbox);
                
                cell.innerHTML = '';
                cell.appendChild(container);
                
                // Also update the status cell
                updateRowStatus(row);
                
                // Complete this download
                if (onComplete) onComplete();
            })
            .catch(error => {
                console.error(`Error downloading file ${itemId}:`, error);
                // Restore original content on error
                cell.innerHTML = originalContent;
                
                // Show error message
                const errorMsg = document.createElement('div');
                errorMsg.className = 'text-xs text-red-500 mt-1';
                errorMsg.textContent = 'Download failed';
                cell.appendChild(errorMsg);
                
                // Hide error after a few seconds
                setTimeout(() => {
                    if (cell.contains(errorMsg)) {
                        cell.removeChild(errorMsg);
                    }
                }, 3000);
                
                // Complete this download (even though it failed)
                if (onComplete) onComplete();
            });
    }
    
    // Helper function to update row status
    function updateRowStatus(row) {
        const statusCell = row.querySelector('td:nth-child(7)'); // Status cell
        const packetCheckbox = row.querySelector('.packet-checkbox');
        const dataFileCheckbox = row.querySelector('.datafile-checkbox');
        
        // Determine combined status
        let allDownloaded = packetCheckbox && packetCheckbox.disabled;
        if (dataFileCheckbox) {
            allDownloaded = allDownloaded && dataFileCheckbox.disabled;
        } else {
            // If there's no data file checkbox, consider it "all downloaded" if packet is downloaded
            allDownloaded = packetCheckbox && packetCheckbox.disabled;
        }
        
        let partiallyDownloaded = (packetCheckbox && packetCheckbox.disabled) || 
                                  (dataFileCheckbox && dataFileCheckbox.disabled);
        
        let statusBadge = document.createElement('span');
        
        if (allDownloaded) {
            statusBadge.className = 'status-badge status-downloaded';
            statusBadge.textContent = 'All Downloaded';
        } else if (partiallyDownloaded) {
            statusBadge.className = 'status-badge status-partial';
            statusBadge.textContent = 'Partially Downloaded';
        } else {
            statusBadge.className = 'status-badge status-pending';
            statusBadge.textContent = 'Not Downloaded';
        }
        
        statusCell.innerHTML = '';
        statusCell.appendChild(statusBadge);
    }
    
    // Initialize multiselect dropdowns
    initializeMultiselect();
    
    // Initialize sorting functionality
    initializeSorting();
    
    // Initial load
    loadContests();
    updateCacheStats();
    
    // Refresh cache after it's loaded
    setTimeout(() => {
        fetch('/refresh-cache')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateCacheStats();
                    loadContests();
                }
            })
            .catch(error => {
                console.error('Error refreshing cache on load:', error);
            });
    }, 1000);
}); 
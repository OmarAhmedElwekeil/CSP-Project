// Schedule page logic
Auth.requireAuth();

let allLevels = [];
let allSections = [];
let allGroups = [];
let allRooms = [];
let scheduleData = [];

const isAdmin = Auth.isAdmin();

async function init() {
    try {
        showLoading(true);
        if (isAdmin) {
            document.getElementById('admin-controls').style.display = 'block';
        }
        [allLevels, allSections, allGroups, allRooms] = await Promise.all([
            API.get(Endpoints.levels), API.get(Endpoints.sections), 
            API.get(Endpoints.groups), API.get(Endpoints.rooms)
        ]);
        populateFilters();
    } catch (error) {
        showNotification('Failed to initialize: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function populateFilters() {
    const levelSelect = document.getElementById('filter-level');
    allLevels.forEach(level => {
        const option = document.createElement('option');
        option.value = level.level_id;
        option.textContent = level.level_name;
        levelSelect.appendChild(option);
    });
    const roomSelect = document.getElementById('filter-room');
    allRooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.room_id;
        option.textContent = room.room_number + ' (' + room.room_type + ')';
        roomSelect.appendChild(option);
    });
}

function onLevelChange() {
    const levelId = parseInt(document.getElementById('filter-level').value);
    const sectionSelect = document.getElementById('filter-section');
    sectionSelect.innerHTML = '<option value="">All Sections</option>';
    document.getElementById('filter-group').innerHTML = '<option value="">All Groups</option>';
    if (levelId) {
        allSections.filter(s => s.level_id === levelId).forEach(section => {
            const option = document.createElement('option');
            option.value = section.section_id;
            option.textContent = `Section ${section.section_number}`;
            sectionSelect.appendChild(option);
        });
    }
}

function onSectionChange() {
    const sectionId = parseInt(document.getElementById('filter-section').value);
    const groupSelect = document.getElementById('filter-group');
    groupSelect.innerHTML = '<option value="">All Groups</option>';
    if (sectionId) {
        allGroups.filter(g => g.section_id === sectionId).forEach(group => {
            const option = document.createElement('option');
            option.value = group.group_id;
            option.textContent = `Group ${group.group_number}`;
            groupSelect.appendChild(option);
        });
    }
}

async function loadSchedule() {
    try {
        showLoading(true);
        const params = new URLSearchParams();
        const levelId = document.getElementById('filter-level').value;
        const sectionId = document.getElementById('filter-section').value;
        const groupId = document.getElementById('filter-group').value;
        const roomId = document.getElementById('filter-room').value;
        if (levelId) params.append('level_id', levelId);
        if (sectionId) params.append('section_id', sectionId);
        if (groupId) params.append('group_id', groupId);
        if (roomId) params.append('room_id', roomId);
        const query = params.toString() ? '?' + params.toString() : '';
        scheduleData = await API.get(Endpoints.getSchedule + query);
        renderSchedule();
    } catch (error) {
        showNotification('Failed to load schedule: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function renderSchedule() {
    const display = document.getElementById('schedule-display');
    if (!scheduleData || scheduleData.length === 0) {
        display.innerHTML = '<p class="text-muted text-center">No schedule data available.</p>';
        return;
    }
    
    // Build hierarchical structure: Level -> Group -> Section
    const hierarchy = {};
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday'];
    
    // BLOCK-TO-ROW MAPPING: Backend uses blocks 0-7, Frontend has 11 rows (8 slots + 3 breaks)
    // Block 0, 1 → Row 0, 1
    // Row 2 = BREAK
    // Block 2, 3 → Row 3, 4
    // Row 5 = BREAK
    // Block 4, 5 → Row 6, 7
    // Row 8 = BREAK
    // Block 6, 7 → Row 9, 10
    const blockToRowMap = {
        0: 0, 1: 1,   // First pair
        2: 3, 3: 4,   // Second pair (after break at row 2)
        4: 6, 5: 7,   // Third pair (after break at row 5)
        6: 9, 7: 10   // Fourth pair (after break at row 8)
    };
    
    // Define 11 table rows: 8 time slots + 3 break rows
    const tableRows = [
        { type: 'slot', block: 0, label: '09:00 AM – 09:45 AM', start: '09:00', end: '09:45' },
        { type: 'slot', block: 1, label: '09:45 AM – 10:30 AM', start: '09:45', end: '10:30' },
        { type: 'break', label: 'Break (10:30 AM – 10:45 AM)' },
        { type: 'slot', block: 2, label: '10:45 AM – 11:30 AM', start: '10:45', end: '11:30' },
        { type: 'slot', block: 3, label: '11:30 AM – 12:15 PM', start: '11:30', end: '12:15' },
        { type: 'break', label: 'Break (12:15 PM – 12:30 PM)' },
        { type: 'slot', block: 4, label: '12:30 PM – 01:15 PM', start: '12:30', end: '13:15' },
        { type: 'slot', block: 5, label: '01:15 PM – 02:00 PM', start: '13:15', end: '14:00' },
        { type: 'break', label: 'Break (02:00 PM – 02:15 PM)' },
        { type: 'slot', block: 6, label: '02:15 PM – 03:00 PM', start: '14:15', end: '15:00' },
        { type: 'slot', block: 7, label: '03:00 PM – 03:45 PM', start: '15:00', end: '15:45' }
    ];
    
    // Build hierarchical structure from ACTUAL database sections
    // This ensures we show ALL sections, not just ones with schedules
    // First, build the complete hierarchy from database
    allSections.forEach(section => {
        // Find the group and level for this section
        const group = allGroups.find(g => g.group_id === section.group_id);
        if (!group) return;
        
        const level = allLevels.find(l => l.level_id === group.level_id);
        if (!level) return;
        
        const levelName = level.level_name;
        const groupNum = group.group_number;
        const sectionNum = section.section_number;
        
        if (!hierarchy[levelName]) hierarchy[levelName] = {};
        if (!hierarchy[levelName][groupNum]) hierarchy[levelName][groupNum] = new Set();
        hierarchy[levelName][groupNum].add(sectionNum);
    });
    
    // Convert sets to sorted arrays
    Object.keys(hierarchy).forEach(level => {
        Object.keys(hierarchy[level]).forEach(group => {
            hierarchy[level][group] = Array.from(hierarchy[level][group]).sort((a, b) => a - b);
        });
    });
    
    // Calculate column spans
    const levelSpans = {};
    Object.keys(hierarchy).sort().forEach(level => {
        let levelCols = 0;
        Object.keys(hierarchy[level]).sort((a, b) => a - b).forEach(group => {
            levelCols += hierarchy[level][group].length;
        });
        levelSpans[level] = levelCols;
    });
    
    // Build table
    let html = '<table class="schedule-table hierarchy-grid"><thead>';
    
    // Header Row 1: Levels
    html += '<tr class="level-header">';
    html += '<th rowspan="3" class="day-header">Day</th>';
    html += '<th rowspan="3" class="time-header">Time Slot</th>';
    Object.keys(hierarchy).sort().forEach(level => {
        html += `<th colspan="${levelSpans[level]}" class="level-cell">${level}</th>`;
    });
    html += '</tr>';
    
    // Header Row 2: Groups
    html += '<tr class="group-header">';
    Object.keys(hierarchy).sort().forEach(level => {
        Object.keys(hierarchy[level]).sort((a, b) => a - b).forEach(group => {
            const sectionCount = hierarchy[level][group].length;
            html += `<th colspan="${sectionCount}" class="group-cell">Group ${group}</th>`;
        });
    });
    html += '</tr>';
    
    // Header Row 3: Sections (Show all sections individually)
    html += '<tr class="section-header">';
    Object.keys(hierarchy).sort().forEach(level => {
        Object.keys(hierarchy[level]).sort((a, b) => a - b).forEach(group => {
            hierarchy[level][group].forEach(section => {
                // Display section number (section 0 still gets shown as a column)
                const sectionLabel = `Sec ${section}`;
                html += `<th class="section-cell">${sectionLabel}</th>`;
            });
        });
    });
    html += '</tr></thead><tbody>';
    
    // Track which cells are already occupied by rowspan sessions
    // Key format: "day-visualRow-level-group-section"
    const occupiedCells = new Set();
    
    // Body: Days and Table Rows (11 rows per day: 8 slots + 3 breaks)
    days.forEach((day, dayIndex) => {
        tableRows.forEach((row, visualRowIndex) => {
            const isFirstRow = visualRowIndex === 0;
            const isBreak = row.type === 'break';
            const rowClass = isFirstRow ? 'time-row day-start' : (isBreak ? 'break-row' : 'time-row');
            
            html += `<tr class="${rowClass}">`;
            
            // Day cell (spans all 11 rows)
            if (isFirstRow) {
                html += `<td rowspan="11" class="day-cell"><div class="day-label">${day}</div></td>`;
            }
            
            // Time slot cell
            html += `<td class="time-slot-cell">`;
            html += `<div class="time-label">${row.label}</div></td>`;
            
            // Data cells with COLSPAN ALGORITHM for Group Lectures
            Object.keys(hierarchy).sort().forEach(level => {
                Object.keys(hierarchy[level]).sort((a, b) => a - b).forEach(group => {
                    const groupSections = hierarchy[level][group];
                    let sectionIndex = 0;  // Track which section we're on
                    
                    while (sectionIndex < groupSections.length) {
                        const section = groupSections[sectionIndex];
                        const cellKey = `${day}-${visualRowIndex}-${level}-${group}-${section}`;
                        
                        // Skip if this cell is occupied by a rowspan from previous row
                        if (occupiedCells.has(cellKey)) {
                            sectionIndex++;
                            continue;
                        }
                        
                        // For break rows, show empty cells
                        if (isBreak) {
                            html += '<td class="schedule-cell break-cell"></td>';
                            sectionIndex++;
                            continue;
                        }
                        
                        // Check for GROUP LECTURE (applies to all sections in group)
                        const groupLecture = scheduleData.find(s => {
                            return s.day === day && 
                                   s.level_name === level && 
                                   s.group_number == group && 
                                   s.session_type === 'LECTURE' &&
                                   s.start_block === row.block;
                        });
                        
                        if (groupLecture) {
                            // RENDER GROUP LECTURE with colspan = number of sections
                            const colspan = groupSections.length;
                            const durationBlocks = groupLecture.duration_blocks || 2;
                            const rowspan = durationBlocks === 2 ? 2 : 1;
                            
                            // Mark all covered cells as occupied
                            if (rowspan === 2) {
                                let nextSlotRow = -1;
                                for (let i = visualRowIndex + 1; i < tableRows.length; i++) {
                                    if (tableRows[i].type === 'slot') {
                                        nextSlotRow = i;
                                        break;
                                    }
                                }
                                if (nextSlotRow !== -1) {
                                    groupSections.forEach(sec => {
                                        const nextCellKey = `${day}-${nextSlotRow}-${level}-${group}-${sec}`;
                                        occupiedCells.add(nextCellKey);
                                    });
                                }
                            }
                            
                            const location = groupLecture.building_name === 'Hall' 
                                ? groupLecture.room_number 
                                : groupLecture.building_name + ' / ' + groupLecture.room_number;
                            
                            html += `<td class="schedule-cell lecture" colspan="${colspan}" rowspan="${rowspan}">`;
                            html += `<div class="schedule-session lecture">`;
                            html += '<div class="session-content">';
                            html += `<div class="course-title">${groupLecture.course_code} . ${groupLecture.course_name}</div>`;
                            html += `<div class="session-type">Lec</div>`;
                            html += `<div class="session-instructor">${groupLecture.instructor_or_ta}</div>`;
                            html += `<div class="session-location">${location}</div>`;
                            html += '</div></div></td>';
                            
                            // Skip all sections in this group (covered by colspan)
                            sectionIndex = groupSections.length;
                        } else {
                            // Check for SECTION-SPECIFIC class (Lab or Tutorial)
                            const sectionSession = scheduleData.find(s => {
                                return s.day === day && 
                                       s.level_name === level && 
                                       s.group_number == group && 
                                       s.section_number == section &&  // Match exact section number
                                       s.session_type !== 'LECTURE' &&
                                       s.start_block === row.block;
                            });
                            
                            if (sectionSession) {
                                const durationBlocks = sectionSession.duration_blocks || 2;
                                const rowspan = durationBlocks === 2 ? 2 : 1;
                                
                                // Mark future cells as occupied if rowspan > 1
                                if (rowspan === 2) {
                                    let nextSlotRow = -1;
                                    for (let i = visualRowIndex + 1; i < tableRows.length; i++) {
                                        if (tableRows[i].type === 'slot') {
                                            nextSlotRow = i;
                                            break;
                                        }
                                    }
                                    if (nextSlotRow !== -1) {
                                        const nextCellKey = `${day}-${nextSlotRow}-${level}-${group}-${section}`;
                                        occupiedCells.add(nextCellKey);
                                    }
                                }
                                
                                const location = sectionSession.building_name === 'Hall' 
                                    ? sectionSession.room_number 
                                    : sectionSession.building_name + ' / ' + sectionSession.room_number;
                                
                                const sessionTypeLabel = sectionSession.session_type === 'LAB' ? 'Lab' : 'Tut';
                                
                                html += `<td class="schedule-cell ${sectionSession.session_type.toLowerCase()}" rowspan="${rowspan}">`;
                                html += `<div class="schedule-session ${sectionSession.session_type.toLowerCase()}">`;
                                html += '<div class="session-content">';
                                html += `<div class="course-title">${sectionSession.course_code} . ${sectionSession.course_name}</div>`;
                                html += `<div class="session-type">${sessionTypeLabel}</div>`;
                                html += `<div class="session-instructor">${sectionSession.instructor_or_ta}</div>`;
                                html += `<div class="session-location">${location}</div>`;
                                html += '</div></div></td>';
                            } else {
                                html += '<td class="schedule-cell empty-cell"></td>';
                            }
                            
                            sectionIndex++;
                        }
                    }
                });
            });
            html += '</tr>';
        });
        
        // Clear occupied cells after each day
        occupiedCells.clear();
    });
    
    html += '</tbody></table>';
    display.innerHTML = html;
}

function getDuration(startTime, endTime) {
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    return (endHour * 60 + endMin) - (startHour * 60 + startMin);
}

async function generateSchedule() {
    try {
        showLoading(true);
        const result = await API.post(Endpoints.generateSchedule, {});
        if (result.success) {
            showNotification('Schedule generated!', 'success');
            await loadSchedule();
        }
    } catch (error) {
        showNotification('Failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function exportSchedule() {
    try {
        showLoading(true);
        await API.downloadFile(Endpoints.exportSchedule, 'schedule.xlsx');
        showNotification('Exported!', 'success');
    } catch (error) {
        showNotification('Failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function importSchedule() {
    const file = document.getElementById('import-file').files[0];
    try {
        showLoading(true);
        await API.uploadFile(Endpoints.importSchedule, file);
        showNotification('Imported!', 'success');
        await loadSchedule();
    } catch (error) {
        showNotification('Failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
        document.getElementById('import-file').value = '';
    }
}

init();

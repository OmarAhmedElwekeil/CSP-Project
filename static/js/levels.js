// Levels page logic
Auth.requireAdmin();

let allLevels = [];
let allGroups = [];
let allSections = [];
let selectedLevelId = null;
let selectedGroupId = null;
let editingLevelId = null;

const levelModal = new Modal('level-modal-overlay');

// Load all data
async function loadAllData() {
    try {
        showLoading(true);
        [allLevels, allGroups, allSections] = await Promise.all([
            API.get(Endpoints.levels),
            API.get(Endpoints.groups),
            API.get(Endpoints.sections)
        ]);
        renderLevelsTable();
    } catch (error) {
        showNotification('Failed to load data: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Render levels table
function renderLevelsTable() {
    const columns = [
        { key: 'level_name', label: 'Level Name' },
        { key: 'specialization', label: 'Specialization', 
          format: (value) => value || '<span class="text-muted">General</span>' 
        },
        { key: 'num_sections', label: 'Groups' },
        { key: 'num_groups_per_section', label: 'Sections/Group' },
        { key: 'total_students', label: 'Total Students' }
    ];

    const actions = [
        {
            label: 'View Groups',
            className: 'btn-primary',
            handler: (level) => viewLevelGroups(level)
        },
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (level) => editLevel(level)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (level) => deleteLevel(level.level_id)
        }
    ];

    const table = createTable(allLevels, columns, actions);
    document.getElementById('levels-table').innerHTML = '';
    document.getElementById('levels-table').appendChild(table);
}

// Render groups table (middle level)
function renderGroupsTable() {
    const groupsForLevel = allGroups.filter(g => g.level_id === selectedLevelId);
    
    const columns = [
        { key: 'group_number', label: 'Group',
          format: (value) => `Group ${value}`
        },
        { key: 'num_students', label: 'Students' },
        { 
            key: 'sections_count', 
            label: 'Sections',
            format: (value, group) => {
                const count = allSections.filter(s => s.group_id === group.group_id).length;
                return `<span class="badge badge-primary">${count}</span>`;
            }
        }
    ];

    const actions = [
        {
            label: 'View Sections',
            className: 'btn-primary',
            handler: (group) => viewGroupSections(group)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (group) => deleteGroup(group.group_id)
        }
    ];

    const table = createTable(groupsForLevel, columns, actions);
    document.getElementById('groups-table').innerHTML = '';
    document.getElementById('groups-table').appendChild(table);
}

// Render sections table (bottom level - no drill-down)
function renderSectionsTable() {
    const sectionsForGroup = allSections.filter(s => s.group_id === selectedGroupId);
    
    const columns = [
        { key: 'section_number', label: 'Section', 
          format: (value) => `Section ${value}`
        },
        { key: 'num_students', label: 'Students' }
    ];

    const actions = [
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (section) => deleteSection(section.section_id)
        }
    ];

    const table = createTable(sectionsForGroup, columns, actions);
    document.getElementById('sections-table').innerHTML = '';
    document.getElementById('sections-table').appendChild(table);
}

// View level groups
function viewLevelGroups(level) {
    selectedLevelId = level.level_id;
    document.getElementById('selected-level-name').textContent = level.level_name;
    document.getElementById('groups-section').classList.remove('hidden');
    document.getElementById('sections-section').classList.add('hidden');
    renderGroupsTable();
    document.getElementById('groups-section').scrollIntoView({ behavior: 'smooth' });
}

// View group sections
function viewGroupSections(group) {
    selectedGroupId = group.group_id;
    document.getElementById('selected-group-name').textContent = `Group ${group.group_number}`;
    document.getElementById('sections-section').classList.remove('hidden');
    renderSectionsTable();
    document.getElementById('sections-section').scrollIntoView({ behavior: 'smooth' });
}

// Level CRUD
function openLevelModal() {
    editingLevelId = null;
    levelModal.setTitle('Add Level');
    clearForm('level-form');
    levelModal.open();
}

function editLevel(level) {
    editingLevelId = level.level_id;
    levelModal.setTitle('Edit Level');
    
    // Extract level number from level_name (e.g., "Level 1" -> 1, "Level 3 - a" -> 3)
    const levelNumberMatch = level.level_name.match(/Level (\d)/);
    const levelData = {
        level_id: level.level_id,
        level_number: levelNumberMatch ? parseInt(levelNumberMatch[1]) : '',
        specialization: level.specialization || '',
        num_sections: level.num_sections,
        num_groups_per_section: level.num_groups_per_section,
        total_students: level.total_students
    };
    
    setFormData('level-form', levelData);
    levelModal.open();
}

async function saveLevel() {
    if (!validateForm('level-form')) return;

    const data = getFormData('level-form');
    delete data.level_id;
    delete data.level_name; // Remove computed field
    
    // Convert empty specialization to null for proper validation
    if (data.specialization === '' || !data.specialization) {
        data.specialization = null;
    }

    try {
        showLoading(true);
        if (editingLevelId) {
            await API.put(Endpoints.level(editingLevelId), data);
            showNotification('Level updated successfully', 'success');
        } else {
            await API.post(Endpoints.levels, data);
            showNotification('Level created successfully', 'success');
        }
        levelModal.close();
        await loadAllData();
        
        // Re-render currently visible tables and update titles
        if (selectedLevelId) {
            const updatedLevel = allLevels.find(l => l.level_id === selectedLevelId);
            if (updatedLevel) {
                document.getElementById('selected-level-name').textContent = updatedLevel.level_name;
            }
            renderGroupsTable();
            if (selectedGroupId) {
                renderSectionsTable();
            }
        }
    } catch (error) {
        showNotification('Failed to save level: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function deleteLevel(id) {
    const groupCount = allGroups.filter(g => g.level_id === id).length;
    const warningMsg = groupCount > 0 
        ? `Are you sure you want to delete this level? This will also delete ${groupCount} group(s) and all their sections.`
        : 'Are you sure you want to delete this level?';
    
    if (!window.confirm(warningMsg)) return;

    try {
        showLoading(true);
        await API.delete(Endpoints.level(id));
        showNotification('Level deleted successfully', 'success');
        await loadAllData();
    } catch (error) {
        showNotification('Failed to delete level: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Group CRUD
async function deleteGroup(id) {
    const sectionCount = allSections.filter(s => s.group_id === id).length;
    const warningMsg = sectionCount > 0
        ? `Are you sure you want to delete this group? This will also delete ${sectionCount} section(s).`
        : 'Are you sure you want to delete this group?';
    
    if (!window.confirm(warningMsg)) return;

    try {
        showLoading(true);
        await API.delete(Endpoints.group(id));
        showNotification('Group deleted successfully', 'success');
        await loadAllData();
        renderGroupsTable();
    } catch (error) {
        showNotification('Failed to delete group: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Section CRUD
async function deleteSection(id) {
    if (!window.confirm('Are you sure you want to delete this section?')) return;

    try {
        showLoading(true);
        await API.delete(Endpoints.section(id));
        showNotification('Section deleted successfully', 'success');
        await loadAllData();
        renderSectionsTable();
    } catch (error) {
        showNotification('Failed to delete section: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize
loadAllData();

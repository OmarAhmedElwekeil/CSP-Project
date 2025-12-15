// TAs page logic
Auth.requireAdmin();

let allTAs = [];
let allCourses = [];
let filteredTAs = [];
let editingTAId = null;

const taModal = new Modal('ta-modal-overlay');

// Load TAs
async function loadTAs() {
    try {
        showLoading(true);
        allTAs = await API.get(Endpoints.tas);
        filteredTAs = [...allTAs];
        renderTAsTable();
    } catch (error) {
        showNotification('Failed to load TAs: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Load courses
async function loadCourses() {
    try {
        allCourses = await API.get(Endpoints.courses);
        populateCoursesDropdown();
    } catch (error) {
        showNotification('Failed to load courses: ' + error.message, 'error');
    }
}

// Populate courses dropdown
function populateCoursesDropdown() {
    const select = document.getElementById('ta-courses');
    select.innerHTML = '';
    allCourses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.course_id;
        option.textContent = `${course.course_code} - ${course.course_name}`;
        select.appendChild(option);
    });
}

// Render TAs table
function renderTAsTable() {
    const columns = [
        { key: 'ta_name', label: 'Name' },
        { 
            key: 'courses', 
            label: 'Courses',
            format: (courses) => courses && courses.length > 0 
                ? courses.map(c => c.course_code).join(', ')
                : '<span class="text-muted">No courses assigned</span>'
        }
    ];

    const actions = [
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (ta) => editTA(ta)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (ta) => deleteTA(ta.ta_id)
        }
    ];

    const table = createTable(filteredTAs, columns, actions);
    document.getElementById('tas-table').innerHTML = '';
    document.getElementById('tas-table').appendChild(table);
}

// Filter TAs
function filterTAs() {
    const searchTerm = document.getElementById('ta-search')?.value || '';
    filteredTAs = filterData(allTAs, searchTerm, ['ta_name']);
    renderTAsTable();
}

// Open TA modal
function openTAModal() {
    editingTAId = null;
    taModal.setTitle('Add TA');
    clearForm('ta-form');
    
    // Clear course selections
    const select = document.getElementById('ta-courses');
    Array.from(select.options).forEach(opt => opt.selected = false);
    
    taModal.open();
}

// Edit TA
function editTA(ta) {
    editingTAId = ta.ta_id;
    taModal.setTitle('Edit TA');
    setFormData('ta-form', ta);
    
    // Select courses assigned to this TA
    const select = document.getElementById('ta-courses');
    const courseIds = (ta.courses || []).map(c => c.course_id);
    Array.from(select.options).forEach(opt => {
        opt.selected = courseIds.includes(parseInt(opt.value));
    });
    
    taModal.open();
}

// Save TA
async function saveTA() {
    if (!validateForm('ta-form')) {
        return;
    }

    const formData = getFormData('ta-form');
    
    // Get selected courses
    const select = document.getElementById('ta-courses');
    const selectedCourseIds = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));
    
    const data = {
        ta_name: formData.ta_name
    };

    try {
        showLoading(true);
        
        let taId;
        if (editingTAId) {
            await API.put(Endpoints.ta(editingTAId), data);
            taId = editingTAId;
            showNotification('TA updated successfully', 'success');
        } else {
            const result = await API.post(Endpoints.tas, data);
            taId = result.ta_id;
            showNotification('TA created successfully', 'success');
        }
        
        // Get current courses for this TA
        const ta = await API.get(Endpoints.ta(taId));
        const currentCourseIds = (ta.courses || []).map(c => c.course_id);
        
        // Remove courses that are no longer selected
        for (const courseId of currentCourseIds) {
            if (!selectedCourseIds.includes(courseId)) {
                try {
                    await API.delete(Endpoints.assignTACourse(taId, courseId));
                } catch (e) {
                    console.error('Failed to remove course:', e);
                }
            }
        }
        
        // Add newly selected courses
        for (const courseId of selectedCourseIds) {
            if (!currentCourseIds.includes(courseId)) {
                try {
                    await API.post(Endpoints.assignTACourse(taId, courseId), {});
                } catch (e) {
                    console.error('Failed to assign course:', e);
                }
            }
        }

        taModal.close();
        await loadTAs();
        renderTAsTable();
    } catch (error) {
        showNotification('Failed to save TA: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete TA
async function deleteTA(id) {
    if (!window.confirm('Are you sure you want to delete this TA?')) {
        return;
    }

    try {
        showLoading(true);
        await API.delete(Endpoints.ta(id));
        showNotification('TA deleted successfully', 'success');
        await loadTAs();
        renderTAsTable();
    } catch (error) {
        showNotification('Failed to delete TA: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTAs();
    loadCourses();
    
    const searchInput = document.getElementById('ta-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterTAs);
    }
});

// Instructors page logic
Auth.requireAdmin();

let allInstructors = [];
let allCourses = [];
let filteredInstructors = [];
let editingInstructorId = null;

const instructorModal = new Modal('instructor-modal-overlay');

// Load instructors
async function loadInstructors() {
    try {
        showLoading(true);
        allInstructors = await API.get(Endpoints.instructors);
        filteredInstructors = [...allInstructors];
        renderInstructorsTable();
    } catch (error) {
        showNotification('Failed to load instructors: ' + error.message, 'error');
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
    const select = document.getElementById('instructor-courses');
    select.innerHTML = '';
    allCourses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.course_id;
        option.textContent = `${course.course_code} - ${course.course_name}`;
        select.appendChild(option);
    });
}

// Render instructors table
function renderInstructorsTable() {
    const columns = [
        { key: 'instructor_name', label: 'Name' },
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
            handler: (instructor) => editInstructor(instructor)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (instructor) => deleteInstructor(instructor.instructor_id)
        }
    ];

    const table = createTable(filteredInstructors, columns, actions);
    document.getElementById('instructors-table').innerHTML = '';
    document.getElementById('instructors-table').appendChild(table);
}

// Filter instructors
function filterInstructors() {
    const searchTerm = document.getElementById('instructor-search')?.value || '';
    filteredInstructors = filterData(allInstructors, searchTerm, ['instructor_name']);
    renderInstructorsTable();
}

// Open instructor modal
function openInstructorModal() {
    editingInstructorId = null;
    instructorModal.setTitle('Add Instructor');
    clearForm('instructor-form');
    
    // Clear course selections
    const select = document.getElementById('instructor-courses');
    Array.from(select.options).forEach(opt => opt.selected = false);
    
    instructorModal.open();
}

// Edit instructor
function editInstructor(instructor) {
    editingInstructorId = instructor.instructor_id;
    instructorModal.setTitle('Edit Instructor');
    setFormData('instructor-form', instructor);
    
    // Select courses assigned to this instructor
    const select = document.getElementById('instructor-courses');
    const courseIds = (instructor.courses || []).map(c => c.course_id);
    Array.from(select.options).forEach(opt => {
        opt.selected = courseIds.includes(parseInt(opt.value));
    });
    
    instructorModal.open();
}

// Save instructor
async function saveInstructor() {
    if (!validateForm('instructor-form')) {
        return;
    }

    const formData = getFormData('instructor-form');
    
    // Get selected courses
    const select = document.getElementById('instructor-courses');
    const selectedCourseIds = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));
    
    const data = {
        instructor_name: formData.instructor_name
    };

    try {
        showLoading(true);
        
        let instructorId;
        if (editingInstructorId) {
            await API.put(Endpoints.instructor(editingInstructorId), data);
            instructorId = editingInstructorId;
            showNotification('Instructor updated successfully', 'success');
        } else {
            const result = await API.post(Endpoints.instructors, data);
            instructorId = result.instructor_id;
            showNotification('Instructor created successfully', 'success');
        }
        
        // Get current courses for this instructor
        const instructor = await API.get(Endpoints.instructor(instructorId));
        const currentCourseIds = (instructor.courses || []).map(c => c.course_id);
        
        // Remove courses that are no longer selected
        for (const courseId of currentCourseIds) {
            if (!selectedCourseIds.includes(courseId)) {
                try {
                    await API.delete(Endpoints.assignInstructorCourse(instructorId, courseId));
                } catch (e) {
                    console.error('Failed to remove course:', e);
                }
            }
        }
        
        // Add newly selected courses
        for (const courseId of selectedCourseIds) {
            if (!currentCourseIds.includes(courseId)) {
                try {
                    await API.post(Endpoints.assignInstructorCourse(instructorId, courseId), {});
                } catch (e) {
                    console.error('Failed to assign course:', e);
                }
            }
        }

        instructorModal.close();
        await loadInstructors();
        renderInstructorsTable();
    } catch (error) {
        showNotification('Failed to save instructor: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete instructor
async function deleteInstructor(id) {
    if (!window.confirm('Are you sure you want to delete this instructor?')) {
        return;
    }

    try {
        showLoading(true);
        await API.delete(Endpoints.instructor(id));
        showNotification('Instructor deleted successfully', 'success');
        await loadInstructors();
        renderInstructorsTable();
    } catch (error) {
        showNotification('Failed to delete instructor: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadInstructors();
    loadCourses();
    
    const searchInput = document.getElementById('instructor-search');
    if (searchInput) {
        searchInput.addEventListener('input', filterInstructors);
    }
});

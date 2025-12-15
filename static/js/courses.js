// Courses page logic
Auth.requireAdmin();

let allCourses = [];
let allLevels = [];
let allInstructors = [];
let allTAs = [];
let filteredCourses = [];
let editingCourseId = null;

const courseModal = new Modal('course-modal-overlay');

// Load courses
async function loadCourses() {
    try {
        showLoading(true);
        allCourses = await API.get(Endpoints.courses);
        filteredCourses = [...allCourses];
        renderCoursesTable();
    } catch (error) {
        showNotification('Failed to load courses: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Load related data
async function loadRelatedData() {
    try {
        allLevels = await API.get(Endpoints.levels);
        populateDropdowns();
    } catch (error) {
        showNotification('Failed to load related data: ' + error.message, 'error');
    }
}

function populateDropdowns() {
    // Levels
    const levelSelect = document.getElementById('course-level');
    levelSelect.innerHTML = '<option value="">Select level</option>';
    allLevels.forEach(level => {
        const option = document.createElement('option');
        option.value = level.level_id;
        option.textContent = level.level_name;
        levelSelect.appendChild(option);
    });
}

// Render courses table
function renderCoursesTable() {
    const columns = [
        { key: 'course_code', label: 'Code' },
        { key: 'course_name', label: 'Name' },
        { 
            key: 'level_id', 
            label: 'Level',
            format: (value) => {
                const level = allLevels.find(l => l.level_id === value);
                return level ? level.level_name : '-';
            }
        },
        { 
            key: 'lecture_slots', 
            label: 'Slots',
            format: (value, course) => {
                const parts = [];
                if (course.lecture_slots) parts.push(`Lec:${course.lecture_slots}`);
                if (course.lab_slots) parts.push(`Lab:${course.lab_slots}`);
                if (course.tutorial_slots) parts.push(`Tut:${course.tutorial_slots}`);
                return parts.join(' / ') || '-';
            }
        }
    ];

    const actions = [
        {
            label: 'Edit',
            className: 'btn-secondary',
            handler: (course) => editCourse(course)
        },
        {
            label: 'Delete',
            className: 'btn-danger',
            handler: (course) => deleteCourse(course.course_id)
        }
    ];

    const table = createTable(filteredCourses, columns, actions);
    document.getElementById('courses-table').innerHTML = '';
    document.getElementById('courses-table').appendChild(table);
}

// Filter courses
function filterCourses() {
    const searchTerm = document.getElementById('course-search').value;
    filteredCourses = filterData(allCourses, searchTerm, ['code', 'name', 'course_type']);
    renderCoursesTable();
}

// Open course modal
function openCourseModal() {
    editingCourseId = null;
    courseModal.setTitle('Add Course');
    clearForm('course-form');
    
    // Reset optional fields
    document.getElementById('lecture-slots').value = '1';
    document.getElementById('lab-slots').value = '0';
    document.getElementById('tutorial-slots').value = '0';
    
    courseModal.open();
}

// Edit course
function editCourse(course) {
    editingCourseId = course.course_id;
    courseModal.setTitle('Edit Course');
    
    // Set form data
    setFormData('course-form', course);
    
    courseModal.open();
}

// Save course
async function saveCourse() {
    if (!validateForm('course-form')) {
        return;
    }

    const data = getFormData('course-form');
    delete data.course_id;

    try {
        showLoading(true);
        
        if (editingCourseId) {
            await API.put(Endpoints.course(editingCourseId), data);
            showNotification('Course updated successfully', 'success');
        } else {
            await API.post(Endpoints.courses, data);
            showNotification('Course created successfully', 'success');
        }

        courseModal.close();
        await loadCourses();
    } catch (error) {
        showNotification('Failed to save course: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Delete course
async function deleteCourse(id) {
    if (!window.confirm('Are you sure you want to delete this course? This may affect existing schedules.')) {
        return;
    }

    try {
        showLoading(true);
        await API.delete(Endpoints.course(id));
        showNotification('Course deleted successfully', 'success');
        await loadCourses();
    } catch (error) {
        showNotification('Failed to delete course: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Initialize page
async function init() {
    await loadRelatedData();
    await loadCourses();
}

init();
